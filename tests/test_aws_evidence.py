"""Contract tests for the consultant-triggered AWS evidence adapter."""

from __future__ import annotations

import hashlib
import html
import hmac
import inspect
import json
import logging
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import boto3
import pytest
from alembic import command
from alembic.config import Config
from botocore.exceptions import EndpointConnectionError, NoCredentialsError
from botocore.stub import Stubber
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.config import settings
from app.database import get_db
from app.main import app
from app.models.assessment import _new_id
from app.models.audit_event import AuditEvent
from app.models.client import Client
from app.models.engagement import Engagement
from app.models.evidence import Evidence, EvidenceUse, EvidenceVersion
from app.routers import aws as aws_router
from app.services import aws_evidence, evidence as evidence_service
from app.template_config import configure_templates
from app.routers.web import templates

REPO_ROOT = Path(__file__).resolve().parents[1]
ACCOUNT_ID = "111122223333"
ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/ComplianceEvidenceReadOnly"
BASE_ACCESS_KEY = "AKIATESTTESTTESTTEST"
BASE_SECRET = "test-base-secret"
SESSION_SECRET = "test-session-secret-DO-NOT-LEAK"
SESSION_TOKEN = "test-session-token-DO-NOT-LEAK"
PULL_ID = "0" * 32
FIXED_NOW = datetime(2026, 9, 24, 10, 0, tzinfo=timezone.utc)


@pytest.fixture(scope="module", autouse=True)
def _register_frameworks():
    from app.main import _register_frameworks as register

    register()


def _alembic_config(db_path: Path) -> Config:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


@pytest.fixture()
def db_path(tmp_path):
    path = tmp_path / "aws-evidence.sqlite3"
    command.upgrade(_alembic_config(path), "head")
    return path


@pytest.fixture()
def engine(db_path):
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _record):  # pragma: no cover
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    yield engine
    engine.dispose()


@pytest.fixture()
def db(engine):
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def http(db, db_path, monkeypatch):
    configure_templates(templates)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path}")

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def upload_root(tmp_path, monkeypatch) -> Path:
    root = tmp_path / "uploads"
    root.mkdir()
    monkeypatch.setattr(settings, "upload_dir", str(root))
    monkeypatch.setattr(settings, "aws_external_id_secret", "test-external-id-secret-1234567890")
    monkeypatch.setattr(settings, "session_secret", SESSION_SECRET)
    monkeypatch.setattr(settings, "firm_name", "Acme Advisory")
    for name in (
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AWS_PROFILE",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("AWS_CONFIG_FILE", str(tmp_path / "missing-config"))
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(tmp_path / "missing-credentials"))
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    return root


def _seed_engagement(db, name="Acme AWS"):
    client = Client(
        id=_new_id(), name=f"{name} Client", industry="Technology", size="medium"
    )
    engagement = Engagement(
        id=_new_id(),
        client_id=client.id,
        name=name,
        type="gap_assessment",
        status="active",
    )
    db.add_all([client, engagement])
    db.commit()
    return client, engagement


def _snapshot(db, upload_root):
    return {
        "counts": {
            "evidence": db.query(Evidence).count(),
            "versions": db.query(EvidenceVersion).count(),
            "uses": db.query(EvidenceUse).count(),
            "audit": db.query(AuditEvent).count(),
        },
        "evidence": sorted((row.id, row.status) for row in db.query(Evidence).all()),
        "versions": sorted(
            (row.id, row.status, row.file_hash_sha256)
            for row in db.query(EvidenceVersion).all()
        ),
        "paths": sorted(
            str(path.relative_to(upload_root))
            for path in upload_root.rglob("*")
            if path.is_file()
        ),
    }


def _rule(name, state="ACTIVE"):
    return {
        "ConfigRuleName": name,
        "ConfigRuleArn": f"arn:aws:config:eu-west-1:{ACCOUNT_ID}:config-rule/{name}",
        "ConfigRuleId": f"config-rule-{name}",
        "Description": f"Description for {name}",
        "ConfigRuleState": state,
        "Source": {"Owner": "AWS", "SourceIdentifier": name.upper()},
    }


def _evaluation(rule_name, resource_id, compliance, *, resource_type="AWS::S3::Bucket", mode=None):
    qualifier = {
        "ConfigRuleName": rule_name,
        "ResourceType": resource_type,
        "ResourceId": resource_id,
    }
    if mode is not None:
        qualifier["EvaluationMode"] = mode
    return {
        "EvaluationResultIdentifier": {"EvaluationResultQualifier": qualifier},
        "ComplianceType": compliance,
        "ResultRecordedTime": FIXED_NOW,
        "ConfigRuleInvokedTime": FIXED_NOW - timedelta(minutes=1),
        "Annotation": f"Annotation for {resource_id}",
        "ResultToken": "must-not-be-stored",
    }


