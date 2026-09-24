"""AWS evidence adapter (P4-1): a consultant-triggered, read-only pull of AWS Config rule evaluations and Security Hub findings into versioned engagement Evidence, via AssumeRole with an engagement-bound external ID and a least-privilege session policy. Holds no credentials beyond the request."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore import xform_name
from botocore.config import Config
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    ConnectTimeoutError,
    ConnectionClosedError,
    CredentialRetrievalError,
    EndpointConnectionError,
    NoCredentialsError,
    PartialCredentialsError,
    ReadTimeoutError,
    SSOError,
    TokenRetrievalError,
)
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import settings
from app.models.audit_event import AuditEvent
from app.models.engagement import Engagement
from app.models.evidence import Evidence, EvidenceVersion
from app.services import evidence as evidence_service

logger = logging.getLogger(__name__)

AWS_OPERATIONS = (
    ("sts", "AssumeRole"),
    ("config", "DescribeConfigRules"),
    ("config", "GetComplianceDetailsByConfigRule"),
    ("securityhub", "GetFindings"),
)
SUPPORTED_REGIONS = frozenset(
    set(boto3.session.Session().get_available_regions("config"))
    & set(boto3.session.Session().get_available_regions("securityhub"))
    & set(boto3.session.Session().get_available_regions("sts"))
)
MAX_REGIONS = 4
MAX_DESCRIBE_RULE_PAGES = 40
MAX_CONFIG_RULES_PER_REGION = 300
MAX_EVALUATIONS_PER_RULE = 500
MAX_FINDINGS_PER_REGION = 2000
PULL_DEADLINE_SECONDS = 600
SESSION_DURATION_SECONDS = 900
EXTERNAL_ID_VERSION = "v1"
MIN_EXTERNAL_ID_SECRET_CHARS = 32
ROLE_ARN_RE = re.compile(
    r"arn:aws:iam::(?P<account>\d{12}):role/(?:[\w+=,.@-]+/)*[\w+=,.@-]{1,64}"
)
BOTO_CONFIG = Config(
    connect_timeout=5,
    read_timeout=30,
    retries={"max_attempts": 5, "mode": "standard"},
)
CONFIG_PROVENANCE_PREFIX = "aws_config:"
SECURITYHUB_PROVENANCE_PREFIX = "aws_securityhub:"
SUGGESTED_ROLE_NAME = "ComplianceEvidenceReadOnly"
CONSULTANT_PRINCIPAL_PLACEHOLDER = (
    "arn:aws:iam::<CONSULTANT_ACCOUNT_ID>:role/<CONSULTANT_ROLE_NAME>"
)
EXAMPLE_ACCOUNT_ID = "111122223333"
STEPS = (
    "trust_policy_check",
    "assume_role",
    "config",
    "securityhub",
    "deadline",
    "write",
)

NOT_CONFIGURED = (
    "AWS evidence collection is not configured. Set AWS_EXTERNAL_ID_SECRET in .env to a random value of "
    "at least 32 characters that differs from SESSION_SECRET, then restart."
)
INVALID_ACCOUNT_ID = "Enter the client's 12-digit AWS account ID."
INVALID_ROLE_ARN = "Enter the role ARN in the form arn:aws:iam::<account-id>:role/<role-name>."
ROLE_ACCOUNT_MISMATCH = "The role ARN must belong to the AWS account ID entered."
REGIONS_REQUIRED = "Enter at least one AWS region."
TOO_MANY_REGIONS = "Pull at most 4 regions at a time."
UNKNOWN_REGION = "Unknown or unsupported AWS region: {region}."
BASE_CREDENTIALS_UNAVAILABLE = (
    "This machine has no usable AWS credentials for the consultant identity. "
    "Sign in (for example with aws sso login) and try again. Nothing was collected."
)
ASSUME_ROLE_DENIED = (
    "Could not assume the role. Check the role ARN, that its trust policy names your consultant "
    "principal, and that it requires this engagement's external ID. Nothing was collected."
)
TRUST_POLICY_MISSING_EXTERNAL_ID = (
    "The role can be assumed without this engagement's external ID. Add the "
    "sts:ExternalId condition shown on this page to the role's trust policy, then try "
    "again. Nothing was collected."
)
ASSUMED_ACCOUNT_MISMATCH = (
    "The assumed role belongs to a different AWS account than the one entered. Nothing was collected."
)
STS_REGION_DISABLED = (
    "AWS STS is not activated in {region}. List an activated region first. Nothing was collected."
)
REGION_NOT_ENABLED = (
    "The temporary session is not valid in {region}; the region may not be enabled for this account. "
    "Nothing was collected."
)
PERMISSION_MISSING = (
    "The role is missing permission {action} in {region}. Apply the read-only permissions policy "
    "shown on this page. Nothing was collected."
)
SESSION_EXPIRED = (
    "The temporary AWS session expired before the pull finished. Pull fewer regions. Nothing was collected."
)
DEADLINE_EXCEEDED = (
    "The pull took longer than 10 minutes and was stopped. Pull fewer regions. Nothing was collected."
)
AWS_UNREACHABLE = "Could not reach AWS. Check the network connection and try again. Nothing was collected."
AWS_ERROR = "AWS returned an error ({code}) during {step}. Nothing was collected."
WRITE_FAILED = "The AWS data was retrieved but could not be saved as evidence. Nothing was collected."
ORIGIN_REJECTED = "Cross-site requests cannot start an AWS pull."


class AwsEvidenceError(Exception):
    status_code = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class AwsEngagementNotFound(AwsEvidenceError):
    status_code = 404

    def __init__(self, message: str = "Engagement not found"):
        super().__init__(message)


class AwsNotConfigured(AwsEvidenceError):
    pass


class AwsValidationError(AwsEvidenceError):
    pass


class AwsPullFailed(AwsEvidenceError):
    def __init__(self, message: str, *, step: str, error_code: str | None = None):
        self.step = step
        self.error_code = error_code
        super().__init__(message)


@dataclass(frozen=True)
class TemporaryCredentials:
    access_key_id: str = field(repr=False)
    secret_access_key: str = field(repr=False)
    session_token: str = field(repr=False)
    expiration: datetime


@dataclass(frozen=True)
class SourceSummary:
    source: str
    region: str
    status: str
    items: int
    created: int
    versioned: int
    unchanged: int
    rejected: int
    truncated: bool
    skipped_rules: int


@dataclass(frozen=True)
class PullResult:
    pull_id: str
    account_id: str
    regions: tuple[str, ...]
    sources: tuple[SourceSummary, ...]
    evidence_ids: tuple[str, ...]
    started_at: datetime
    finished_at: datetime


@dataclass
class _PendingSource:
    source: str
    region: str
    status: str
    documents: list[tuple[str, str, dict]]
    truncated: bool = False
    skipped_rules: int = 0
    created: int = 0
    versioned: int = 0
    unchanged: int = 0
    rejected: int = 0

    def summary(self) -> SourceSummary:
        return SourceSummary(
            source=self.source,
            region=self.region,
            status=self.status,
            items=len(self.documents),
            created=self.created,
            versioned=self.versioned,
            unchanged=self.unchanged,
            rejected=self.rejected,
            truncated=self.truncated,
            skipped_rules=self.skipped_rules,
        )


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _monotonic() -> float:
    return time.monotonic()


def _new_pull_id() -> str:
    return uuid.uuid4().hex


def is_configured() -> bool:
    secret = settings.aws_external_id_secret
    return len(secret) >= MIN_EXTERNAL_ID_SECRET_CHARS and secret != settings.session_secret


def external_id(engagement_id: str) -> str:
    message = f"evidence-external-id:{EXTERNAL_ID_VERSION}:{engagement_id}"
    return hmac.new(
        settings.aws_external_id_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def permissions_policy(account_id: str) -> dict:
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "ListConfigRules",
                "Effect": "Allow",
                "Action": "config:DescribeConfigRules",
                "Resource": "*",
            },
            {
                "Sid": "ReadConfigRuleEvaluations",
                "Effect": "Allow",
                "Action": "config:GetComplianceDetailsByConfigRule",
                "Resource": f"arn:aws:config:*:{account_id}:config-rule/*",
            },
            {
                "Sid": "ReadSecurityHubFindings",
                "Effect": "Allow",
                "Action": "securityhub:GetFindings",
                "Resource": f"arn:aws:securityhub:*:{account_id}:hub/default",
            },
        ],
    }


def trust_policy(
    external_id: str,
    consultant_principal_arn: str = CONSULTANT_PRINCIPAL_PLACEHOLDER,
) -> dict:
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowConsultantEvidencePull",
                "Effect": "Allow",
                "Principal": {"AWS": consultant_principal_arn},
                "Action": "sts:AssumeRole",
                "Condition": {"StringEquals": {"sts:ExternalId": external_id}},
            }
        ],
    }


def consultant_policy() -> dict:
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AssumeClientEvidenceRoles",
                "Effect": "Allow",
                "Action": "sts:AssumeRole",
                "Resource": "arn:aws:iam::*:role/ComplianceEvidenceReadOnly",
            }
        ],
    }


def session_policy_json(account_id: str) -> str:
    return json.dumps(permissions_policy(account_id), separators=(",", ":"), sort_keys=True)


def canonical_json(doc: dict) -> str:
    return json.dumps(doc, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat()


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", value)[:100]


def _short_hash(region: str, key: str) -> str:
    return hashlib.sha256(f"{region}\n{key}".encode("utf-8")).hexdigest()[:8]


def evidence_filename(source: str, *, account_id: str, region: str, key: str) -> str:
    if source == "aws_config":
        prefix = "aws-config"
    elif source == "aws_securityhub":
        prefix = "aws-securityhub"
    else:
        raise ValueError(f"Unknown AWS evidence source: {source}")
    return f"{prefix}_{account_id}_{region}_{_slug(key)}_{_short_hash(region, key)}.txt"


def config_rule_document(
    *,
    account_id: str,
    region: str,
    rule: dict,
    evaluations: list[dict],
    truncated: bool,
) -> dict:
    ordered = sorted(
        evaluations,
        key=lambda evaluation: (
            (evaluation.get("EvaluationResultIdentifier") or {})
            .get("EvaluationResultQualifier", {})
            .get("ResourceType")
            or "",
            (evaluation.get("EvaluationResultIdentifier") or {})
            .get("EvaluationResultQualifier", {})
            .get("ResourceId")
            or "",
            (evaluation.get("EvaluationResultIdentifier") or {})
            .get("EvaluationResultQualifier", {})
            .get("EvaluationMode")
            or "",
        ),
    )
    rendered = []
    for evaluation in ordered:
        qualifier = (evaluation.get("EvaluationResultIdentifier") or {}).get(
            "EvaluationResultQualifier", {}
        )
        rendered.append(
            {
                "resource_type": qualifier.get("ResourceType"),
                "resource_id": qualifier.get("ResourceId"),
                "evaluation_mode": qualifier.get("EvaluationMode") or None,
                "compliance_type": evaluation.get("ComplianceType"),
                "result_recorded_time": _iso(evaluation.get("ResultRecordedTime")),
                "config_rule_invoked_time": _iso(evaluation.get("ConfigRuleInvokedTime")),
                "annotation": evaluation.get("Annotation") or None,
            }
        )
    compliant = sum(item["compliance_type"] == "COMPLIANT" for item in rendered)
    non_compliant = sum(item["compliance_type"] == "NON_COMPLIANT" for item in rendered)
    source = rule.get("Source") or {}
    return {
        "schema": "aws_config_rule_evaluations/v1",
        "source": "aws_config",
        "account_id": account_id,
        "region": region,
        "rule": {
            "name": rule.get("ConfigRuleName"),
            "arn": rule.get("ConfigRuleArn"),
            "id": rule.get("ConfigRuleId"),
            "description": rule.get("Description") or None,
            "state": rule.get("ConfigRuleState"),
            "source_owner": source.get("Owner") or None,
            "source_identifier": source.get("SourceIdentifier") or None,
        },
        "compliance_types_requested": ["COMPLIANT", "NON_COMPLIANT"],
        "summary": {
            "compliant": compliant,
            "non_compliant": non_compliant,
            "total": len(rendered),
        },
        "truncated": truncated,
        "evaluations": rendered,
    }


_SEVERITY_LABELS = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL", "UNKNOWN")
_COMPLIANCE_STATUSES = ("PASSED", "FAILED", "WARNING", "NOT_AVAILABLE", "NONE")


def securityhub_documents(
    *,
    account_id: str,
    region: str,
    findings: list[dict],
    truncated: bool,
) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for finding in findings:
        grouped.setdefault(finding.get("GeneratorId"), []).append(finding)
    documents = []
    for generator_id in sorted(grouped):
        group = sorted(grouped[generator_id], key=lambda finding: finding.get("Id") or "")
        by_severity = {label: 0 for label in _SEVERITY_LABELS}
        by_compliance = {label: 0 for label in _COMPLIANCE_STATUSES}
        rendered = []
        for finding in group:
            severity = ((finding.get("Severity") or {}).get("Label") or "UNKNOWN")
            severity = severity if severity in _SEVERITY_LABELS[:-1] else "UNKNOWN"
            compliance = ((finding.get("Compliance") or {}).get("Status") or "NONE")
            compliance = compliance if compliance in _COMPLIANCE_STATUSES[:-1] else "NONE"
            by_severity[severity] += 1
            by_compliance[compliance] += 1
            rendered.append(
                {
                    "id": finding.get("Id"),
                    "title": finding.get("Title"),
                    "severity_label": (finding.get("Severity") or {}).get("Label") or None,
                    "compliance_status": (finding.get("Compliance") or {}).get("Status") or None,
                    "workflow_status": (finding.get("Workflow") or {}).get("Status") or None,
                    "product_name": finding.get("ProductName") or None,
                    "resources": [
                        {"type": resource.get("Type"), "id": resource.get("Id")}
                        for resource in finding.get("Resources", [])
                    ],
                    "first_observed_at": finding.get("FirstObservedAt") or None,
                    "last_observed_at": finding.get("LastObservedAt") or None,
                    "updated_at": finding.get("UpdatedAt"),
                }
            )
        documents.append(
            {
                "schema": "aws_securityhub_findings/v1",
                "source": "aws_securityhub",
                "account_id": account_id,
                "region": region,
                "generator_id": generator_id,
                "filters": {
                    "aws_account_id": account_id,
                    "region": region,
                    "record_state": "ACTIVE",
                },
                "summary": {
                    "by_severity": by_severity,
                    "by_compliance_status": by_compliance,
                    "total": len(rendered),
                },
                "truncated": truncated,
                "findings": rendered,
            }
        )
    return documents


def _sts_client(region: str):
    return boto3.session.Session().client("sts", region_name=region, config=BOTO_CONFIG)


def _service_client(credentials: TemporaryCredentials, service: str, region: str):
    return boto3.session.Session(
        aws_access_key_id=credentials.access_key_id,
        aws_secret_access_key=credentials.secret_access_key,
        aws_session_token=credentials.session_token,
        region_name=region,
    ).client(service, config=BOTO_CONFIG)


def _call(client, service: str, operation: str, **params) -> dict:
    if (service, operation) not in AWS_OPERATIONS:
        raise AssertionError(f"Unsupported AWS operation: {service}:{operation}")
    return getattr(client, xform_name(operation))(**params)


def _error_code(exc: ClientError) -> str:
    return str(exc.response.get("Error", {}).get("Code", "Unknown"))


def _map_error(
    exc,
    *,
    step: str,
    region: str | None,
    operation: str | None,
) -> AwsPullFailed:
    credential_errors = (
        NoCredentialsError,
        PartialCredentialsError,
        CredentialRetrievalError,
        TokenRetrievalError,
        SSOError,
    )
    if isinstance(exc, credential_errors):
        return AwsPullFailed(BASE_CREDENTIALS_UNAVAILABLE, step=step, error_code=type(exc).__name__)

    code = _error_code(exc) if isinstance(exc, ClientError) else type(exc).__name__
    if isinstance(exc, ClientError) and step in {"assume_role", "trust_policy_check"} and code in {
        "InvalidClientTokenId",
        "ExpiredToken",
        "ExpiredTokenException",
        "SignatureDoesNotMatch",
        "UnrecognizedClientException",
    }:
        return AwsPullFailed(BASE_CREDENTIALS_UNAVAILABLE, step=step, error_code=code)
    if isinstance(exc, (EndpointConnectionError, ConnectTimeoutError, ReadTimeoutError, ConnectionClosedError)):
        return AwsPullFailed(AWS_UNREACHABLE, step=step, error_code=code)
    if isinstance(exc, ClientError) and step == "assume_role" and code == "AccessDenied":
        return AwsPullFailed(ASSUME_ROLE_DENIED, step=step, error_code=code)
    if isinstance(exc, ClientError) and step in {"assume_role", "trust_policy_check"} and code == "RegionDisabledException":
        return AwsPullFailed(
            STS_REGION_DISABLED.format(region=region), step=step, error_code=code
        )
    if isinstance(exc, ClientError) and step in {"config", "securityhub"} and code in {
        "ExpiredToken",
        "ExpiredTokenException",
    }:
        return AwsPullFailed(SESSION_EXPIRED, step=step, error_code=code)
    if isinstance(exc, ClientError) and step in {"config", "securityhub"} and code in {
        "UnrecognizedClientException",
        "InvalidClientTokenId",
        "AuthFailure",
    }:
        return AwsPullFailed(REGION_NOT_ENABLED.format(region=region), step=step, error_code=code)
    if isinstance(exc, ClientError) and step in {"config", "securityhub"} and code in {
        "AccessDeniedException",
        "AccessDenied",
        "UnauthorizedOperation",
    }:
        action = f"{_service_for_step(step, operation)}:{operation}"
        return AwsPullFailed(
            PERMISSION_MISSING.format(action=action, region=region),
            step=step,
            error_code=code,
        )
    return AwsPullFailed(AWS_ERROR.format(code=code, step=step), step=step, error_code=code)


def _service_for_step(step: str, operation: str | None) -> str:
    if operation is not None:
        for service, candidate in AWS_OPERATIONS:
            if candidate == operation:
                return service
    return step


def _check_deadline(deadline: float) -> None:
    if _monotonic() > deadline:
        raise AwsPullFailed(DEADLINE_EXCEEDED, step="deadline")


def _mapped_call(
    client,
    service: str,
    operation: str,
    *,
    step: str,
    region: str,
    deadline: float,
    **params,
) -> dict:
    _check_deadline(deadline)
    try:
        return _call(client, service, operation, **params)
    except (ClientError, BotoCoreError) as exc:
        raise _map_error(exc, step=step, region=region, operation=operation) from exc


def _config_source(
    credentials: TemporaryCredentials,
    *,
    account_id: str,
    region: str,
    deadline: float,
) -> _PendingSource:
    client = _service_client(credentials, "config", region)
    rules: list[dict] = []
    next_token: str | None = None
    truncated = False
    for page_number in range(MAX_DESCRIBE_RULE_PAGES):
        params = {} if next_token is None else {"NextToken": next_token}
        response = _mapped_call(
            client,
            "config",
            "DescribeConfigRules",
            step="config",
            region=region,
            deadline=deadline,
            **params,
        )
        rules.extend(response.get("ConfigRules", []))
        next_token = response.get("NextToken") or None
        if not next_token:
            break
        if page_number == MAX_DESCRIBE_RULE_PAGES - 1:
            truncated = True
    active_rules = sorted(
        (rule for rule in rules if rule.get("ConfigRuleState") == "ACTIVE"),
        key=lambda rule: rule.get("ConfigRuleName") or "",
    )
    if len(active_rules) > MAX_CONFIG_RULES_PER_REGION:
        active_rules = active_rules[:MAX_CONFIG_RULES_PER_REGION]
        truncated = True

    documents: list[tuple[str, str, dict]] = []
    skipped_rules = 0
    for rule in active_rules:
        rule_name = rule.get("ConfigRuleName") or ""
        evaluations: list[dict] = []
        evaluations_truncated = False
        skipped = False
        next_token = None
        while True:
            params = {
                "ConfigRuleName": rule_name,
                "ComplianceTypes": ["COMPLIANT", "NON_COMPLIANT"],
                "Limit": 100,
            }
            if next_token:
                params["NextToken"] = next_token
            try:
                response = _mapped_call(
                    client,
                    "config",
                    "GetComplianceDetailsByConfigRule",
                    step="config",
                    region=region,
                    deadline=deadline,
                    **params,
                )
            except AwsPullFailed as exc:
                if exc.error_code != "NoSuchConfigRuleException":
                    raise
                skipped_rules += 1
                skipped = True
                break
            page = response.get("EvaluationResults", [])
            remaining = MAX_EVALUATIONS_PER_RULE - len(evaluations)
            if len(page) > remaining:
                evaluations.extend(page[:remaining])
                evaluations_truncated = True
                break
            evaluations.extend(page)
            next_token = response.get("NextToken") or None
            if len(evaluations) >= MAX_EVALUATIONS_PER_RULE:
                if next_token:
                    evaluations_truncated = True
                break
            if not next_token:
                break
        if skipped:
            continue
        document = config_rule_document(
            account_id=account_id,
            region=region,
            rule=rule,
            evaluations=evaluations,
            truncated=evaluations_truncated,
        )
        documents.append(
            (
                rule_name,
                evidence_filename(
                    "aws_config", account_id=account_id, region=region, key=rule_name
                ),
                document,
            )
        )
    return _PendingSource(
        source="aws_config",
        region=region,
        status="collected",
        documents=documents,
        truncated=truncated,
        skipped_rules=skipped_rules,
    )


def _securityhub_source(
    credentials: TemporaryCredentials,
    *,
    account_id: str,
    region: str,
    deadline: float,
) -> _PendingSource:
    client = _service_client(credentials, "securityhub", region)
    filters = {
        "AwsAccountId": [{"Value": account_id, "Comparison": "EQUALS"}],
        "Region": [{"Value": region, "Comparison": "EQUALS"}],
        "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
    }
    findings: list[dict] = []
    next_token: str | None = None
    truncated = False
    first_page = True
    while True:
        params = {"Filters": filters, "MaxResults": 100}
        if next_token:
            params["NextToken"] = next_token
        try:
            response = _mapped_call(
                client,
                "securityhub",
                "GetFindings",
                step="securityhub",
                region=region,
                deadline=deadline,
                **params,
            )
        except AwsPullFailed as exc:
            if first_page and exc.error_code == "InvalidAccessException":
                return _PendingSource(
                    source="aws_securityhub",
                    region=region,
                    status="not_enabled",
                    documents=[],
                )
            raise
        first_page = False
        page = response.get("Findings", [])
        remaining = MAX_FINDINGS_PER_REGION - len(findings)
        if len(page) > remaining:
            findings.extend(page[:remaining])
            truncated = True
            break
        findings.extend(page)
        next_token = response.get("NextToken") or None
        if len(findings) >= MAX_FINDINGS_PER_REGION:
            if next_token:
                truncated = True
            break
        if not next_token:
            break
    documents = [
        (
            document["generator_id"],
            evidence_filename(
                "aws_securityhub",
                account_id=account_id,
                region=region,
                key=document["generator_id"],
            ),
            document,
        )
        for document in securityhub_documents(
            account_id=account_id,
            region=region,
            findings=findings,
            truncated=truncated,
        )
    ]
    return _PendingSource(
        source="aws_securityhub",
        region=region,
        status="collected",
        documents=documents,
        truncated=truncated,
    )


def _normalise_inputs(account_id: str, role_arn: str, regions_raw: str) -> tuple[str, str, tuple[str, ...]]:
    clean_account = account_id.strip()
    if re.fullmatch(r"\d{12}", clean_account) is None:
        raise AwsValidationError(INVALID_ACCOUNT_ID)
    clean_role = role_arn.strip()
    role_match = ROLE_ARN_RE.fullmatch(clean_role)
    if role_match is None:
        raise AwsValidationError(INVALID_ROLE_ARN)
    if role_match.group("account") != clean_account:
        raise AwsValidationError(ROLE_ACCOUNT_MISMATCH)
    regions: list[str] = []
    for region in re.split(r"[\s,]+", regions_raw.strip().lower()):
        if region and region not in regions:
            regions.append(region)
    if not regions:
        raise AwsValidationError(REGIONS_REQUIRED)
    if len(regions) > MAX_REGIONS:
        raise AwsValidationError(TOO_MANY_REGIONS)
    for region in regions:
        if region not in SUPPORTED_REGIONS:
            raise AwsValidationError(UNKNOWN_REGION.format(region=region))
    return clean_account, clean_role, tuple(regions)


def _add_audit(
    db: Session,
    *,
    actor: str,
    action: str,
    entity_id: str,
    metadata: dict,
) -> None:
    db.add(
        AuditEvent(
            actor=actor,
            action=action,
            entity_type="engagement",
            entity_id=entity_id,
            metadata_json=json.dumps(metadata, sort_keys=True),
        )
    )


def _record_failure(
    db: Session,
    *,
    engagement_id: str,
    actor: str,
    pull_id: str,
    account_id: str,
    role_arn: str,
    regions: tuple[str, ...],
    step: str,
    error_code: str | None,
    message: str,
    started_at: datetime,
    written_paths: list[Path],
) -> None:
    db.rollback()
    for path in written_paths:
        path.unlink(missing_ok=True)
    _add_audit(
        db,
        actor=actor,
        action="aws_evidence.pull_failed",
        entity_id=engagement_id,
        metadata={
            "pull_id": pull_id,
            "account_id": account_id,
            "role_arn": role_arn,
            "regions": list(regions),
            "step": step,
            "error_code": error_code,
            "message": message,
            "started_at": _iso(started_at),
            "failed_at": _iso(_now()),
        },
    )
    db.commit()
    logger.warning("AWS evidence pull %s failed at %s (%s)", pull_id, step, error_code)


def _existing_evidence(db: Session, engagement_id: str, provenance: str, filename: str) -> Evidence | None:
    return (
        db.query(Evidence)
        .filter(
            Evidence.engagement_id == engagement_id,
            Evidence.uploaded_by == provenance,
            Evidence.original_filename == filename,
            Evidence.status.in_(("active", "invalidated")),
        )
        .order_by(Evidence.created_at, Evidence.id)
        .first()
    )


def pull_aws_evidence(
    db: Session,
    *,
    engagement_id: str,
    account_id: str,
    role_arn: str,
    regions_raw: str,
    actor: str = evidence_service.CONSULTANT_ACTOR,
) -> PullResult:
    engagement = db.get(Engagement, engagement_id)
    if engagement is None:
        raise AwsEngagementNotFound()
    if not is_configured():
        raise AwsNotConfigured(NOT_CONFIGURED)
    account_id, role_arn, regions = _normalise_inputs(account_id, role_arn, regions_raw)

    pull_id = _new_pull_id()
    started_at = _now()
    deadline = _monotonic() + PULL_DEADLINE_SECONDS
    session_policy = session_policy_json(account_id)
    written_paths: list[Path] = []
    pending_sources: list[_PendingSource] = []
    write_phase = False
    current_step = "assume_role"
    try:
        sts = _sts_client(regions[0])
        probe_params = {
            "RoleArn": role_arn,
            "RoleSessionName": f"evidence-probe-{pull_id}",
            "DurationSeconds": SESSION_DURATION_SECONDS,
            "Policy": session_policy,
        }
        try:
            _check_deadline(deadline)
            _call(sts, "sts", "AssumeRole", **probe_params)
        except ClientError as exc:
            if _error_code(exc) != "AccessDenied":
                raise _map_error(
                    exc,
                    step="trust_policy_check",
                    region=regions[0],
                    operation="AssumeRole",
                ) from exc
        except BotoCoreError as exc:
            raise _map_error(
                exc,
                step="trust_policy_check",
                region=regions[0],
                operation="AssumeRole",
            ) from exc
        else:
            raise AwsPullFailed(TRUST_POLICY_MISSING_EXTERNAL_ID, step="trust_policy_check")

        current_step = "assume_role"
        assume_response = _mapped_call(
            sts,
            "sts",
            "AssumeRole",
            step="assume_role",
            region=regions[0],
            deadline=deadline,
            **{
                "RoleArn": role_arn,
                "RoleSessionName": f"evidence-pull-{pull_id}",
                "DurationSeconds": SESSION_DURATION_SECONDS,
                "ExternalId": external_id(engagement.id),
                "Policy": session_policy,
            },
        )
        assumed_arn = assume_response.get("AssumedRoleUser", {}).get("Arn", "")
        assumed_parts = assumed_arn.split(":")
        if len(assumed_parts) < 5 or assumed_parts[4] != account_id:
            raise AwsPullFailed(ASSUMED_ACCOUNT_MISMATCH, step="assume_role")
        credentials_data = assume_response["Credentials"]
        credentials = TemporaryCredentials(
            access_key_id=credentials_data["AccessKeyId"],
            secret_access_key=credentials_data["SecretAccessKey"],
            session_token=credentials_data["SessionToken"],
            expiration=credentials_data["Expiration"],
        )

        for region in regions:
            current_step = "config"
            pending_sources.append(
                _config_source(
                    credentials,
                    account_id=account_id,
                    region=region,
                    deadline=deadline,
                )
            )
            current_step = "securityhub"
            pending_sources.append(
                _securityhub_source(
                    credentials,
                    account_id=account_id,
                    region=region,
                    deadline=deadline,
                )
            )

        write_phase = True
        evidence_ids: list[str] = []
        for source in pending_sources:
            provenance = (
                CONFIG_PROVENANCE_PREFIX + account_id
                if source.source == "aws_config"
                else SECURITYHUB_PROVENANCE_PREFIX + account_id
            )
            for _key, filename, document in source.documents:
                content = canonical_json(document).encode("utf-8")
                digest = evidence_service.sha256_hex(content)
                existing = _existing_evidence(db, engagement.id, provenance, filename)
                if existing is None:
                    evidence, version = evidence_service.receive_evidence(
                        db,
                        engagement_id=engagement.id,
                        assessment_id=None,
                        filename=filename,
                        content=content,
                        category=None,
                        uploaded_by=provenance,
                        actor=provenance,
                        file_type="txt",
                        change_reason=f"AWS pull {pull_id}: first collection",
                    )
                    source.created += 1
                    evidence_ids.append(evidence.id)
                else:
                    current = evidence_service.current_version(db, existing.id)
                    if current is not None and current.file_hash_sha256 == digest:
                        source.unchanged += 1
                        continue
                    version = evidence_service.receive_version(
                        db,
                        evidence_id=existing.id,
                        filename=filename,
                        content=content,
                        change_reason=f"AWS pull {pull_id}: AWS data changed",
                        actor=provenance,
                        file_type="txt",
                    )
                    source.versioned += 1
                    evidence_ids.append(existing.id)
                written_paths.append(evidence_service.blob_path(version.storage_path))
                released = evidence_service.release_from_quarantine(db, version_id=version.id)
                if released.status == "active":
                    released.extracted_text = content.decode("utf-8")
                else:
                    source.rejected += 1

        current_step = "write"
        finished_at = _now()
        source_summaries = tuple(source.summary() for source in pending_sources)
        _add_audit(
            db,
            actor=actor,
            action="aws_evidence.pull_completed",
            entity_id=engagement.id,
            metadata={
                "pull_id": pull_id,
                "account_id": account_id,
                "role_arn": role_arn,
                "regions": list(regions),
                "role_session_name": f"evidence-pull-{pull_id}",
                "external_id_version": EXTERNAL_ID_VERSION,
                "started_at": _iso(started_at),
                "finished_at": _iso(finished_at),
                "sources": [asdict(summary) for summary in source_summaries],
                "evidence_ids": evidence_ids,
            },
        )
        db.commit()
        result = PullResult(
            pull_id=pull_id,
            account_id=account_id,
            regions=regions,
            sources=source_summaries,
            evidence_ids=tuple(evidence_ids),
            started_at=started_at,
            finished_at=finished_at,
        )
        logger.info(
            "AWS evidence pull %s completed: %d created, %d versioned, %d unchanged",
            pull_id,
            sum(source.created for source in pending_sources),
            sum(source.versioned for source in pending_sources),
            sum(source.unchanged for source in pending_sources),
        )
        return result
    except AwsPullFailed as exc:
        _record_failure(
            db,
            engagement_id=engagement.id,
            actor=actor,
            pull_id=pull_id,
            account_id=account_id,
            role_arn=role_arn,
            regions=regions,
            step=exc.step,
            error_code=exc.error_code,
            message=exc.message,
            started_at=started_at,
            written_paths=written_paths if write_phase else [],
        )
        raise
    except Exception as exc:
        failure = AwsPullFailed(
            WRITE_FAILED if write_phase else AWS_ERROR.format(code=type(exc).__name__, step=current_step),
            step="write" if write_phase else current_step,
            error_code=None if write_phase else type(exc).__name__,
        )
        _record_failure(
            db,
            engagement_id=engagement.id,
            actor=actor,
            pull_id=pull_id,
            account_id=account_id,
            role_arn=role_arn,
            regions=regions,
            step=failure.step,
            error_code=failure.error_code,
            message=failure.message,
            started_at=started_at,
            written_paths=written_paths if write_phase else [],
        )
        raise failure from exc


def aws_evidence_rows(db: Session, engagement_id: str) -> list[dict]:
    evidence_rows = (
        db.query(Evidence)
        .filter(
            Evidence.engagement_id == engagement_id,
            or_(
                Evidence.uploaded_by.like(f"{CONFIG_PROVENANCE_PREFIX}%"),
                Evidence.uploaded_by.like(f"{SECURITYHUB_PROVENANCE_PREFIX}%"),
            ),
        )
        .order_by(Evidence.original_filename, Evidence.created_at, Evidence.id)
        .all()
    )
    if not evidence_rows:
        return []
    versions = (
        db.query(EvidenceVersion)
        .filter(EvidenceVersion.evidence_id.in_([row.id for row in evidence_rows]))
        .order_by(EvidenceVersion.evidence_id, EvidenceVersion.version_number)
        .all()
    )
    versions_by_evidence: dict[str, list[EvidenceVersion]] = {}
    for version in versions:
        versions_by_evidence.setdefault(version.evidence_id, []).append(version)
    rows = []
    for evidence in evidence_rows:
        prefix = (
            CONFIG_PROVENANCE_PREFIX
            if evidence.uploaded_by.startswith(CONFIG_PROVENANCE_PREFIX)
            else SECURITYHUB_PROVENANCE_PREFIX
        )
        item_versions = versions_by_evidence.get(evidence.id, [])
        active = [version for version in item_versions if version.status == "active"]
        current = active[-1] if active else None
        newest = max(
            item_versions,
            key=lambda version: (version.created_at, version.id),
            default=None,
        )
        rows.append(
            {
                "id": evidence.id,
                "filename": evidence.original_filename,
                "source": prefix[:-1],
                "account_id": evidence.uploaded_by.removeprefix(prefix),
                "status": evidence.status,
                "current_version_number": current.version_number if current else None,
                "version_count": len(item_versions),
                "last_collected_at": newest.created_at if newest else None,
            }
        )
    return rows


def last_pull_inputs(db: Session, engagement_id: str) -> dict | None:
    event = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.entity_type == "engagement",
            AuditEvent.entity_id == engagement_id,
            AuditEvent.action == "aws_evidence.pull_completed",
        )
        .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
        .first()
    )
    if event is None or event.metadata_json is None:
        return None
    try:
        metadata = json.loads(event.metadata_json)
        regions = metadata["regions"]
        if not isinstance(regions, list) or not all(isinstance(region, str) for region in regions):
            return None
        return {
            "account_id": str(metadata["account_id"]),
            "role_arn": str(metadata["role_arn"]),
            "regions": ", ".join(regions),
        }
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def page_context(db: Session, engagement: Engagement) -> dict:
    previous = last_pull_inputs(db, engagement.id)
    account_id = previous["account_id"] if previous else EXAMPLE_ACCOUNT_ID
    form_values = {
        "account_id": previous["account_id"] if previous else "",
        "role_arn": previous["role_arn"] if previous else "",
        "regions": previous["regions"] if previous else "",
    }
    configured = is_configured()
    page_external_id = external_id(engagement.id) if configured else None
    return {
        "engagement_id": engagement.id,
        "configured": configured,
        "external_id": page_external_id,
        "trust_policy_json": (
            json.dumps(trust_policy(page_external_id), indent=2) if configured else None
        ),
        "permissions_policy_json": (
            json.dumps(permissions_policy(account_id), indent=2) if configured else None
        ),
        "policy_account_note": (
            None
            if previous
            else "Example account ID shown; the policy uses the account you pull."
        ),
        "consultant_policy_json": json.dumps(consultant_policy(), indent=2) if configured else None,
        "suggested_role_name": SUGGESTED_ROLE_NAME,
        "not_configured_message": NOT_CONFIGURED,
        "form_values": form_values,
        "error": None,
        "result": None,
        "rows": aws_evidence_rows(db, engagement.id),
    }