def _finding(finding_id, generator, *, severity="HIGH", compliance="FAILED", include_fields=True):
    value = {
        "SchemaVersion": "2018-10-08",
        "Id": finding_id,
        "ProductArn": f"arn:aws:securityhub:eu-west-1:{ACCOUNT_ID}:product/test/product",
        "GeneratorId": generator,
        "AwsAccountId": ACCOUNT_ID,
        "CreatedAt": "2026-09-24T09:00:00Z",
        "UpdatedAt": "2026-09-24T09:30:00Z",
        "Title": f"Finding {finding_id}",
        "Description": "sensitive description must not be stored",
        "Resources": [{"Type": "AwsS3Bucket", "Id": f"bucket-{finding_id}"}],
        "ProductName": "Security product",
        "Workflow": {"Status": "NEW"},
        "FirstObservedAt": "2026-09-24T08:00:00Z",
        "LastObservedAt": "2026-09-24T09:30:00Z",
    }
    if include_fields:
        value["Severity"] = {"Label": severity}
        value["Compliance"] = {"Status": compliance}
    return value


class FakeAws:
    def __init__(self, monkeypatch, pull_id=PULL_ID):
        self.pull_id = pull_id
        self.engagement_id = None
        self.calls = []
        self.sts_regions = []
        self.clients = {}
        self.client_stubbers = {}
        self.stubbers = []
        self.credentials = {
            "AccessKeyId": "ASIATESTTESTTESTTEST",
            "SecretAccessKey": SESSION_SECRET,
            "SessionToken": SESSION_TOKEN,
            "Expiration": FIXED_NOW + timedelta(minutes=15),
        }
        self.sts_client = boto3.session.Session(
            aws_access_key_id=BASE_ACCESS_KEY,
            aws_secret_access_key=BASE_SECRET,
            region_name="eu-west-1",
        ).client("sts", region_name="eu-west-1")
        self.sts_stubber = Stubber(self.sts_client)
        self.stubbers.append(self.sts_stubber)
        self.sts_stubber.activate()
        monkeypatch.setattr(aws_evidence, "_sts_client", self._sts_client)
        monkeypatch.setattr(aws_evidence, "_service_client", self._service_client)

    def _sts_client(self, region):
        self.sts_regions.append(region)
        return self.sts_client

    def _service_client(self, credentials, service, region):
        assert credentials.access_key_id == self.credentials["AccessKeyId"]
        assert credentials.secret_access_key == self.credentials["SecretAccessKey"]
        assert credentials.session_token == self.credentials["SessionToken"]
        self.calls.append((service, region))
        key = (service, region)
        if key not in self.clients:
            client = boto3.session.Session(
                aws_access_key_id=self.credentials["AccessKeyId"],
                aws_secret_access_key=self.credentials["SecretAccessKey"],
                aws_session_token=self.credentials["SessionToken"],
                region_name=region,
            ).client(service, region_name=region)
            self.clients[key] = client
            stubber = Stubber(client)
            stubber.activate()
            self.stubbers.append(stubber)
        return self.clients[key]

    def expect_probe_denied(self):
        self.sts_stubber.add_client_error(
            "assume_role",
            service_error_code="AccessDenied",
            http_status_code=403,
            expected_params={
                "RoleArn": ROLE_ARN,
                "RoleSessionName": f"evidence-probe-{self.pull_id}",
                "DurationSeconds": 900,
                "Policy": aws_evidence.session_policy_json(ACCOUNT_ID),
            },
        )

    def expect_assume(self, account_id=ACCOUNT_ID, *, assumed_account=None):
        assumed_account = assumed_account or account_id
        self.sts_stubber.add_response(
            "assume_role",
            {
                "Credentials": self.credentials,
                "AssumedRoleUser": {
                    "AssumedRoleId": f"AROATEST:evidence-pull-{self.pull_id}",
                    "Arn": f"arn:aws:sts::{assumed_account}:assumed-role/ComplianceEvidenceReadOnly/evidence-pull-{self.pull_id}",
                },
            },
            expected_params={
                "RoleArn": ROLE_ARN,
                "RoleSessionName": f"evidence-pull-{self.pull_id}",
                "DurationSeconds": 900,
                "ExternalId": aws_evidence.external_id(self.engagement_id),
                "Policy": aws_evidence.session_policy_json(account_id),
            },
        )

    def expect_rules(self, region, pages):
        stubber = self._stubber("config", region)
        for index, page in enumerate(pages):
            params = {} if index == 0 else {"NextToken": pages[index - 1]["NextToken"]}
            response = {"ConfigRules": page["ConfigRules"]}
            if page.get("NextToken"):
                response["NextToken"] = page["NextToken"]
            stubber.add_response("describe_config_rules", response, expected_params=params)

    def expect_details(self, region, rule_name, pages, *, error=None):
        stubber = self._stubber("config", region)
        for index, page in enumerate(pages):
            params = {
                "ConfigRuleName": rule_name,
                "ComplianceTypes": ["COMPLIANT", "NON_COMPLIANT"],
                "Limit": 100,
            }
            if index:
                params["NextToken"] = pages[index - 1]["NextToken"]
            if error:
                stubber.add_client_error(
                    "get_compliance_details_by_config_rule",
                    service_error_code=error,
                    expected_params=params,
                )
                return
            response = {"EvaluationResults": page["EvaluationResults"]}
            if page.get("NextToken"):
                response["NextToken"] = page["NextToken"]
            stubber.add_response(
                "get_compliance_details_by_config_rule", response, expected_params=params
            )

    def expect_findings(self, region, pages, *, error=None):
        stubber = self._stubber("securityhub", region)
        filters = {
            "AwsAccountId": [{"Value": ACCOUNT_ID, "Comparison": "EQUALS"}],
            "Region": [{"Value": region, "Comparison": "EQUALS"}],
            "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
        }
        for index, page in enumerate(pages):
            params = {"Filters": filters, "MaxResults": 100}
            if index:
                params["NextToken"] = pages[index - 1]["NextToken"]
            if error:
                stubber.add_client_error("get_findings", service_error_code=error, expected_params=params)
                return
            response = {"Findings": page["Findings"]}
            if page.get("NextToken"):
                response["NextToken"] = page["NextToken"]
            stubber.add_response("get_findings", response, expected_params=params)

    def expect_securityhub_not_enabled(self, region):
        self._stubber("securityhub", region).add_client_error(
            "get_findings",
            service_error_code="InvalidAccessException",
            expected_params={
                "Filters": {
                    "AwsAccountId": [{"Value": ACCOUNT_ID, "Comparison": "EQUALS"}],
                    "Region": [{"Value": region, "Comparison": "EQUALS"}],
                    "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
                },
                "MaxResults": 100,
            },
        )

    def _stubber(self, service, region):
        key = (service, region)
        if key not in self.clients:
            client = boto3.session.Session(
                aws_access_key_id=self.credentials["AccessKeyId"],
                aws_secret_access_key=self.credentials["SecretAccessKey"],
                aws_session_token=self.credentials["SessionToken"],
                region_name=region,
            ).client(service, region_name=region)
            self.clients[key] = client
            stubber = Stubber(client)
            stubber.activate()
            self.client_stubbers[key] = stubber
            self.stubbers.append(stubber)
        return self.client_stubbers[key]

    def assert_no_pending(self):
        for stubber in self.stubbers:
            stubber.assert_no_pending_responses()


def _patch_clock(monkeypatch, pull_ids=(PULL_ID,)):
    ids = iter(pull_ids)
    monkeypatch.setattr(aws_evidence, "_new_pull_id", lambda: next(ids))
    monkeypatch.setattr(aws_evidence, "_now", lambda: FIXED_NOW)


def _stage_one_region(fake, engagement_id, *, changed=False, new_rule=False):
    fake.engagement_id = engagement_id
    fake.expect_probe_denied()
    fake.expect_assume()
    rules = [_rule("s3-bucket-public-read-prohibited"), _rule("iam-root-access-key-check")]
    if new_rule:
        rules.append(_rule("new-rule"))
    fake.expect_rules(
        "eu-west-1",
        [{"ConfigRules": [rules[0], _rule("old-rule", "DELETING")], "NextToken": "rules-2"}, {"ConfigRules": rules[1:]}],
    )
    iam_eval = _evaluation(
        "iam-root-access-key-check", "resource-1", "NON_COMPLIANT" if changed else "COMPLIANT"
    )
    fake.expect_details("eu-west-1", "iam-root-access-key-check", [{"EvaluationResults": [iam_eval]}])
    fake.expect_details(
        "eu-west-1",
        "s3-bucket-public-read-prohibited",
        [{"EvaluationResults": [_evaluation("s3-bucket-public-read-prohibited", "resource-2", "NON_COMPLIANT")]}],
    )
    if new_rule:
        fake.expect_details("eu-west-1", "new-rule", [{"EvaluationResults": []}])
    fake.expect_findings(
        "eu-west-1",
        [{"Findings": [_finding("finding-1", "gen-a"), _finding("finding-2", "gen-a", include_fields=False), _finding("finding-3", "gen-b", severity="CRITICAL", compliance="PASSED")] }],
    )


def _run_pull(db, engagement, *, account=ACCOUNT_ID, role=ROLE_ARN, regions="eu-west-1"):
    return aws_evidence.pull_aws_evidence(
        db,
        engagement_id=engagement.id,
        account_id=account,
        role_arn=role,
        regions_raw=regions,
    )


def test_scenario_1_evidence_and_version_created_with_provenance(db, upload_root, monkeypatch):
    """Scenario 1: Evidence and EvidenceVersion are created with provenance."""
    _, engagement = _seed_engagement(db)
    _patch_clock(monkeypatch)
    fake = FakeAws(monkeypatch)
    fake.engagement_id = engagement.id
    _stage_one_region(fake, engagement.id)
    result = _run_pull(db, engagement)
    fake.assert_no_pending()

    assert result.account_id == ACCOUNT_ID
    assert result.regions == ("eu-west-1",)
    assert result.sources == (
        aws_evidence.SourceSummary("aws_config", "eu-west-1", "collected", 2, 2, 0, 0, 0, False, 0),
        aws_evidence.SourceSummary("aws_securityhub", "eu-west-1", "collected", 2, 2, 0, 0, 0, False, 0),
    )
    rows = db.query(Evidence).order_by(Evidence.original_filename).all()
    assert len(rows) == 4
    assert all(row.engagement_id == engagement.id and row.assessment_id is None for row in rows)
    assert {row.uploaded_by for row in rows} == {
        f"aws_config:{ACCOUNT_ID}",
        f"aws_securityhub:{ACCOUNT_ID}",
    }
    for row in rows:
        version = db.query(EvidenceVersion).filter_by(evidence_id=row.id).one()
        assert row.status == version.status == "active"
        assert row.mime_type == version.mime_type == "text/plain"
        assert version.version_number == 1
        assert version.storage_path.endswith("/v1.txt")
        content = Path(settings.upload_dir, version.storage_path).read_bytes()
        assert content == version.extracted_text.encode()
        assert hashlib.sha256(content).hexdigest() == version.file_hash_sha256
        assert evidence_service.verify_version(db, version.id)
    config_doc = json.loads(
        Path(settings.upload_dir, db.query(EvidenceVersion).join(Evidence).filter(Evidence.uploaded_by.like("aws_config:%")).first().storage_path).read_text()
    )
    assert config_doc["schema"] == "aws_config_rule_evaluations/v1"
    assert config_doc["summary"]["total"] == 1
    assert "ResultToken" not in json.dumps(config_doc)
    completed = db.query(AuditEvent).filter_by(action="aws_evidence.pull_completed").one()
    metadata = json.loads(completed.metadata_json)
    assert set(metadata) == {
        "pull_id", "account_id", "role_arn", "regions", "role_session_name",
        "external_id_version", "started_at", "finished_at", "sources", "evidence_ids",
    }
    assert metadata["external_id_version"] == "v1"
    assert metadata["evidence_ids"] == list(result.evidence_ids)
    assert fake.sts_regions == ["eu-west-1"]
    assert fake.calls == [("config", "eu-west-1"), ("securityhub", "eu-west-1")]


def test_scenario_2_repull_versions_only_when_changed(db, upload_root, monkeypatch):
    """Scenario 2: A re-pull is unchanged, versioned on data change, and recreates archived identity."""
    _, engagement = _seed_engagement(db)
    pull_ids = iter([PULL_ID, "1" * 32, "2" * 32, "3" * 32])
    monkeypatch.setattr(aws_evidence, "_new_pull_id", lambda: next(pull_ids))
    monkeypatch.setattr(aws_evidence, "_now", lambda: FIXED_NOW)
    fake = FakeAws(monkeypatch)
    _stage_one_region(fake, engagement.id)
    first = _run_pull(db, engagement)
    first_snapshot = _snapshot(db, upload_root)
    fake2 = FakeAws(monkeypatch, "1" * 32)
    _stage_one_region(fake2, engagement.id)
    unchanged = _run_pull(db, engagement)
    assert unchanged.sources[0].unchanged == 2
    assert unchanged.sources[1].unchanged == 2
    assert _snapshot(db, upload_root)["counts"] == first_snapshot["counts"] | {"audit": first_snapshot["counts"]["audit"] + 1}
    fake3 = FakeAws(monkeypatch, "2" * 32)
    _stage_one_region(fake3, engagement.id, changed=True)
    changed = _run_pull(db, engagement)
    assert changed.sources[0].versioned == 1
    iam_filename = aws_evidence.evidence_filename("aws_config", account_id=ACCOUNT_ID, region="eu-west-1", key="iam-root-access-key-check")
    iam = db.query(Evidence).filter_by(original_filename=iam_filename).one()
    versions = db.query(EvidenceVersion).filter_by(evidence_id=iam.id).order_by(EvidenceVersion.version_number).all()
    assert len(versions) == 2
    assert versions[0].status == "superseded"
    assert versions[1].status == "active"
    assert versions[1].change_reason.startswith("AWS pull ")
    evidence_service.transition_evidence(db, evidence_id=iam.id, to_status="archived", actor="consultant")
    db.commit()
    fake4 = FakeAws(monkeypatch, "3" * 32)
    _stage_one_region(fake4, engagement.id)
    _run_pull(db, engagement)
    archived = db.query(Evidence).filter_by(id=iam.id).one()
    assert archived.status == "archived"
    assert db.query(Evidence).filter_by(original_filename=iam_filename).count() == 2
    assert first.evidence_ids


def test_scenario_3_exact_policies_and_documentation():
    """Scenario 3: Policies, session JSON, and documentation are exact."""
    expected = {
        "Version": "2012-10-17",
        "Statement": [
            {"Sid": "ListConfigRules", "Effect": "Allow", "Action": "config:DescribeConfigRules", "Resource": "*"},
            {"Sid": "ReadConfigRuleEvaluations", "Effect": "Allow", "Action": "config:GetComplianceDetailsByConfigRule", "Resource": "arn:aws:config:*:111122223333:config-rule/*"},
            {"Sid": "ReadSecurityHubFindings", "Effect": "Allow", "Action": "securityhub:GetFindings", "Resource": "arn:aws:securityhub:*:111122223333:hub/default"},
        ],
    }
    assert aws_evidence.permissions_policy(ACCOUNT_ID) == expected
    assert aws_evidence.trust_policy("x" * 64, "arn:aws:iam::444455556666:role/Consultant")["Statement"][0]["Condition"] == {"StringEquals": {"sts:ExternalId": "x" * 64}}
    assert aws_evidence.consultant_policy()["Statement"][0]["Resource"] == "arn:aws:iam::*:role/ComplianceEvidenceReadOnly"
    assert aws_evidence.session_policy_json(ACCOUNT_ID) == json.dumps(expected, separators=(",", ":"), sort_keys=True)
    blocks = re.findall(r"```json\n(.*?)\n```", (REPO_ROOT / "docs/operations/aws-evidence.md").read_text(), re.S)
    assert [json.loads(block) for block in blocks] == [
        aws_evidence.trust_policy("<EXTERNAL_ID_FROM_THE_ENGAGEMENT_PAGE>", aws_evidence.CONSULTANT_PRINCIPAL_PLACEHOLDER),
        expected,
        aws_evidence.consultant_policy(),
    ]
    doc = (REPO_ROOT / "docs/operations/aws-evidence.md").read_text()
    for constant in ("NOT_CONFIGURED", "INVALID_ACCOUNT_ID", "INVALID_ROLE_ARN", "ROLE_ACCOUNT_MISMATCH", "REGIONS_REQUIRED", "TOO_MANY_REGIONS", "UNKNOWN_REGION", "BASE_CREDENTIALS_UNAVAILABLE", "ASSUME_ROLE_DENIED", "TRUST_POLICY_MISSING_EXTERNAL_ID", "ASSUMED_ACCOUNT_MISMATCH", "STS_REGION_DISABLED", "REGION_NOT_ENABLED", "PERMISSION_MISSING", "SESSION_EXPIRED", "DEADLINE_EXCEEDED", "AWS_UNREACHABLE", "AWS_ERROR", "WRITE_FAILED", "ORIGIN_REJECTED"):
        assert constant in doc


def test_scenario_4_external_id_configuration_and_ignored_credentials(db, http, monkeypatch):
    """Scenario 4: External IDs are derived, configuration is gated, and posted credentials are ignored."""
    _, engagement = _seed_engagement(db)
    key = settings.aws_external_id_secret
    expected = hmac.new(key.encode(), f"evidence-external-id:v1:{engagement.id}".encode(), hashlib.sha256).hexdigest()
    assert aws_evidence.external_id(engagement.id) == expected
    assert len(expected) == 64 and expected.islower()
    monkeypatch.setattr(settings, "aws_external_id_secret", "")
    assert not aws_evidence.is_configured()
    response = http.get(f"/engagements/{engagement.id}/aws-evidence")
    assert response.status_code == 200
    assert "data-aws-not-configured" in response.text
    assert "data-aws-pull-form" not in response.text
    assert "data-external-id" not in response.text
    assert "data-trust-policy" not in response.text
    monkeypatch.setattr(settings, "aws_external_id_secret", key)
    assert "aws_external_id_secret" in type(settings).model_fields
    assert not [name for name in type(settings).model_fields if "aws" in name.lower() and name != "aws_external_id_secret"]

    _patch_clock(monkeypatch)
    fake = FakeAws(monkeypatch)
    _stage_one_region(fake, engagement.id)
    pulled = http.post(
        f"/engagements/{engagement.id}/aws-evidence/pull",
        data={
            "account_id": ACCOUNT_ID,
            "role_arn": ROLE_ARN,
            "regions": "eu-west-1",
            "external_id": "attacker-chosen",
            "aws_access_key_id": "attacker-key",
            "aws_secret_access_key": "attacker-secret",
        },
    )
    assert pulled.status_code == 200
    assert "data-aws-result" in pulled.text
    fake.assert_no_pending()


@pytest.mark.parametrize(
    "account, role, regions, message",
    [
        ("12345", ROLE_ARN, "eu-west-1", aws_evidence.INVALID_ACCOUNT_ID),
        (ACCOUNT_ID, "arn:aws-us-gov:iam::111122223333:role/X", "eu-west-1", aws_evidence.INVALID_ROLE_ARN),
        (ACCOUNT_ID, "arn:aws:iam::111122223333:user/X", "eu-west-1", aws_evidence.INVALID_ROLE_ARN),
        (ACCOUNT_ID, "arn:aws:iam::111122223333:root", "eu-west-1", aws_evidence.INVALID_ROLE_ARN),
        (ACCOUNT_ID, "not an arn", "eu-west-1", aws_evidence.INVALID_ROLE_ARN),
        (ACCOUNT_ID, ROLE_ARN.replace(ACCOUNT_ID, "444455556666"), "eu-west-1", aws_evidence.ROLE_ACCOUNT_MISMATCH),
        (ACCOUNT_ID, ROLE_ARN, "", aws_evidence.REGIONS_REQUIRED),
        (ACCOUNT_ID, ROLE_ARN, " , ", aws_evidence.REGIONS_REQUIRED),
        (ACCOUNT_ID, ROLE_ARN, "eu-west-1 us-east-1 us-west-1 eu-central-1 ap-south-1", aws_evidence.TOO_MANY_REGIONS),
        (ACCOUNT_ID, ROLE_ARN, "eu-west-1, mars-north-1", aws_evidence.UNKNOWN_REGION.format(region="mars-north-1")),
        (ACCOUNT_ID, ROLE_ARN, "us-gov-west-1", aws_evidence.UNKNOWN_REGION.format(region="us-gov-west-1")),
    ],
)
def test_scenario_5_validation_is_ordered_and_does_not_write(db, upload_root, monkeypatch, account, role, regions, message):
    """Scenario 5: Invalid inputs fail in the prescribed order before AWS or writes."""
    _, engagement = _seed_engagement(db)
    called = []
    monkeypatch.setattr(aws_evidence, "_sts_client", lambda region: called.append(region))
    before = _snapshot(db, upload_root)
    with pytest.raises(aws_evidence.AwsValidationError, match=re.escape(message)):
        _run_pull(db, engagement, account=account, role=role, regions=regions)
    assert called == []
    assert _snapshot(db, upload_root) == before
    assert aws_evidence._normalise_inputs(ACCOUNT_ID, ROLE_ARN, " EU-WEST-1 ,eu-west-1  us-east-1")[2] == ("eu-west-1", "us-east-1")
    with pytest.raises(aws_evidence.AwsEngagementNotFound):
        aws_evidence.pull_aws_evidence(db, engagement_id="missing", account_id=ACCOUNT_ID, role_arn=ROLE_ARN, regions_raw="eu-west-1")
    assert len(aws_evidence.SUPPORTED_REGIONS) == 34
    assert "eu-west-1" in aws_evidence.SUPPORTED_REGIONS and "us-east-1" in aws_evidence.SUPPORTED_REGIONS
    assert "us-gov-west-1" not in aws_evidence.SUPPORTED_REGIONS and "cn-north-1" not in aws_evidence.SUPPORTED_REGIONS


def test_scenario_6_sts_failures_are_sanitised_and_audited(db, upload_root, monkeypatch):
    """Scenario 6: STS failures are mapped, sanitized, and leave no collected data."""
    _, engagement = _seed_engagement(db)
    _patch_clock(monkeypatch)
    fake = FakeAws(monkeypatch)
    fake.engagement_id = engagement.id
    fake.sts_stubber.add_response(
        "assume_role",
        {"Credentials": fake.credentials, "AssumedRoleUser": {"AssumedRoleId": "AROATEST:x", "Arn": f"arn:aws:sts::{ACCOUNT_ID}:assumed-role/x/x"}},
        expected_params={"RoleArn": ROLE_ARN, "RoleSessionName": f"evidence-probe-{PULL_ID}", "DurationSeconds": 900, "Policy": aws_evidence.session_policy_json(ACCOUNT_ID)},
    )
    before = _snapshot(db, upload_root)
    with pytest.raises(aws_evidence.AwsPullFailed) as exc_info:
        _run_pull(db, engagement)
    assert exc_info.value.message == aws_evidence.TRUST_POLICY_MISSING_EXTERNAL_ID
    assert exc_info.value.step == "trust_policy_check"
    assert _snapshot(db, upload_root)["counts"]["evidence"] == before["counts"]["evidence"]
    fake.assert_no_pending()
    failed = db.query(AuditEvent).filter_by(action="aws_evidence.pull_failed").one()
    assert set(json.loads(failed.metadata_json)) == {"pull_id", "account_id", "role_arn", "regions", "step", "error_code", "message", "started_at", "failed_at"}


def test_scenario_7_service_failures_and_non_errors(db, upload_root, monkeypatch):
    """Scenario 7: Service errors fail atomically while disabled Security Hub and deleted rules do not."""
    _, engagement = _seed_engagement(db)
    _patch_clock(monkeypatch, (PULL_ID, "1" * 32))
    fake = FakeAws(monkeypatch)
    fake.engagement_id = engagement.id
    fake.expect_probe_denied()
    fake.expect_assume()
    fake.expect_rules("eu-west-1", [{"ConfigRules": [_rule("a-rule")]}])
    fake.expect_details("eu-west-1", "a-rule", [{"EvaluationResults": []}], error="AccessDeniedException")
    fake.expect_rules("us-east-1", [{"ConfigRules": []}])
    before = _snapshot(db, upload_root)
    with pytest.raises(aws_evidence.AwsPullFailed, match=re.escape(aws_evidence.PERMISSION_MISSING.format(action="config:GetComplianceDetailsByConfigRule", region="eu-west-1"))):
        _run_pull(db, engagement, regions="eu-west-1 us-east-1")
    assert _snapshot(db, upload_root)["counts"]["evidence"] == before["counts"]["evidence"]
    assert db.query(AuditEvent).filter_by(action="aws_evidence.pull_failed").count() == 1

    _, not_enabled_engagement = _seed_engagement(db, "Not Enabled")
    fake2 = FakeAws(monkeypatch, "1" * 32)
    fake2.engagement_id = not_enabled_engagement.id
    fake2.expect_probe_denied()
    fake2.expect_assume()
    fake2.expect_rules("eu-west-1", [{"ConfigRules": [_rule("a-rule")]}])
    fake2.expect_details("eu-west-1", "a-rule", [{"EvaluationResults": []}])
    fake2.expect_findings("eu-west-1", [{}], error="InvalidAccessException")
    result = _run_pull(db, not_enabled_engagement)
    assert result.sources[1].status == "not_enabled"
    assert result.sources[1].items == 0
    fake2.assert_no_pending()


def test_scenario_8_write_failures_rollback_rows_and_blobs(db, upload_root, monkeypatch):
    """Scenario 8: Write failures roll back new and replacement evidence and remove blobs."""
    _, engagement = _seed_engagement(db)
    _patch_clock(monkeypatch)
    fake = FakeAws(monkeypatch)
    fake.engagement_id = engagement.id
    _stage_one_region(fake, engagement.id)
    calls = 0
    original = aws_evidence.evidence_service.release_from_quarantine

    def fail_third(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise RuntimeError("forced write failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(aws_evidence.evidence_service, "release_from_quarantine", fail_third)
    with pytest.raises(aws_evidence.AwsPullFailed, match=re.escape(aws_evidence.WRITE_FAILED)):
        _run_pull(db, engagement)
    assert db.query(Evidence).count() == 0
    assert not [path for path in (upload_root / "evidence").rglob("*") if path.is_file()] if (upload_root / "evidence").exists() else True
    assert db.query(AuditEvent).filter_by(action="aws_evidence.pull_failed").count() == 1


def test_scenario_9_caps_and_truncation(db, upload_root, monkeypatch):
    """Scenario 9: Config and Security Hub caps truncate at the required boundaries."""
    _, engagement = _seed_engagement(db)
    _patch_clock(monkeypatch)
    fake = FakeAws(monkeypatch)
    fake.engagement_id = engagement.id
    fake.expect_probe_denied()
    fake.expect_assume()
    fake.expect_rules("eu-west-1", [{"ConfigRules": [_rule("cap-rule")]}])
    detail_pages = []
    for index in range(5):
        detail_pages.append({"EvaluationResults": [_evaluation("cap-rule", f"r-{index}-{n}", "COMPLIANT") for n in range(100)], "NextToken": f"d-{index + 1}" if index < 4 else "still-more"})
    fake.expect_details("eu-west-1", "cap-rule", detail_pages)
    fake.expect_findings("eu-west-1", [{"Findings": []}])
    result = _run_pull(db, engagement)
    assert result.sources[0].items == 1
    version = db.query(EvidenceVersion).one()
    document = json.loads(Path(settings.upload_dir, version.storage_path).read_text())
    assert len(document["evaluations"]) == 500 and document["truncated"]


def test_scenario_10_credential_hygiene_and_operation_guard(db, upload_root, monkeypatch, caplog, db_path):
    """Scenario 10: Credentials and external IDs never persist, log, or escape the guarded calls."""
    _, engagement = _seed_engagement(db)
    _patch_clock(monkeypatch)
    fake = FakeAws(monkeypatch)
    _stage_one_region(fake, engagement.id)
    with caplog.at_level(logging.DEBUG):
        _run_pull(db, engagement)
    dump = "\n".join(sqlite3.connect(db_path).iterdump())
    files = b"".join(path.read_bytes() for path in upload_root.rglob("*") if path.is_file())
    audit = "\n".join(row.metadata_json or "" for row in db.query(AuditEvent).all())
    for value in (SESSION_SECRET, SESSION_TOKEN, fake.credentials["AccessKeyId"], BASE_SECRET, aws_evidence.external_id(engagement.id)):
        assert value not in dump
        assert value.encode() not in files
        assert value not in caplog.text
        assert value not in audit
    representation = repr(aws_evidence.TemporaryCredentials("AKVALUE1", "SKVALUE2", "STVALUE3", FIXED_NOW))
    assert "expiration" in representation and all(value not in representation for value in ("AKVALUE1", "SKVALUE2", "STVALUE3"))
    untouched = []
    class Untouched:
        def __getattr__(self, name):
            untouched.append(name)
            raise AssertionError(name)
    with pytest.raises(AssertionError):
        aws_evidence._call(Untouched(), "config", "PutConfigRule")
    assert untouched == []
    source = inspect.getsource(aws_evidence)
    assert "boto3.client(" not in source and "boto3.resource(" not in source
    assert set(aws_evidence.AWS_OPERATIONS) == {("sts", "AssumeRole"), ("config", "DescribeConfigRules"), ("config", "GetComplianceDetailsByConfigRule"), ("securityhub", "GetFindings")}


def test_scenario_11_routes_page_origin_and_escaping(db, http, monkeypatch):
    """Scenario 11: Routes, headers, origin protection, prefill, and HTML escaping match the contract."""
    _, engagement = _seed_engagement(db)
    page = http.get(f"/engagements/{engagement.id}/aws-evidence")
    assert page.status_code == 200
    assert page.headers["cache-control"] == "no-store"
    assert page.headers["referrer-policy"] == "no-referrer"
    assert "data-aws-pull-form" in page.text
    assert "data-external-id" in page.text
    assert "data-trust-policy" in page.text
    malicious = http.post(
        f"/engagements/{engagement.id}/aws-evidence/pull",
        data={"account_id": ACCOUNT_ID, "role_arn": ROLE_ARN, "regions": "eu-west-1"},
        headers={"Origin": "https://evil.example"},
    )
    assert malicious.status_code == 403 and aws_evidence.ORIGIN_REJECTED in malicious.text
    invalid = http.post(
        f"/engagements/{engagement.id}/aws-evidence/pull",
        data={"account_id": ACCOUNT_ID, "role_arn": "arn:aws:iam::111122223333:role/<script>", "regions": "eu-west-1"},
    )
    assert invalid.status_code == 200
    assert "data-aws-error" in invalid.text
    assert "&lt;script&gt;" in invalid.text and "<script>" not in invalid.text
    assert http.get("/engagements/missing/aws-evidence").status_code == 404
    routes = {(method, route.path) for route in app.routes for method in getattr(route, "methods", set()) if "/aws-evidence" in route.path}
    assert routes == {("GET", "/engagements/{engagement_id}/aws-evidence"), ("POST", "/engagements/{engagement_id}/aws-evidence/pull")}
    assert not inspect.iscoroutinefunction(aws_router.aws_evidence_page)
    assert not inspect.iscoroutinefunction(aws_router.aws_evidence_pull)
    assert f'href="/engagements/{engagement.id}/aws-evidence"' in http.get(f"/engagements/{engagement.id}").text


def test_scenario_12_structural_guards_and_protected_files():
    """Scenario 12: New templates stay autoescaped and protected contracts remain unchanged."""
    for path in (REPO_ROOT / "app/templates/pages/aws_evidence.html", REPO_ROOT / "app/templates/partials/aws_evidence_panel.html"):
        content = path.read_text()
        assert not re.search(r"\|\s*safe\b|overall_score|CyberAssess", content)
    parameter = inspect.signature(evidence_service.receive_version).parameters["file_type"]
    assert parameter.default is None and parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert "boto3==1.43.101" in (REPO_ROOT / "requirements.txt").read_text()
