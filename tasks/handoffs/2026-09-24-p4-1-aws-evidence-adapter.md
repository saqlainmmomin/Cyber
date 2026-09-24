# P4-1: AWS evidence adapter: a consultant-triggered, read-only pull of AWS Config rule evaluations and Security Hub findings into versioned engagement Evidence, through AssumeRole with an engagement-bound external ID, a pinned least-privilege policy, and no stored credentials

**Plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`, Phase 4, task P4-1: "Input: AWS account ID, role ARN, external ID, region(s)"; "AssumeRole with external ID (no long-lived credentials)"; "Pull Config rule evaluations: compliant/non-compliant per resource (D10)"; "Pull Security Hub findings with severity (D10)"; "Each result becomes an Evidence item with `uploaded_by=aws_config:{account_id}` or `aws_securityhub:{account_id}`"; "Manual trigger only. Read-only. No write access, no continuous monitoring."; test: "Mock boto3 responses. Verify Evidence + EvidenceVersion created with correct provenance. Verify least-privilege policy documented." Phase 4 exit criterion: "AWS evidence adapter working with mocked and (optionally) real AWS account". Decision **D10** in `tasks/2026-09-21-adversarial-review.md`: "Config rules + Security Hub findings. Pull active Config rule evaluations (compliant/non-compliant per resource) and Security Hub findings with severity. No resource inventory in v1."
**Owner:** Codex, from this Claude spec (`tasks/agent-ownership.md`: "P4-1 AWS evidence adapter | Claude designs IAM/security boundary → Codex implements boto3 plumbing"; the same doc names AWS AssumeRole as a security boundary, "anything where a subtle mistake is a vulnerability, not a bug"). **The IAM policy, the trust policy, the external-ID scheme, the AssumeRole call, the set of AWS operations and the credential-handling rules are fixed below. Do not change them, add an AWS operation, widen a policy, or add a credential input.** Every other fork is closed below too.

> **If the code forces a deviation from this design, stop and report it in `## Results`. Do not pick an alternative.**

Merge gate: the standard `[AR]` adversarial review (`tasks/todo.md` tags Phase 4 `[AR: IAM/external ID, retention/purge, performance]`; this task is the "IAM/external ID" part).
**Depends on:** P2-1 (evidence service, merged), P2-5 (engagement-level evidence precedent, merged). `main` is at `a4ac3d9`.
**Runs in parallel with:** P4-2, P4-3, P4-4. The plan calls them independent, but four files may be touched by more than one Phase 4 branch; the coordination rules are in **D-P4-1-Q**.
**Blocks:** nothing in Phase 4. (P4-2's seed script may use AWS evidence later; it does not need to.)
**Failing contract suite: none pre-written.** A grep of `tests/` for `aws`, `boto`, `P4-1`, `securityhub`, `assume_role` and `external_id` finds nothing that tests this task (across `tests/`, `app/` and `scripts/`, the only `AWS` hits are two question strings in `scripts/generate_facilitator_guide.py`). **Codex writes `tests/test_aws_evidence.py` itself** from `## Test scenarios`. Every scenario listed is required. You may add cases, but you may not drop or weaken one. **No existing test file is modified.**

## Step 0 (for the dispatching Claude session, before Codex starts)

`boto3` is not installed in `/Users/saqlainmomin/dpdpa-gap-tool/.venv`, and Codex's sandbox has had no network access in earlier tasks (P1-5's Results: "network access prevented installation"). **Before dispatch, run `/Users/saqlainmomin/dpdpa-gap-tool/.venv/bin/pip install boto3==1.43.101`** (it pulls `botocore==1.43.101`, `jmespath`, `s3transfer`). Every worktree symlinks this `.venv`, so this is a one-time install.

**Codex:** your first action is `.venv/bin/python -c "import boto3, botocore; print(boto3.__version__, botocore.__version__)"`. It must print `1.43.101 1.43.101`. If it doesn't, **stop and report in `## Results`**. Don't try to install, vendor, or stub out `boto3`, and don't add `moto` (D-P4-1-O).

## Goal

1. On a new page, `/engagements/{engagement_id}/aws-evidence`, the consultant sees exactly what the **client** must set up in their AWS account: a role trust policy that names the consultant's principal and requires **this engagement's external ID**, and a read-only permissions policy with exactly three actions. Both are rendered from the same Python functions the pull uses.
2. The consultant enters the client's **account ID**, **role ARN** and **regions** and presses "Pull AWS evidence". CyberAssess assumes the role through STS with the engagement's external ID and a session policy that is the same least-privilege policy. It then reads **active AWS Config rules and their compliant/non-compliant evaluations per resource**, and **active Security Hub findings with severity**, for that account only.
3. Each Config rule (per region), and each Security Hub finding generator (per region), becomes one **engagement-level `Evidence`** item with `uploaded_by = "aws_config:{account_id}"` or `"aws_securityhub:{account_id}"`, holding a canonical JSON text blob. A later pull adds a **new `EvidenceVersion`** to the same Evidence when the AWS data changed, and nothing when it didn't.
4. The pull is all-or-nothing: either every item is written and one `aws_evidence.pull_completed` audit event records it, or nothing is written and one `aws_evidence.pull_failed` audit event says why.
5. No AWS credential of any kind is accepted as input, stored in the database, written to disk, logged, or rendered. The temporary session credentials exist only in memory for the length of the request.

## Current state

Grounded against `a4ac3d9` on `main`. Baseline `.venv/bin/pytest -q` → **502 passed, 126 warnings, 1 error** (I ran it in a fresh worktree at `a4ac3d9`; the error is the known one-time `tests/test_workpaper.py::test_smoke_full_assessment_traceability` teardown artifact from `_guard_dev_database_untouched`, documented since P2-3). `alembic heads` → `4e8c1a9d2b57 (head)`. Re-locate everything by symbol name.

- **`requirements.txt`** pins 14 packages, one per line as `name==version`; no `boto3`, `botocore` or `moto`. The `.venv` is Python 3.13.13.
- **`app/models/evidence.py`**: `Evidence` (`id`, `engagement_id` FK, `assessment_id` nullable FK, `document_category` nullable, `original_filename`, `storage_path`, `file_hash_sha256`, `file_size_bytes`, `mime_type`, `status`, **`uploaded_by: String(255)`**, `created_at`). The comment on `original_filename` says the v1 fields "are frozen at creation". `EvidenceVersion` (`id`, `evidence_id`, `version_number`, `storage_path`, `file_hash_sha256`, `file_size_bytes`, `change_reason` nullable, `status` server default `quarantined`, `original_filename`, `mime_type`, `extracted_text` nullable, `created_at`), unique `(evidence_id, version_number)`. No JSON/config column that could hold an AWS connection.
- **`app/services/evidence.py`** (P2-1), read in full:
  - `EVIDENCE_STATUSES = ("quarantined", "active", "rejected", "invalidated", "archived")`, `VERSION_STATUSES`, `BLOCKING_DUPLICATE_STATUSES = ("quarantined", "active", "invalidated")`, `CONSULTANT_ACTOR = "consultant"`, `SCAN_ACTOR = "system:scan-placeholder"`, **`FILE_TYPE_TO_MIME` includes `"txt": "text/plain"`**.
  - `_file_type(filename, supplied)`: uses `detect_file_type(filename)` **only when `supplied is None`**, else `supplied.lower()`; raises `UnsupportedFileType` unless the result is in `FILE_TYPE_TO_MIME`. `app/services/document_processor.detect_file_type` returns `None` for `.txt`, and **`extract_text` raises `ValueError` for `txt`**. So `ingest_upload`, `ingest_engagement_upload` and `ingest_new_version` (which all call `extract_text`) cannot ingest text. That is the P3-4 Results deviation ("`.txt` rejected").
  - **`receive_evidence(db, *, engagement_id, assessment_id, filename, content, category, uploaded_by, actor, file_type=None, evidence_id=None, created_at=None, change_reason=None, allow_duplicate=False) -> (Evidence, EvidenceVersion)`**: accepts an explicit `file_type`; refuses empty content; unless `allow_duplicate`, raises `DuplicateEvidence` when a same-engagement, same-`assessment_id` (NULL matches NULL) Evidence in a blocking status has a version with the same SHA-256; writes the blob with exclusive create at `evidence/{engagement_id}/{evidence_id}/v1.{type}`; adds both rows `quarantined` plus two `audit_events` (`evidence.created` with metadata `assessment_id, sha256, size_bytes, uploaded_by, version_id`; `evidence_version.created`); **flushes, does not commit**; on any exception it calls **`db.rollback()`** and unlinks its own blob.
  - **`receive_version(db, *, evidence_id, filename, content, change_reason, actor) -> EvidenceVersion`**: needs Evidence status `active`/`invalidated`, no quarantined version, a non-blank `change_reason`, content different from the current active version (else `DuplicateEvidence`); **calls `_file_type(filename, None)`, so it has no way to accept `txt`**; writes `v{n}.{type}`; flushes; rolls back and unlinks on error.
  - `release_from_quarantine(db, *, version_id, actor=SCAN_ACTOR)`: placeholder scan (always passes, logs a warning), supersedes prior active versions, activates the version and (if quarantined) the Evidence, writing status audit events; flushes.
  - `current_version`, `verify_version(db, version_id) -> bool` (blob exists and hashes match), `sha256_hex`, `blob_path`, `evidence_detail`.
  - Only `release_from_quarantine` precedent for text blobs: **`scripts/migrate_documents_to_evidence.py`** calls `receive_evidence(..., file_type="txt", ...)`, then `release_from_quarantine(...)`, then sets `version.extracted_text` directly, then commits. **This task follows that pattern.**
- **Engagement-level evidence precedent (P2-5, `app/services/magic_links.py`):** `client_actor(link) = f"client_link:{link.id}"` is used as both `uploaded_by` and `actor`; `receive_client_upload` calls `ingest_engagement_upload(..., assessment_id=None)`; `client_upload_rows` lists rows with `Evidence.uploaded_by.like("client_link:%")`. Engagement-level Evidence (`assessment_id IS NULL`) enters an assessment's analysis only when mapped with `evidence_service.map_evidence` (`active_versions_in_scope` covers assessment-owned or `EvidenceUse`-mapped Evidence).
- **Routers.** `app/routers/magic.py` is the model for an engagement-scoped consultant surface outside `web.py`: `router = APIRouter(include_in_schema=False)`, `from app.routers.web import templates`, a `_CONSULTANT_HEADERS = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}` dict, errors rendered into a partial with status 200 (404 for an unknown engagement), and the partial re-rendered with `hx-target` + `hx-swap="outerHTML"`. `app/main.py` imports routers in one alphabetical `from app.routers import (analysis, assessments, conclusions, desk_review, documents, evidence, findings, integrated_reports, magic, questionnaire, reports, review, snapshots, web,)` block and registers them in two groups: `# API routes` (13 `include_router` lines) and `# Web portal routes` (`magic.router`, then `web.router`).
- **`app/routers/web.py`**: engagement pages `engagement_detail` (`GET /engagements/{engagement_id}`), `integrated_reports_page`, `remediation_tracker_page` all do `db.get(Engagement, …)` → `HTTPException(404, "Engagement not found")`, `db.get(Client, engagement.client_id)` → `HTTPException(404, "Client not found")`. **`web.py` is not modified by this task.**
- **`app/templates/pages/engagement_detail.html`**: under the header `<p class="mt-2 text-sm text-gray-500 dark:text-gray-400">{{ client.name }} · …</p>` there are two links on consecutive lines: `…/integrated-reports` ("Integrated reports →") and `…/remediation` with classes `mt-2 ml-4 inline-block text-sm font-medium text-brand dark:text-navy-300 hover:underline` ("Remediation tracker →"). The page ends with `{% include "partials/magic_links.html" %}`.
- **`app/config.py`**: `Settings(BaseSettings)` with `session_secret: str = _DEFAULT_SESSION_SECRET` (`"change-me-in-production"`), a `warn_insecure_defaults` model validator, and `model_config = {"env_file": ".env", ..., "extra": "ignore"}`. **No AWS setting of any kind.** `tests/test_config_security_warnings.py` asserts that custom `session_secret`/`auditor_password` produce **no** warning records; a new setting must not add a warning.
- **`app/models/audit_event.py`**: `AuditEvent(id, actor, action, entity_type, entity_id String(36), metadata_json Text, created_at)`. Writers use `json.dumps(metadata, sort_keys=True)`.
- **CORS**: `app/main.py` adds `CORSMiddleware(allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])`. There is no auth and no CSRF protection anywhere (single-user MVP, by design). This matters for D-P4-1-L.
- **Logging**: nothing in `app/` configures logging levels (`basicConfig`/`dictConfig`/`setLevel` are absent).
- **Guards other tests enforce on new files:** `tests/test_white_label.py::test_no_hardcoded_product_name_in_client_surfaces` fails if `CyberAssess` appears anywhere under `app/templates/`. `tests/test_no_blended_scoring.py` forbids `overall_score` in templates.
- **AWS facts verified for this spec** (not from memory): botocore `1.43.101`'s service models (installed in a scratch venv) and AWS's programmatic Service Authorization Reference (`servicereference.us-east-1.amazonaws.com/v1/{config,securityhub,sts}/…json`):
  - `config.DescribeConfigRules` input `ConfigRuleNames, Filters, NextToken` (no limit); output `ConfigRules, NextToken`. **IAM: no resource type (resource-level permissions not supported), so its `Resource` must be `"*"`.**
  - `config.GetComplianceDetailsByConfigRule` input `ConfigRuleName` (required), `ComplianceTypes` (enum `COMPLIANT | NON_COMPLIANT | NOT_APPLICABLE | INSUFFICIENT_DATA`), `Limit` (0–100), `NextToken`; output `EvaluationResults, NextToken`. `EvaluationResult` = `EvaluationResultIdentifier{EvaluationResultQualifier{ConfigRuleName, ResourceType, ResourceId, EvaluationMode}, OrderingTimestamp, ResourceEvaluationId}, ComplianceType, ResultRecordedTime, ConfigRuleInvokedTime, Annotation, ResultToken`. **IAM resource type `ConfigRule`: `arn:${Partition}:config:${Region}:${Account}:config-rule/${ConfigRuleId}`** (the rule **id**, not its name).
  - `ConfigRule` shape: `ConfigRuleName, ConfigRuleArn, ConfigRuleId, Description, Scope, Source{Owner, SourceIdentifier, …}, InputParameters, MaximumExecutionFrequency, ConfigRuleState, CreatedBy, EvaluationModes, RuleEvaluationVisibility`.
  - `securityhub.GetFindings` input `Filters, SortCriteria, NextToken, MaxResults` (1–100); `AwsSecurityFindingFilters` has `AwsAccountId`, `Region`, `RecordState`. Required finding fields: `SchemaVersion, Id, ProductArn, GeneratorId, AwsAccountId, CreatedAt, UpdatedAt, Title, Description, Resources`. **IAM resource type `hub`: `arn:${Partition}:securityhub:${Region}:${Account}:hub/default`.** Not-enabled Security Hub raises the modeled `InvalidAccessException`.
  - `sts.AssumeRole` input includes `RoleArn`, `RoleSessionName` (2–64, `[\w+=,.@-]*`), `Policy`, `DurationSeconds` (900–43200), `ExternalId` (2–1224, `[\w+=,.@:\/-]*`); condition key `sts:ExternalId` exists.
  - `botocore.stub.Stubber` ships with botocore, validates every stubbed call's parameters against the real service model, and raises on an unexpected operation. `add_client_error("assume_role", service_error_code="AccessDenied", http_status_code=403)` produces a `ClientError` with `response["Error"]["Code"] == "AccessDenied"` (checked).
  - The intersection of `boto3.session.Session().get_available_regions(...)` for `config`, `securityhub` and `sts` in botocore 1.43.101 is **34 commercial (`aws` partition) regions**, computed offline from bundled endpoint data.
  - botocore exception classes present: `NoCredentialsError`, `PartialCredentialsError`, `CredentialRetrievalError`, `TokenRetrievalError`, `SSOError` (parent of `SSOTokenLoadError`, `UnauthorizedSSOTokenError`), `EndpointConnectionError`/`ConnectTimeoutError` (under `ConnectionError`), `ReadTimeoutError`/`ConnectionClosedError` (under `HTTPClientError`), `BotoCoreError`, `ClientError`.

## Decisions (made here so they are not relitigated)

### D-P4-1-A. Scope of AWS access: exactly four operations, all read-only, through one guarded helper

```python
AWS_OPERATIONS = (
    ("sts", "AssumeRole"),
    ("config", "DescribeConfigRules"),
    ("config", "GetComplianceDetailsByConfigRule"),
    ("securityhub", "GetFindings"),
)
```

- **No other AWS API is called, ever.** No `GetCallerIdentity`, no `DescribeComplianceByConfigRule`, no `GetEnabledStandards`, no `ListDiscoveredResources` or any resource-inventory call (D10: "No resource inventory in v1"), no S3, no paginator objects.
- **Every AWS call goes through one function**, `_call(client, service: str, operation: str, **params) -> dict`. It raises `AssertionError` **before touching the client** if `(service, operation)` is not in `AWS_OPERATIONS`, then calls `getattr(client, botocore.xform_name(operation))(**params)` (`from botocore import xform_name`). No other line in the module calls an AWS client method. This makes the operation set checkable from source (scenario 10).
- `DescribeComplianceByConfigRule` is **not** used: `DescribeConfigRules` gives the active rules and `GetComplianceDetailsByConfigRule` gives the per-resource results that D10 asks for; the rule-level rollup is derived locally. Fewer actions is a smaller grant.
- **Why not `GetFindingsV2`/Security Hub v2:** D10 asks for "Security Hub findings with severity"; the ASFF `GetFindings` API is the one every Security Hub CSPM account has, and its `hub/default` resource is well-defined. v2 is open question 3.

### D-P4-1-B. The client-side permissions policy (exact; also used as the STS session policy)

`permissions_policy(account_id: str) -> dict` returns exactly this, with `111122223333` replaced by `account_id`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListConfigRules",
      "Effect": "Allow",
      "Action": "config:DescribeConfigRules",
      "Resource": "*"
    },
    {
      "Sid": "ReadConfigRuleEvaluations",
      "Effect": "Allow",
      "Action": "config:GetComplianceDetailsByConfigRule",
      "Resource": "arn:aws:config:*:111122223333:config-rule/*"
    },
    {
      "Sid": "ReadSecurityHubFindings",
      "Effect": "Allow",
      "Action": "securityhub:GetFindings",
      "Resource": "arn:aws:securityhub:*:111122223333:hub/default"
    }
  ]
}
```

- **Three actions, one per statement, each a single string (never a list, never a wildcard such as `config:Get*` or `securityhub:*`).** No `Deny`, no `NotAction`, no `NotResource`, no `Condition`.
- **The one `"Resource": "*"` is forced by AWS**, not chosen: `config:DescribeConfigRules` has no resource type in the Service Authorization Reference, so IAM cannot scope it. In a role's own identity policy, `"*"` for Config can only reach that account's own rules (an identity policy can't grant access into another account). It exposes only rule metadata (names, descriptions, source identifiers), no resource data. This is the only `"*"` resource, and scenario 3 pins that.
- The other two are **account-scoped ARNs**. The region segment is `*` so the policy doesn't need editing when the consultant pulls another region; the rule segment is `*` because the ARN uses the opaque `ConfigRuleId`, which the client can't know in advance, and the pull must read every active rule. `hub/default` is a literal, not a wildcard.
- **Partition `aws` only.** GovCloud (`aws-us-gov`) and China (`aws-cn`) are out of scope; the role-ARN validation (D-P4-1-E) rejects them.
- **No `ReadOnlyAccess`/`SecurityAudit` managed policy is recommended.** The page and the doc say to attach this inline policy and nothing else.

### D-P4-1-C. The client-side trust policy, and the consultant-side identity

`trust_policy(external_id: str, consultant_principal_arn: str = CONSULTANT_PRINCIPAL_PLACEHOLDER) -> dict` returns exactly:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowConsultantEvidencePull",
      "Effect": "Allow",
      "Principal": {"AWS": "<consultant_principal_arn>"},
      "Action": "sts:AssumeRole",
      "Condition": {"StringEquals": {"sts:ExternalId": "<external_id>"}}
    }
  ]
}
```

```python
CONSULTANT_PRINCIPAL_PLACEHOLDER = "arn:aws:iam::<CONSULTANT_ACCOUNT_ID>:role/<CONSULTANT_ROLE_NAME>"
SUGGESTED_ROLE_NAME = "ComplianceEvidenceReadOnly"
```

- `StringEquals`, never `StringLike`. The principal is a **specific role** in the consultant's account, never the account root (`arn:aws:iam::<id>:root` would delegate the decision to every principal in the consultant's account); the page and the doc say so in one sentence each.
- **The consultant principal is shown as the placeholder**; CyberAssess does not discover it. (`sts:GetCallerIdentity` is not in `AWS_OPERATIONS`, and for an SSO session it returns an `assumed-role` ARN that isn't a valid trust principal.) The consultant replaces the placeholder with their own role ARN.
- **Consultant-side identity policy** (documented only, in `docs/operations/aws-evidence.md` and on the page; the app never uses it): `consultant_policy() -> dict` returns
  ```json
  {"Version": "2012-10-17", "Statement": [{"Sid": "AssumeClientEvidenceRoles", "Effect": "Allow",
   "Action": "sts:AssumeRole", "Resource": "arn:aws:iam::*:role/ComplianceEvidenceReadOnly"}]}
  ```
  The account segment is `*` because client accounts vary; the role name bounds it. If a client uses a different role name, the consultant adds that role's ARN. **The app does not require the suggested role name**; it validates only the ARN's shape and account (D-P4-1-E).
- **Where the consultant's base credentials come from:** the botocore **default credential chain** on the machine running CyberAssess (for example an IAM Identity Center session after `aws sso login`, or `AWS_PROFILE`). CyberAssess never reads, writes or asks for access keys, and has **no setting** for them. The doc recommends short-lived SSO credentials and says long-lived IAM user keys defeat the point of this design. That's guidance; the app can't detect the credential type and doesn't try.

### D-P4-1-D. The external ID: generated by CyberAssess, bound to the engagement, derived (never stored), never typed

The plan lists "external ID" as an input. **It is an input to the AssumeRole call, but it is not a form field.** AWS's confused-deputy guidance says the third party (here, the consultant's tool) generates a unique external ID per customer. If the consultant could type any value, one client could hand over another client's role ARN and external ID, and the tool would pull that other client's data into the wrong engagement. So:

```python
EXTERNAL_ID_VERSION = "v1"
MIN_EXTERNAL_ID_SECRET_CHARS = 32

def external_id(engagement_id: str) -> str:
    """HMAC-SHA256(settings.aws_external_id_secret, f"evidence-external-id:{EXTERNAL_ID_VERSION}:{engagement_id}"), hex."""
```

- The result is 64 lowercase hex characters (fits `ExternalId`'s 2–1224 length and `[\w+=,.@:\/-]*` pattern), stable for an engagement, different for every engagement, and unguessable without the secret. Use `hmac.new(key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()`.
- **Nothing is stored.** No table, no column, no audit metadata, no evidence blob holds the external ID. It is recomputed when the page renders and when a pull runs. (Storing it would need a schema change and an Alembic revision that would race P4-3/P4-4's possible revisions; deriving needs neither.)
- **New setting** in `app/config.py`, after `firm_primary_hex`: `aws_external_id_secret: str = ""`. **No warning is added** to `warn_insecure_defaults` (an empty value just disables the feature, and `tests/test_config_security_warnings.py` must still pass unchanged).
- `is_configured() -> bool` is `True` exactly when `len(settings.aws_external_id_secret) >= MIN_EXTERNAL_ID_SECRET_CHARS` **and** `settings.aws_external_id_secret != settings.session_secret` (key separation: the session cookie key and the AWS trust key must differ). When `False`, the page shows `NOT_CONFIGURED` and no form, no external ID and no trust policy; a pull raises `AwsNotConfigured(NOT_CONFIGURED)` **before any AWS call or DB write**.
- `.env.example` gains, after the white-label block: a comment line `# AWS evidence pull (P4-1): random value, 32+ characters, different from SESSION_SECRET` and `# AWS_EXTERNAL_ID_SECRET=`.
- **Rotating the secret changes every engagement's external ID**, so every client must update their trust policy. That is documented in the doc, not handled in code (open question 2).
- The external ID is **displayed** on the AWS evidence page (the client needs it). It is not a password, but it is treated as sensitive: never logged, never in audit metadata, never in exception messages, and the page is served `Cache-Control: no-store` (D-P4-1-L).

### D-P4-1-E. Inputs and validation (exact order; no AWS call and no write on any failure)

`pull_aws_evidence` validates, in this order, and raises `AwsValidationError(message)` on the first failure:

1. `account_id.strip()` matches `^\d{12}$` → else `INVALID_ACCOUNT_ID`.
2. `role_arn.strip()` fully matches `ROLE_ARN_RE = re.compile(r"arn:aws:iam::(?P<account>\d{12}):role/(?:[\w+=,.@-]+/)*[\w+=,.@-]{1,64}")` → else `INVALID_ROLE_ARN`. (Use `fullmatch`. This rejects other partitions, users, `root`, and anything with spaces.)
3. The ARN's `account` group equals the account ID → else `ROLE_ACCOUNT_MISMATCH`. This keeps the provenance string `aws_*:{account_id}` truthful.
4. Regions: split `regions_raw` on commas and whitespace, lower-case, drop empties, de-duplicate keeping first-seen order. Empty → `REGIONS_REQUIRED`; more than `MAX_REGIONS = 4` → `TOO_MANY_REGIONS`; any region not in `SUPPORTED_REGIONS` → `UNKNOWN_REGION.format(region=<first bad one>)`.

`SUPPORTED_REGIONS: frozenset[str]` is computed **once at import** as the intersection of `boto3.session.Session().get_available_regions(s)` for `s in ("config", "securityhub", "sts")` (offline, from botocore's bundled endpoint data; 34 regions with the pinned version).

The engagement lookup (`AwsEngagementNotFound`, 404) and `is_configured()` come **before** step 1. **The form has no external-ID, access-key, secret-key, session-token or profile field**, and the route ignores any such posted field (scenario 4).

### D-P4-1-F. The STS flow (exact)

After validation:

1. `pull_id = _new_pull_id()` (`uuid.uuid4().hex`, 32 chars), `started_at = _now()` (`datetime.now(timezone.utc)`), `deadline = _monotonic() + PULL_DEADLINE_SECONDS` (`time.monotonic`; `PULL_DEADLINE_SECONDS = 600`). `_new_pull_id`, `_now` and `_monotonic` are module-level functions so tests can patch them.
2. `sts = _sts_client(regions[0])`: `boto3.session.Session().client("sts", region_name=region, config=BOTO_CONFIG)`. The default credential chain, the regional STS endpoint of the first listed region, **no explicit keys**.
3. **External-ID enforcement probe.** `_call(sts, "sts", "AssumeRole", RoleArn=role_arn, RoleSessionName=f"evidence-probe-{pull_id}", DurationSeconds=900, Policy=<session policy>)`, **without `ExternalId`**.
   - `ClientError` with code `AccessDenied` → **expected**; continue.
   - **Success → refuse.** The returned credentials are dropped unused (never passed to `_service_client`) and the pull fails with `TRUST_POLICY_MISSING_EXTERNAL_ID` (step `trust_policy_check`). A role that can be assumed without this engagement's external ID is exactly the confused-deputy hole D-P4-1-D closes, so CyberAssess won't use it.
   - Any other error → mapped by D-P4-1-J, pull fails.
4. **The real call.** `_call(sts, "sts", "AssumeRole", RoleArn=role_arn, RoleSessionName=f"evidence-pull-{pull_id}", DurationSeconds=900, ExternalId=external_id(engagement.id), Policy=<session policy>)`.
   - `<session policy>` is `json.dumps(permissions_policy(account_id), separators=(",", ":"), sort_keys=True)` (identical in both calls). **Even if the client over-grants the role (say `AdministratorAccess`), the session can only do what D-P4-1-B allows**, since AWS intersects the session policy with the role's policies.
   - `DurationSeconds=900` is STS's minimum. The deadline (600 s) ends every pull well before the session expires.
   - Both session names fit `[\w+=,.@-]{2,64}` (46 and 47 chars) and show up in the client's CloudTrail, so the audit event's `pull_id` correlates with the client's logs.
5. **Assumed-account check.** `response["AssumedRoleUser"]["Arn"]` has the form `arn:aws:sts::<account>:assumed-role/…`; its account (the fifth `:`-separated field) must equal `account_id` → else `ASSUMED_ACCOUNT_MISMATCH` (step `assume_role`).
6. `credentials = TemporaryCredentials(access_key_id=c["AccessKeyId"], secret_access_key=c["SecretAccessKey"], session_token=c["SessionToken"], expiration=c["Expiration"])` from `response["Credentials"]`.

```python
BOTO_CONFIG = botocore.config.Config(connect_timeout=5, read_timeout=30, retries={"max_attempts": 5, "mode": "standard"})

@dataclass(frozen=True)
class TemporaryCredentials:
    access_key_id: str = field(repr=False)
    secret_access_key: str = field(repr=False)
    session_token: str = field(repr=False)
    expiration: datetime
```

`_service_client(credentials, service, region)`: `boto3.session.Session(aws_access_key_id=credentials.access_key_id, aws_secret_access_key=credentials.secret_access_key, aws_session_token=credentials.session_token, region_name=region).client(service, config=BOTO_CONFIG)`. **This function and `TemporaryCredentials` are the only places the three credential values appear.** The credentials object is a local variable of `pull_aws_evidence`; it is never stored on a module global, a cache, the DB session, a template context, an exception or a log record.

### D-P4-1-G. What is pulled (exact calls, filters, ordering and caps)

For each region in input order, in this order: Config, then Security Hub. `_check_deadline()` runs **before every AWS call** (including the two STS calls) and raises `DEADLINE_EXCEEDED` (step `deadline`) when `_monotonic() > deadline`.

**Config** (`client = _service_client(credentials, "config", region)`):
1. `DescribeConfigRules`: first call with no parameters, then `NextToken=<token>` while the response has a non-empty `NextToken`, at most `MAX_DESCRIBE_RULE_PAGES = 40` calls. Keep rules with `ConfigRuleState == "ACTIVE"` ("active Config rule evaluations", D10). Sort by `ConfigRuleName`. If more than `MAX_CONFIG_RULES_PER_REGION = 300` are active, or a 41st page would be needed, keep the first 300 by name and set the **source-level** `truncated = True`.
2. For each kept rule, `GetComplianceDetailsByConfigRule(ConfigRuleName=<name>, ComplianceTypes=["COMPLIANT", "NON_COMPLIANT"], Limit=100)`, then with `NextToken` added, until there's no `NextToken` or `MAX_EVALUATIONS_PER_RULE = 500` results have been read. If a `NextToken` remains at 500, or more than 500 came back, keep the first 500 and set that rule document's `truncated = True`. ("compliant/non-compliant per resource", D10. `NOT_APPLICABLE` and `INSUFFICIENT_DATA` are deliberately not requested.)
3. `NoSuchConfigRuleException` on a rule (deleted between the two calls) → skip that rule, increment the source's `skipped_rules`; not an error.

**Security Hub** (`client = _service_client(credentials, "securityhub", region)`):
1. `GetFindings(Filters=FINDING_FILTERS, MaxResults=100)`, then with `NextToken`, until there's no `NextToken` or `MAX_FINDINGS_PER_REGION = 2000` findings have been read (region-level `truncated = True` if a token remains at 2000 or more came back; keep the first 2000). No `SortCriteria`.
   ```python
   FINDING_FILTERS = {  # built per call with the real account and region
       "AwsAccountId": [{"Value": account_id, "Comparison": "EQUALS"}],
       "Region": [{"Value": region, "Comparison": "EQUALS"}],
       "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
   }
   ```
   `AwsAccountId` stops an administrator account's hub from returning member accounts' findings. `Region` stops a finding aggregator from returning linked regions' findings twice. `RecordState=ACTIVE` excludes archived findings.
2. `InvalidAccessException` (Security Hub not enabled in that region) on the first call → the source summary gets `status = "not_enabled"` and 0 items; **not an error**. On a later page it's an error (step `securityhub`).
3. Group findings by `GeneratorId` (a required ASFF field); groups sorted by `GeneratorId`, findings in each group sorted by `Id`.

These caps bound one pull to about 4 × (40 + 300 × 5 + 20) ≈ 6,240 calls in the worst case, and the 600 s deadline bounds it in time. Typical accounts are far smaller.

### D-P4-1-H. Evidence granularity, identity, and data mapping

**One Evidence per (source, account, region, Config rule name)** and **one per (source, account, region, Security Hub `GeneratorId`)**. Not one per resource evaluation or per finding: a Security Hub account commonly has thousands of active findings, each Evidence costs a blob and four audit rows, and consultants map Evidence to requirements (P2-1 `EvidenceUse`) at the control level, which is what a rule or a generator is. "Each result becomes an Evidence item" is read as "each rule's result and each generator's result". Every per-resource evaluation and per-finding row is kept **inside** the item, so nothing D10 asks for is lost.

| `Evidence` field | Config rule item | Security Hub generator item |
|---|---|---|
| `engagement_id` | the engagement | the engagement |
| `assessment_id` | `None` (engagement-level, as in P2-5) | `None` |
| `uploaded_by` | `f"aws_config:{account_id}"` | `f"aws_securityhub:{account_id}"` |
| `original_filename` (the **identity key**) | `f"aws-config_{account_id}_{region}_{_slug(rule_name)}_{_short_hash(region, rule_name)}.txt"` | `f"aws-securityhub_{account_id}_{region}_{_slug(generator_id)}_{_short_hash(region, generator_id)}.txt"` |
| `document_category` | `None` | `None` |
| `mime_type` | `text/plain` (from `file_type="txt"`) | `text/plain` |
| `status` | `active` after release | `active` after release |

- `_slug(value) = re.sub(r"[^A-Za-z0-9._-]", "_", value)[:100]`; `_short_hash(region, key) = sha256(f"{region}\n{key}".encode("utf-8")).hexdigest()[:8]`. The hash makes two keys that slug identically still differ. The filename is at most 196 characters, below `_display_filename`'s 255 cap, and has no `/` or `\`, so it survives `_display_filename` unchanged.
- **`EvidenceVersion.extracted_text` = the blob's text**, so it can be read, cited (P2-2 citations work on `extracted_text`) and analysed once mapped.
- **Engagement-level, not assessment-level:** an AWS account's state isn't bound to one assessment, and putting every rule into an assessment's analysis automatically would flood the analysis input. The consultant maps the items they need with the existing P2-1 mapping (`map_evidence`), exactly as for magic-link uploads. No new mapping UI (open question 4).

**Blob content** is `canonical_json(doc) = json.dumps(doc, sort_keys=True, indent=2, ensure_ascii=False) + "\n"`, encoded UTF-8. All `datetime` values become ISO 8601 UTC strings via `_iso(dt)` (`dt.astimezone(timezone.utc).isoformat()`, `None` stays `None`). **The pull time is not in the document**, so the same AWS state gives the same bytes and hash (the time lives on `EvidenceVersion.created_at` and in the audit event). Exact documents:

```jsonc
// Config rule item
{
  "schema": "aws_config_rule_evaluations/v1",
  "source": "aws_config",
  "account_id": "111122223333",
  "region": "eu-west-1",
  "rule": {
    "name": ConfigRuleName, "arn": ConfigRuleArn, "id": ConfigRuleId,
    "description": Description or null, "state": ConfigRuleState,
    "source_owner": Source.Owner or null, "source_identifier": Source.SourceIdentifier or null
  },
  "compliance_types_requested": ["COMPLIANT", "NON_COMPLIANT"],
  "summary": {"compliant": <int>, "non_compliant": <int>, "total": <int>},
  "truncated": <bool>,
  "evaluations": [   // sorted by (resource_type, resource_id, evaluation_mode or "")
    {"resource_type": Qualifier.ResourceType, "resource_id": Qualifier.ResourceId,
     "evaluation_mode": Qualifier.EvaluationMode or null, "compliance_type": ComplianceType,
     "result_recorded_time": iso, "config_rule_invoked_time": iso, "annotation": Annotation or null}
  ]
}

// Security Hub generator item
{
  "schema": "aws_securityhub_findings/v1",
  "source": "aws_securityhub",
  "account_id": "111122223333",
  "region": "eu-west-1",
  "generator_id": GeneratorId,
  "filters": {"aws_account_id": "111122223333", "region": "eu-west-1", "record_state": "ACTIVE"},
  "summary": {
    "by_severity": {"CRITICAL": n, "HIGH": n, "MEDIUM": n, "LOW": n, "INFORMATIONAL": n, "UNKNOWN": n},
    "by_compliance_status": {"PASSED": n, "FAILED": n, "WARNING": n, "NOT_AVAILABLE": n, "NONE": n},
    "total": n
  },
  "truncated": <bool>,   // the region-level Security Hub truncation flag
  "findings": [   // sorted by id
    {"id": Id, "title": Title, "severity_label": Severity.Label or null,
     "compliance_status": Compliance.Status or null, "workflow_status": Workflow.Status or null,
     "product_name": ProductName or null,
     "resources": [{"type": r.Type, "id": r.Id} for r in Resources],   // in API order
     "first_observed_at": FirstObservedAt or null, "last_observed_at": LastObservedAt or null,
     "updated_at": UpdatedAt}
  ]
}
```

- Summary keys are **always all present** (zeros included). A missing `Severity.Label` counts as `UNKNOWN`; a missing `Compliance.Status` counts as `NONE`; any other unexpected label also counts under `UNKNOWN`/`NONE`. ASFF timestamps are already ISO strings; pass them through unchanged.
- **Deliberately excluded (data minimisation):** `ResultToken`, `InputParameters`, `Scope`, `OrderingTimestamp`, `ResourceEvaluationId`, finding `Description`, `Remediation`, `ProductFields`, `Resources[].Details`, `Network`, `Process`, `Malware`, `UserDefinedFields`, and everything else not listed. Finding details can carry client secrets and personal data; the listed fields are enough to show a control's state per resource with severity.

### D-P4-1-I. Writing: all-or-nothing, a new version only when the data changed

All AWS reads finish **before** the first DB write. Then, in one transaction, for each document in order (regions in input order; per region Config items by rule name, then Security Hub items by generator id):

```text
content = canonical_json(doc).encode("utf-8"); digest = sha256_hex(content)
existing = first Evidence where engagement_id == E, uploaded_by == provenance, original_filename == filename,
           status in ("active", "invalidated"), ordered by (created_at, id)
if existing is None:
    evidence, version = evidence_service.receive_evidence(db, engagement_id=E, assessment_id=None, filename=filename,
        content=content, category=None, uploaded_by=provenance, actor=provenance, file_type="txt",
        change_reason=f"AWS pull {pull_id}: first collection")                           -> "created"
elif current_version(existing).file_hash_sha256 == digest:
    nothing is written                                                                 -> "unchanged"
else:
    version = evidence_service.receive_version(db, evidence_id=existing.id, filename=filename, content=content,
        change_reason=f"AWS pull {pull_id}: AWS data changed", actor=provenance, file_type="txt")  -> "versioned"
then (created/versioned): released = evidence_service.release_from_quarantine(db, version_id=version.id)
    if released.status == "active": released.extracted_text = content.decode("utf-8")
    else: count it as "rejected" (the placeholder scan never rejects today)
```

- **The one change to `app/services/evidence.py`:** `receive_version` gains a keyword-only `file_type: str | None = None` after `actor`, and its `_file_type(filename, None)` becomes `_file_type(filename, file_type)`. That exactly mirrors `receive_evidence`; `None` keeps today's behaviour for every existing caller. **Nothing else in that file changes.** Without this, text blobs can't be versioned (Current state).
- `release_from_quarantine` is called with its default `actor=SCAN_ACTOR`, as every other intake path does.
- `allow_duplicate` stays `False`. Every document contains its account, region and rule/generator key, so two different keys can't produce equal bytes. A `DuplicateEvidence` therefore means a real conflict (such as a concurrent pull) and fails the pull.
- **Archived, rejected or quarantined** Evidence with the same key is ignored, and a new Evidence is created. An archived item stays archived: the consultant's archive decision isn't reversed by a pull.
- **Rules or generators that disappear** from AWS leave their Evidence untouched. Nothing is archived automatically (open question 5).
- **One commit.** After every document, add the `aws_evidence.pull_completed` audit event (D-P4-1-K), then `db.commit()` exactly once.
- **Failure during the write phase** (any exception, including `EvidenceError`): `db.rollback()`; unlink **every blob path written in this pull** (track `evidence_service.blob_path(version.storage_path)` for each created/versioned version as soon as it's returned, and `unlink(missing_ok=True)` each); then record `aws_evidence.pull_failed` with step `write` in a new transaction and commit it; raise `AwsPullFailed(WRITE_FAILED)`. (`receive_evidence`/`receive_version` already roll back and unlink their own blob when they fail; the orchestrator covers the blobs of the items before it.)
- **Failure before the write phase** (validation excepted): nothing has been added to the session. Record `aws_evidence.pull_failed`, commit it, raise `AwsPullFailed(<message>)`.
- `pull_aws_evidence` **never calls `extract_text`** and **never touches an assessment's status**.

### D-P4-1-J. Error mapping (exact; every message ends the pull with nothing collected)

The mapping lives in one function, `_map_error(exc, *, step: str, region: str | None, operation: str | None) -> AwsPullFailed`. Codes are read from `exc.response["Error"]["Code"]`. **AWS error messages are never shown, logged or stored**: only the code, the step and the region are. Checked in this order:

| Condition | Message constant |
|---|---|
| `NoCredentialsError`, `PartialCredentialsError`, `CredentialRetrievalError`, `TokenRetrievalError`, `SSOError` (any step); or `ClientError` code in `{"InvalidClientTokenId", "ExpiredToken", "ExpiredTokenException", "SignatureDoesNotMatch", "UnrecognizedClientException"}` **at step `assume_role` or `trust_policy_check`** | `BASE_CREDENTIALS_UNAVAILABLE` |
| `EndpointConnectionError`, `ConnectTimeoutError`, `ReadTimeoutError`, `ConnectionClosedError` | `AWS_UNREACHABLE` |
| step `assume_role`, code `AccessDenied` | `ASSUME_ROLE_DENIED` |
| code `RegionDisabledException` (STS) | `STS_REGION_DISABLED.format(region=regions[0])` |
| step `config`/`securityhub`, code in `{"ExpiredToken", "ExpiredTokenException"}` | `SESSION_EXPIRED` |
| step `config`/`securityhub`, code in `{"UnrecognizedClientException", "InvalidClientTokenId", "AuthFailure"}` | `REGION_NOT_ENABLED.format(region=region)` |
| step `config`/`securityhub`, code in `{"AccessDeniedException", "AccessDenied", "UnauthorizedOperation"}` | `PERMISSION_MISSING.format(action=f"{service}:{operation}", region=region)` |
| any other `ClientError` | `AWS_ERROR.format(code=code, step=step)` |
| any other `BotoCoreError` | `AWS_ERROR.format(code=type(exc).__name__, step=step)` |

`ASSUMED_ACCOUNT_MISMATCH`, `TRUST_POLICY_MISSING_EXTERNAL_ID` and `DEADLINE_EXCEEDED` are raised directly, not through `_map_error`. Throttling is left to botocore's `standard` retry mode (5 attempts) and, if still failing, falls into the `AWS_ERROR` row. **Steps (exact strings):** `trust_policy_check`, `assume_role`, `config`, `securityhub`, `deadline`, `write`. One region's failure fails the whole pull, including regions already read (a partial pull could be mistaken for a complete one). The only non-error outcomes are `not_enabled` Security Hub and skipped deleted rules (D-P4-1-G).

**Messages (exact; tests compare them):**

```python
NOT_CONFIGURED = ("AWS evidence collection is not configured. Set AWS_EXTERNAL_ID_SECRET in .env to a random value of "
                  "at least 32 characters that differs from SESSION_SECRET, then restart.")
INVALID_ACCOUNT_ID = "Enter the client's 12-digit AWS account ID."
INVALID_ROLE_ARN = "Enter the role ARN in the form arn:aws:iam::<account-id>:role/<role-name>."
ROLE_ACCOUNT_MISMATCH = "The role ARN must belong to the AWS account ID entered."
REGIONS_REQUIRED = "Enter at least one AWS region."
TOO_MANY_REGIONS = "Pull at most 4 regions at a time."
UNKNOWN_REGION = "Unknown or unsupported AWS region: {region}."
BASE_CREDENTIALS_UNAVAILABLE = ("This machine has no usable AWS credentials for the consultant identity. "
                                "Sign in (for example with aws sso login) and try again. Nothing was collected.")
ASSUME_ROLE_DENIED = ("Could not assume the role. Check the role ARN, that its trust policy names your consultant "
                      "principal, and that it requires this engagement's external ID. Nothing was collected.")
TRUST_POLICY_MISSING_EXTERNAL_ID = ("The role can be assumed without this engagement's external ID. Add the "
                                    "sts:ExternalId condition shown on this page to the role's trust policy, then try "
                                    "again. Nothing was collected.")
ASSUMED_ACCOUNT_MISMATCH = "The assumed role belongs to a different AWS account than the one entered. Nothing was collected."
STS_REGION_DISABLED = "AWS STS is not activated in {region}. List an activated region first. Nothing was collected."
REGION_NOT_ENABLED = "The temporary session is not valid in {region}; the region may not be enabled for this account. Nothing was collected."
PERMISSION_MISSING = ("The role is missing permission {action} in {region}. Apply the read-only permissions policy "
                      "shown on this page. Nothing was collected.")
SESSION_EXPIRED = "The temporary AWS session expired before the pull finished. Pull fewer regions. Nothing was collected."
DEADLINE_EXCEEDED = "The pull took longer than 10 minutes and was stopped. Pull fewer regions. Nothing was collected."
AWS_UNREACHABLE = "Could not reach AWS. Check the network connection and try again. Nothing was collected."
AWS_ERROR = "AWS returned an error ({code}) during {step}. Nothing was collected."
WRITE_FAILED = "The AWS data was retrieved but could not be saved as evidence. Nothing was collected."
ORIGIN_REJECTED = "Cross-site requests cannot start an AWS pull."
```

**Exceptions:** `AwsEvidenceError(Exception)` with `status_code` and `message` (the `EvidenceError` shape); `AwsEngagementNotFound` (404, message `"Engagement not found"`), `AwsNotConfigured` (400), `AwsValidationError` (400), `AwsPullFailed` (400, plus attributes `step: str` and `error_code: str | None`).

### D-P4-1-K. Audit events and the pull summary

**Success**, one row: `actor="consultant"` (`evidence_service.CONSULTANT_ACTOR`), `action="aws_evidence.pull_completed"`, `entity_type="engagement"`, `entity_id=engagement.id`, `metadata_json=json.dumps(meta, sort_keys=True)` with **exactly** these keys:
`pull_id, account_id, role_arn, regions (list), role_session_name, external_id_version ("v1"), started_at (iso), finished_at (iso), sources (list of SourceSummary dicts, in pull order), evidence_ids (list: created and versioned Evidence ids, in write order)`.

**Failure**, one row: same actor/entity, `action="aws_evidence.pull_failed"`, metadata keys **exactly** `pull_id, account_id, role_arn, regions, step, error_code (str or null), message, started_at, failed_at`.

**Neither contains** the external ID, any credential value, an AWS error message, or AWS response data. Validation failures (D-P4-1-E), `AwsNotConfigured` and `AwsEngagementNotFound` write **no** audit row (nothing was attempted). The per-item `evidence.created` / `evidence_version.created` / status events come from the evidence service unchanged, with `actor = uploaded_by = provenance`.

```python
@dataclass(frozen=True)
class SourceSummary:
    source: str            # "aws_config" | "aws_securityhub"
    region: str
    status: str            # "collected" | "not_enabled"
    items: int             # documents built for this source/region
    created: int
    versioned: int
    unchanged: int
    rejected: int
    truncated: bool        # source-level: Config rules capped / Security Hub findings capped
    skipped_rules: int     # Config only; 0 for Security Hub

@dataclass(frozen=True)
class PullResult:
    pull_id: str
    account_id: str
    regions: tuple[str, ...]
    sources: tuple[SourceSummary, ...]   # per region: Config then Security Hub
    evidence_ids: tuple[str, ...]
    started_at: datetime
    finished_at: datetime
```

`SourceSummary` is serialised into the audit metadata with `dataclasses.asdict`.

### D-P4-1-L. Routes, templates, and the one request-forgery guard

New module **`app/routers/aws.py`** (not `aws_evidence.py`, so it doesn't share a name with the service), modelled on `app/routers/magic.py`: `router = APIRouter(include_in_schema=False)`, `from app.routers.web import templates`, `from app.services import aws_evidence`, and `_HEADERS = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}` on every response.

| Method + path | Handler | Response |
|---|---|---|
| `GET /engagements/{engagement_id}/aws-evidence` | `aws_evidence_page` | `pages/aws_evidence.html`, 200 (404 `HTTPException("Engagement not found")` / `("Client not found")`) |
| `POST /engagements/{engagement_id}/aws-evidence/pull` | `aws_evidence_pull` | `partials/aws_evidence_panel.html`, 200 on success **and** on handled errors (the magic-link consultant convention, so HTMX swaps it), 404 for an unknown engagement, 403 for a rejected origin |

- **Both handlers are plain `def`, not `async def`.** boto3 blocks, and a sync route runs in FastAPI's threadpool instead of stalling the event loop. The POST reads `account_id: str = Form("")`, `role_arn: str = Form("")`, `regions: str = Form("")` and **nothing else**.
- **Origin guard (POST only), before anything else:** if the request has an `Origin` header and `urllib.parse.urlsplit(origin).netloc != request.headers.get("host")`, return the panel with `ORIGIN_REJECTED` and status 403, with no DB read beyond the engagement lookup and no AWS call. The app has no auth and a wildcard CORS policy that reflects any origin, so any web page the consultant visits could otherwise post to this route and make their machine assume a role the attacker names. A missing `Origin` (curl, tests) is allowed. The app-wide CSRF question is open question 6; this guard covers only the route that uses the consultant's cloud credentials.
- The POST calls `aws_evidence.pull_aws_evidence(db, engagement_id=…, account_id=…, role_arn=…, regions_raw=…)`, catches `AwsEvidenceError` (the service has already committed or written nothing, so the router **never commits or rolls back**, except `AwsEngagementNotFound` → 404), and renders the panel with either `result` or `error`, and the submitted values refilled.

**`pages/aws_evidence.html`** (extends `base.html`; context `engagement`, `client`, `configured`, `external_id` (or `None`), `trust_policy_json`, `permissions_policy_json`, `consultant_policy_json`, `panel` context):
- `{% block title %}AWS evidence — {{ engagement.name }}{% endblock %}`; breadcrumb `Portfolio / {{ client.name }} / {{ engagement.name }} / AWS evidence` (links like `remediation_tracker.html`).
- `<h1>` "AWS evidence"; subtitle "Read-only pull of AWS Config rule evaluations and Security Hub findings into this engagement's evidence. Runs only when you press the button."
- When not `configured`: `<div data-aws-not-configured>` with `NOT_CONFIGURED`, and **no** form, external ID or policy blocks.
- When `configured`, three sections:
  1. "Client setup": `<input data-external-id readonly value="{{ external_id }}">` labelled "External ID for this engagement"; the suggested role name; `<pre data-trust-policy>{{ trust_policy_json }}</pre>` with the note "Replace the principal with your own consultant role ARN. Never use an account root principal."; `<pre data-permissions-policy>{{ permissions_policy_json }}</pre>` with the note "Attach only this inline policy to the role."; `<pre data-consultant-policy>{{ consultant_policy_json }}</pre>` with the note "Your own identity needs this to assume client roles."
  2. The panel include.
- The policies are rendered with the **prefill** account ID (D-P4-1-M) or, if none, `111122223333` with the note "Example account ID shown; the policy uses the account you pull." `*_json` strings are `json.dumps(policy, indent=2)` from `aws_evidence`; the template never builds a policy itself.

**`partials/aws_evidence_panel.html`** (`<section id="aws-evidence-panel">`; context `engagement_id`, `configured`, `form_values` (`account_id`, `role_arn`, `regions`), `error`, `result`, `rows`):
- When `configured`: `<form data-aws-pull-form hx-post="/engagements/{{ engagement_id }}/aws-evidence/pull" hx-target="#aws-evidence-panel" hx-swap="outerHTML">` with text inputs `account_id`, `role_arn`, `regions` (placeholder "eu-west-1, us-east-1"), refilled from `form_values`, and submit "Pull AWS evidence". **No other inputs.**
- `error` → `<div data-aws-error>{{ error }}</div>`.
- `result` → `<div data-aws-result>`: "Pull complete", the pull id, then per source `<tr data-aws-source-row>` with source label (`AWS Config` / `Security Hub`), region, status label (`Collected` / `Not enabled`), items, created, versioned, unchanged, and "Truncated" when `truncated`.
- The collected-evidence table: `<tr data-aws-evidence-row>` per `rows` entry (filename linked to `/evidence/{{ row.id }}`, source label, status, `v{{ row.current_version_number }}` or "—", version count, last collected `%Y-%m-%d %H:%M` UTC), or "No AWS evidence collected yet."
- Everything autoescaped. **No `|safe`, no `CyberAssess`, no `overall_score`.**

**Link** in `pages/engagement_detail.html`, on the line directly after the "Remediation tracker →" link: `<a href="/engagements/{{ engagement.id }}/aws-evidence" class="mt-2 ml-4 inline-block text-sm font-medium text-brand dark:text-navy-300 hover:underline">AWS evidence →</a>`.

**Registration** in `app/main.py`: add `aws,` to the router import block (alphabetically, first), and `app.include_router(aws.router)` under `# Web portal routes`, **before** `app.include_router(magic.router)`. Nothing else in `main.py` changes.

### D-P4-1-M. Read models for the page

In `app/services/aws_evidence.py`:
- `aws_evidence_rows(db, engagement_id) -> list[dict]`: every Evidence of the engagement with `uploaded_by` LIKE `aws_config:%` or `aws_securityhub:%`, **any status**, ordered by `original_filename, created_at, id`. Keys exactly `id, filename, source ("aws_config" | "aws_securityhub"), account_id, status, current_version_number (int or None), version_count, last_collected_at (the newest version's created_at)`. Two queries at most (Evidence, then their versions).
- `last_pull_inputs(db, engagement_id) -> dict | None`: from the newest `aws_evidence.pull_completed` audit event for the engagement (`created_at` desc, `id` desc), `{"account_id", "role_arn", "regions": ", ".join(regions)}`; `None` if there is none or its metadata is unreadable. It prefills the form and the policy account on `GET`. No new storage.
- `page_context(db, engagement) -> dict` builds the page context in D-P4-1-L (the router adds `request`, `engagement`, `client`).

### D-P4-1-N. Credential and secret hygiene (the checkable rules)

1. **No credential input.** No form field, setting, env var read, or function parameter accepts an access key, secret key, session token or profile name. `Settings` gains only `aws_external_id_secret`.
2. **No persistence.** No credential value or external ID reaches the DB, an audit row, an evidence blob, a template context (except the external ID on the page), a log record, or an exception message.
3. **No logging of AWS data.** The module logs at most one `logger.info` per pull (`"AWS evidence pull %s completed: %d created, %d versioned, %d unchanged"`) and one `logger.warning` per failure (`"AWS evidence pull %s failed at %s (%s)"` with pull id, step and error code). Never session credentials, the external ID, AWS error messages or response bodies.
4. **Only `_service_client` and `TemporaryCredentials`** name `aws_access_key_id`/`aws_secret_access_key`/`aws_session_token`/`SecretAccessKey`/`SessionToken`, plus the one line in `pull_aws_evidence` that builds `TemporaryCredentials` from the response.
5. **No `boto3.client(` or `boto3.resource(` calls**: only `boto3.session.Session(...)` in `_sts_client` and `_service_client`. No module-level client or session cache.

### D-P4-1-O. Test doubles: `botocore.stub.Stubber`, not `moto`

**Decision: `botocore.stub.Stubber`**, with the module's two client factories monkeypatched.
- Stubber ships with the pinned botocore, so there is **no new dependency** (and Codex can't install one; Step 0).
- It validates every call's parameters against the **real service model** and raises on any operation that wasn't stubbed. That checks the exact `expected_params` of every call, including the exact `Policy`, `ExternalId`, `Filters` and `ComplianceTypes`, which is what this security boundary needs. `moto` would instead emulate AWS behaviour (and moto's Config/Security Hub coverage is partial), which proves less about the calls CyberAssess makes.
- Tests build real clients with dummy keys, `boto3.session.Session(aws_access_key_id="AKIATESTTESTTESTTEST", aws_secret_access_key="test-base-secret", region_name=r).client(service)`, wrap them in `Stubber`, `activate()`, and after each test `assert_no_pending_responses()`. Non-`ClientError` botocore exceptions (`NoCredentialsError`, `EndpointConnectionError`) come from a tiny fake client whose method raises, since Stubber only produces service errors.

### D-P4-1-P. Documentation: `docs/operations/aws-evidence.md` (new)

Sections, in order: "What this does" (the Goal, in five sentences); "Client setup" (create role `ComplianceEvidenceReadOnly`, the trust policy as a fenced `json` block rendered from `trust_policy("<EXTERNAL_ID_FROM_THE_ENGAGEMENT_PAGE>", CONSULTANT_PRINCIPAL_PLACEHOLDER)`, the permissions policy as a fenced `json` block rendered from `permissions_policy("111122223333")`); "Consultant setup" (`AWS_EXTERNAL_ID_SECRET`, SSO credentials recommended and long-lived keys discouraged, the fenced `json` from `consultant_policy()`); "Why each permission" (a three-row table: action, what it reads, why `DescribeConfigRules` must be `"*"`); "What is collected and what is not" (D10, the excluded fields list from D-P4-1-H, no resource inventory, no write, no schedule); "Rotating the external ID secret"; "Troubleshooting" (one line per message constant in D-P4-1-J). Each fenced JSON block is `json.dumps(..., indent=2)` output exactly, so scenario 3 can parse the three blocks and compare them to the functions. **Don't write "CyberAssess" in the policy JSON**; prose may use it.

### D-P4-1-Q. Shared-file coordination with P4-2, P4-3 and P4-4 (pre-declared)

The plan says the four Phase 4 tasks don't overlap, but these files may be edited by more than one branch:

| File | P4-1's edit | Rule if another Phase 4 branch also edits it |
|---|---|---|
| `app/main.py` | `aws,` in the import block; `app.include_router(aws.router)` before `magic.router` | **Keep both sides.** Keep every router import and every `include_router` line from both branches; keep the import block alphabetical; don't reorder existing lines. |
| `app/templates/pages/engagement_detail.html` | one `AWS evidence →` link after "Remediation tracker →" | **Keep both links**, each on its own line, P4-1's directly after "Remediation tracker →". |
| `app/services/evidence.py` | one keyword-only parameter on `receive_version` (D-P4-1-I) | **Keep both.** P4-4 (purge) is likely to add functions here; P4-1 changes only that signature line and the one `_file_type` call. If P4-4 changed `receive_version` too, stop and report. |
| `app/config.py`, `.env.example` | one setting / two comment lines, after the white-label block | Keep both sides; P4-1's lines go after any lines already there. |
| `requirements.txt` | `boto3==1.43.101` appended as the last line | Keep both sides; one package per line. |
| `tasks/todo.md` | the P4-1 line only | Keep both sides; touch only your own task's line. |

No Alembic revision is added by this task, so there can be no head conflict from P4-1.

### D-P4-1-R. Consistency audit of this spec (the P2-4 lesson, done in advance)

1. **White label.** No mandated template string contains `CyberAssess`. The suggested role name is `ComplianceEvidenceReadOnly`, the session names are `evidence-probe-…`/`evidence-pull-…`, the HMAC label is `evidence-external-id:v1:…`. `tests/test_white_label.py` greps only `app/templates/` and three export utils, so the service and doc may say "CyberAssess"; the templates may not.
2. **No `overall_score`** anywhere in the new templates.
3. **Existing evidence tests.** `receive_version`'s new parameter defaults to `None`, so `tests/test_evidence_service.py`, `tests/test_magic_links.py`, `tests/test_remediation_tracking.py` and `tests/test_report_snapshots.py` are unaffected. `evidence_panel_rows`, `client_upload_rows` and `active_versions_in_scope` are unchanged. AWS items don't appear on any assessment's evidence panel until mapped, and never in `client_upload_rows` (its filter is `client_link:%`).
4. **Config warnings.** `aws_external_id_secret` adds no validator and no warning, so `tests/test_config_security_warnings.py::test_settings_do_not_warn_for_custom_credentials` still sees no records.
5. **Route sets.** The two new paths contain `/aws-evidence` and none of `/findings`, `/conclusions`, `/workpaper`, `/snapshots`, `/remediation`, `/integrated-reports`, `/magic-links`, so no existing route-set assertion changes. This task pins its own set (scenario 11).
6. **Counted attributes.** None of `data-aws-not-configured`, `data-external-id`, `data-trust-policy`, `data-permissions-policy`, `data-consultant-policy`, `data-aws-pull-form`, `data-aws-error`, `data-aws-result`, `data-aws-source-row` and `data-aws-evidence-row` is a substring of another (checked), so `text.count("data-aws-source-row")` and `text.count("data-aws-evidence-row")` are exact.
7. **HTML escaping.** The policy JSON renders inside `<pre>` with autoescape, so `"` becomes `&#34;`. Tests compare page text after `html.unescape`.
8. **The service commits.** Unlike P3-1's "never commits" services, `pull_aws_evidence` commits (as `evidence_service.ingest_upload` does). No structural guard in the suite forbids `.commit(` in a new module.

## Required approach

1. **Step 0 check** (above). Stop if boto3 isn't importable at `1.43.101`.
2. **`requirements.txt`:** append `boto3==1.43.101`.
3. **`app/config.py`, `.env.example`:** D-P4-1-D.
4. **`app/services/evidence.py`:** the one `receive_version` change (D-P4-1-I).
5. **`app/services/aws_evidence.py` (new).** Docstring: `"""AWS evidence adapter (P4-1): a consultant-triggered, read-only pull of AWS Config rule evaluations and Security Hub findings into versioned engagement Evidence, via AssumeRole with an engagement-bound external ID and a least-privilege session policy. Holds no credentials beyond the request."""` Public API, exact:
   ```python
   AWS_OPERATIONS; SUPPORTED_REGIONS; MAX_REGIONS = 4; MAX_DESCRIBE_RULE_PAGES = 40; MAX_CONFIG_RULES_PER_REGION = 300
   MAX_EVALUATIONS_PER_RULE = 500; MAX_FINDINGS_PER_REGION = 2000; PULL_DEADLINE_SECONDS = 600; SESSION_DURATION_SECONDS = 900
   EXTERNAL_ID_VERSION = "v1"; MIN_EXTERNAL_ID_SECRET_CHARS = 32; ROLE_ARN_RE; BOTO_CONFIG
   CONFIG_PROVENANCE_PREFIX = "aws_config:"; SECURITYHUB_PROVENANCE_PREFIX = "aws_securityhub:"
   SUGGESTED_ROLE_NAME; CONSULTANT_PRINCIPAL_PLACEHOLDER; EXAMPLE_ACCOUNT_ID = "111122223333"
   STEPS = ("trust_policy_check", "assume_role", "config", "securityhub", "deadline", "write")
   # messages: D-P4-1-J
   class AwsEvidenceError(Exception); class AwsEngagementNotFound; class AwsNotConfigured
   class AwsValidationError; class AwsPullFailed          # D-P4-1-J
   @dataclass TemporaryCredentials; SourceSummary; PullResult   # D-P4-1-F, K

   def is_configured() -> bool
   def external_id(engagement_id: str) -> str
   def permissions_policy(account_id: str) -> dict
   def trust_policy(external_id: str, consultant_principal_arn: str = CONSULTANT_PRINCIPAL_PLACEHOLDER) -> dict
   def consultant_policy() -> dict
   def session_policy_json(account_id: str) -> str
   def canonical_json(doc: dict) -> str
   def config_rule_document(*, account_id: str, region: str, rule: dict, evaluations: list[dict], truncated: bool) -> dict
   def securityhub_documents(*, account_id: str, region: str, findings: list[dict], truncated: bool) -> list[dict]
   def evidence_filename(source: str, *, account_id: str, region: str, key: str) -> str   # source: "aws_config" | "aws_securityhub"
   def pull_aws_evidence(db: Session, *, engagement_id: str, account_id: str, role_arn: str, regions_raw: str,
                         actor: str = evidence_service.CONSULTANT_ACTOR) -> PullResult
   def aws_evidence_rows(db: Session, engagement_id: str) -> list[dict]
   def last_pull_inputs(db: Session, engagement_id: str) -> dict | None
   def page_context(db: Session, engagement: Engagement) -> dict

   # test seams (module-level, patched by tests)
   def _now() -> datetime; def _monotonic() -> float; def _new_pull_id() -> str
   def _sts_client(region: str); def _service_client(credentials: TemporaryCredentials, service: str, region: str)
   def _call(client, service: str, operation: str, **params) -> dict
   def _map_error(exc, *, step: str, region: str | None, operation: str | None) -> AwsPullFailed
   ```
   `config_rule_document` takes a raw `ConfigRule` dict and raw `EvaluationResult` dicts (boto3 response shapes); `securityhub_documents` takes raw ASFF findings and returns one document per `GeneratorId`, already sorted.
6. **`app/routers/aws.py` (new), `app/main.py`:** D-P4-1-L.
7. **Templates:** `pages/aws_evidence.html`, `partials/aws_evidence_panel.html` (new); the link in `pages/engagement_detail.html` (D-P4-1-L).
8. **`docs/operations/aws-evidence.md` (new):** D-P4-1-P. Generate its JSON blocks by running the three policy functions, not by hand.
9. **`tasks/todo.md`:** update the Phase 4 line to note P4-1's status with a link to this handoff's Results. Touch nothing else in that file.
10. **`tests/test_aws_evidence.py` (new):** `## Test scenarios`. Copy (don't import) the `db_path` / `engine` / `db` / `http` fixtures and the autouse `upload_root` fixture from `tests/test_report_snapshots.py` (**no test may write under the real `uploads/` or touch `data/dpdpa.db`**). Add:
    - an autouse fixture that sets `AWS_CONFIG_FILE` and `AWS_SHARED_CREDENTIALS_FILE` to non-existent paths under `tmp_path`, sets `AWS_EC2_METADATA_DISABLED=true`, deletes `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` and `AWS_PROFILE`, and sets `settings.aws_external_id_secret` to a fixed 40-character test value (unless a test overrides it). **No test may reach the network or a real credential.**
    - `_seed_engagement(db, name="Acme AWS")` → a `Client` + `Engagement` (hand-set rows are fine; engagement creation isn't under test).
    - `FakeAws`: builds the stubbed STS client and one stubbed client per `(service, region)`, and monkeypatches `aws_evidence._sts_client` (records the region) and `aws_evidence._service_client` (asserts the credentials equal the stubbed AssumeRole response's, records `(service, region)`). Helpers `expect_probe_denied()`, `expect_assume(account_id=…)`, `expect_rules(region, pages)`, `expect_details(region, rule_name, pages)`, `expect_findings(region, pages)`, `expect_securityhub_not_enabled(region)`, each with **exact `expected_params`**.
    - `_snapshot(db, upload_root)`: counts of `evidence`, `evidence_versions`, `evidence_uses`, `audit_events`; every Evidence `(id, status)`; every version `(id, status, file_hash_sha256)`; the sorted relative paths of files under `upload_root`.

    Fixed test values: account `111122223333`, role `arn:aws:iam::111122223333:role/ComplianceEvidenceReadOnly`, STS response credentials `AccessKeyId="ASIATESTTESTTESTTEST"`, `SecretAccessKey="test-session-secret-DO-NOT-LEAK"`, `SessionToken="test-session-token-DO-NOT-LEAK"`, `Expiration` = 15 minutes after the patched `_now`, `AssumedRoleUser={"AssumedRoleId": "AROATEST:evidence-pull-…", "Arn": "arn:aws:sts::111122223333:assumed-role/ComplianceEvidenceReadOnly/evidence-pull-…"}`. Patch `_new_pull_id` to return `"0" * 32` (and a different fixed value for a second pull).

    Every scenario is one or more test functions whose docstrings start with `Scenario N:`.

## Key files

| File | Why it matters |
|---|---|
| `app/services/aws_evidence.py` (new) | Policies, external ID, STS flow, pull, mapping, write, error mapping, read models (D-P4-1-A … N). |
| `app/routers/aws.py` (new) | Page and pull routes, origin guard (D-P4-1-L). |
| `app/templates/pages/aws_evidence.html`, `app/templates/partials/aws_evidence_panel.html` (new) | Setup instructions, pull form, results, collected list. |
| `app/templates/pages/engagement_detail.html` | One link (D-P4-1-L). |
| `app/main.py` | Router import and registration only (D-P4-1-L, Q). |
| `app/services/evidence.py` | **Only** the `receive_version(..., file_type=None)` parameter (D-P4-1-I). |
| `app/config.py`, `.env.example`, `requirements.txt` | One setting, two comment lines, one pin. |
| `docs/operations/aws-evidence.md` (new) | The documented least-privilege policy (D-P4-1-P). |
| `tests/test_aws_evidence.py` (new) | The contract. |
| `app/models/*`, `alembic/versions/*`, `app/routers/web.py`, `app/routers/magic.py`, `app/services/magic_links.py`, `app/services/document_processor.py`, `scripts/*`, every existing file under `tests/` | **Not modified.** No schema change. |

## Non-goals

- **No schema change, no Alembic revision, no new table**, and no stored AWS connection (D-P4-1-D, M).
- **No resource inventory** and no AWS operation beyond D-P4-1-A (D10).
- **No write to AWS, no scheduled or background pull, no continuous monitoring, no retry queue.** Manual trigger only (plan).
- No `moto` or any other new test dependency (D-P4-1-O).
- No automatic mapping of AWS evidence to assessments or requirements, and no new mapping UI (open question 4).
- No automatic archive of Evidence for rules/generators that disappeared (open question 5).
- No GovCloud/China partitions, no Security Hub v2 API (open question 3), no AWS Organizations-wide pull, no Config aggregators.
- No app-wide CSRF protection (open question 6). No auth.
- No change to analysis, citations, workpaper, reports or PDF.

## Test scenarios

All in `tests/test_aws_evidence.py`. "Nothing written" means `_snapshot(db, upload_root)` is unchanged. "Failed cleanly" means nothing written **except exactly one new `aws_evidence.pull_failed` audit row** with the exact metadata key set of D-P4-1-K and the expected `step` and `error_code`.

1. **The plan's test: Evidence + EvidenceVersion created with correct provenance.**
   - One region `eu-west-1`. Stubs, in order: probe `AccessDenied`; AssumeRole success with exact params (`RoleArn`, `RoleSessionName="evidence-pull-" + "0"*32`, `DurationSeconds=900`, `ExternalId=external_id(engagement.id)`, `Policy=session_policy_json("111122223333")`), and the probe's exact params (`RoleSessionName="evidence-probe-" + "0"*32`, **no `ExternalId` key**); `DescribeConfigRules` over two pages (`NextToken`) with rules `s3-bucket-public-read-prohibited` (ACTIVE), `iam-root-access-key-check` (ACTIVE) and `old-rule` (`DELETING`); `GetComplianceDetailsByConfigRule` for the two active rules only, one of them over two pages, with one `COMPLIANT` and one `NON_COMPLIANT` evaluation; `GetFindings` with exact `Filters`/`MaxResults=100` over two pages returning three findings under two `GeneratorId`s, one with no `Severity` and one with no `Compliance`.
   - `pull_aws_evidence(...)` returns a `PullResult` with two `SourceSummary` rows (`aws_config`: items 2, created 2; `aws_securityhub`: items 2, created 2), `status="collected"`, `truncated=False`.
   - Exactly four Evidence rows: `engagement_id` = the engagement, `assessment_id is None`, `status == "active"`, `uploaded_by` exactly `"aws_config:111122223333"` (2) and `"aws_securityhub:111122223333"` (2), `original_filename == evidence_filename(...)` for each key, `mime_type == "text/plain"`, `document_category is None`.
   - Each has exactly one `EvidenceVersion`: `version_number == 1`, `status == "active"`, `storage_path` ending `/v1.txt`, the blob bytes equal `canonical_json(<expected doc>).encode()`, `file_hash_sha256` equals their SHA-256, `verify_version` is `True`, and `extracted_text` equals the blob text.
   - The parsed Config documents equal hand-written expected dicts (every D-P4-1-H key; evaluations sorted; summary `compliant 1, non_compliant 1, total 2` for the two-evaluation rule; no `ResultToken`); `old-rule` has no Evidence. The Security Hub documents equal expected dicts (summary buckets all present with `UNKNOWN: 1` and `NONE: 1` where due; no `Description`).
   - Audit: per Evidence, `evidence.created` with `actor == uploaded_by`; exactly one `aws_evidence.pull_completed` with `entity_type == "engagement"`, the exact key set, `external_id_version == "v1"`, `role_session_name == "evidence-pull-" + "0"*32`, and `evidence_ids` equal to the four ids in write order (Config by rule name, then Security Hub by generator id).
   - `_sts_client` was called once with `"eu-west-1"`; `_service_client` was called for `("config", "eu-west-1")` and `("securityhub", "eu-west-1")` only; every Stubber has no pending responses.
2. **Re-pull versioning (D-P4-1-I).**
   - Repeat scenario 1's AWS data with a second pull id → every source row `unchanged == items`, no new Evidence, no new version, no new blob, one more `pull_completed` whose `evidence_ids == []`.
   - Change one evaluation's `ComplianceType` → that rule's Evidence gets v2 (`status "active"`, `change_reason` starts `"AWS pull "`), v1 becomes `superseded`, the Evidence id is unchanged, `storage_path` ends `/v2.txt`, and `versioned == 1`.
   - A new active rule → one new Evidence (`created == 1`).
   - Archive one Config Evidence with `evidence_service.transition_evidence(..., to_status="archived")`, then pull the same data → a **new** Evidence with the same filename is created, and the archived one is still `archived` with one version.
   - A rule that no longer appears → its Evidence is untouched.
3. **Least-privilege policy is exact and documented (D-P4-1-B, C, P).**
   - `permissions_policy("111122223333")` equals the D-P4-1-B literal. Its action set is `{"config:DescribeConfigRules", "config:GetComplianceDetailsByConfigRule", "securityhub:GetFindings"}`, which equals `{f"{s}:{o}" for s, o in AWS_OPERATIONS if s != "sts"}`. Every `Action` is a `str` containing no `*`; every `Effect` is `"Allow"`; no statement has `NotAction`, `NotResource` or `Condition`; exactly one statement has `Resource == "*"`, and its action is `config:DescribeConfigRules`; the other resources contain `:111122223333:`.
   - No action name starts with `Put`, `Delete`, `Create`, `Update`, `Start`, `Stop`, `Tag`, `Untag`, `Batch`, `Enable`, `Disable`, `Associate` or `Accept` after its `service:` prefix.
   - `trust_policy("x" * 64, "arn:aws:iam::444455556666:role/Consultant")` equals the D-P4-1-C literal with those values, and its condition is `StringEquals` on `sts:ExternalId`. `consultant_policy()` equals its literal.
   - `session_policy_json(a) == json.dumps(permissions_policy(a), separators=(",", ":"), sort_keys=True)`, and it is the `Policy` both AssumeRole calls received (from scenario 1's stubs).
   - `docs/operations/aws-evidence.md` exists; its fenced `json` blocks parse to exactly `trust_policy("<EXTERNAL_ID_FROM_THE_ENGAGEMENT_PAGE>", CONSULTANT_PRINCIPAL_PLACEHOLDER)`, `permissions_policy("111122223333")` and `consultant_policy()`, in that order; it mentions every message constant's first sentence under "Troubleshooting".
4. **External ID and configuration (D-P4-1-D).**
   - `external_id(e)` is 64 lowercase hex characters, equals the HMAC computed in the test from the D-P4-1-D formula, is stable across calls, differs for two engagements, and changes when the secret changes.
   - `is_configured()` is `False` for `""`, a 31-character secret, and a secret equal to `settings.session_secret` (patch both); `True` for 32+ characters that differ. For each `False` case: `pull_aws_evidence` raises `AwsNotConfigured(NOT_CONFIGURED)`, `_sts_client` is never called, nothing written; `GET` the page → 200 with `data-aws-not-configured`, and without `data-aws-pull-form`, `data-external-id` or `data-trust-policy`.
   - A POST that also sends `external_id=attacker-chosen`, `aws_access_key_id=…`, `aws_secret_access_key=…` → the AssumeRole stub's expected `ExternalId` is still `external_id(engagement.id)` (the extra fields are ignored), and the pull succeeds.
   - `Settings.model_fields` contains `aws_external_id_secret` and no other field whose name contains `aws`.
5. **Input validation (D-P4-1-E).** Parametrized; each raises `AwsValidationError` with the exact message, `_sts_client` is never called, and nothing is written (no audit row): account `"12345"`, `"11112222333a"`; role `"arn:aws-us-gov:iam::111122223333:role/X"`, `"arn:aws:iam::111122223333:user/X"`, `"arn:aws:iam::111122223333:root"`, `"not an arn"`; role account `444455556666` with account `111122223333` → `ROLE_ACCOUNT_MISMATCH`; regions `""` / `" , "` → `REGIONS_REQUIRED`; five distinct regions → `TOO_MANY_REGIONS`; `"eu-west-1, mars-north-1"` → `UNKNOWN_REGION` naming `mars-north-1`; `"us-gov-west-1"` → `UNKNOWN_REGION`. Positive: `" EU-WEST-1 ,eu-west-1  us-east-1"` normalises to `("eu-west-1", "us-east-1")`. Unknown engagement → `AwsEngagementNotFound`. `len(SUPPORTED_REGIONS) == 34` with the pinned botocore, and it contains `eu-west-1` and `us-east-1` but not `us-gov-west-1` or `cn-north-1`.
6. **STS failures (D-P4-1-F, J).** Each failed cleanly, with no `_service_client` call:
   - probe **succeeds** → `TRUST_POLICY_MISSING_EXTERNAL_ID`, step `trust_policy_check`; the real AssumeRole is **not** called (no pending stub for it is consumed: stub only the probe);
   - real AssumeRole `AccessDenied` → `ASSUME_ROLE_DENIED`, step `assume_role`, `error_code "AccessDenied"`;
   - `AssumedRoleUser.Arn` in account `444455556666` → `ASSUMED_ACCOUNT_MISMATCH`;
   - `RegionDisabledException` → `STS_REGION_DISABLED` naming the first region;
   - `ExpiredToken` on the probe → `BASE_CREDENTIALS_UNAVAILABLE`;
   - a fake STS client raising `NoCredentialsError()` → `BASE_CREDENTIALS_UNAVAILABLE`, `error_code "NoCredentialsError"`; raising `EndpointConnectionError(endpoint_url="https://sts.eu-west-1.amazonaws.com")` → `AWS_UNREACHABLE`;
   - every `pull_failed` row's `message` equals the raised message, and its metadata has no key other than D-P4-1-K's.
7. **Service failures and non-errors (D-P4-1-G, J).**
   - Two regions: region 1 fully succeeds; region 2's `GetComplianceDetailsByConfigRule` → `AccessDeniedException` → `PERMISSION_MISSING` with `config:GetComplianceDetailsByConfigRule` and region 2; failed cleanly, so **region 1's data was not written either**.
   - `GetFindings` `AccessDeniedException` → `PERMISSION_MISSING` with `securityhub:GetFindings`.
   - `ExpiredTokenException` from Config → `SESSION_EXPIRED`; `UnrecognizedClientException` from Security Hub → `REGION_NOT_ENABLED`; `ThrottlingException` from Config → `AWS_ERROR` with code `ThrottlingException` and step `config` (verified: a stubbed error bypasses botocore's retry handler even with `mode="standard"`, so one stub suffices).
   - Security Hub `InvalidAccessException` on the first call → the pull **succeeds**, the Security Hub source row has `status "not_enabled"`, 0 items; the Config items are written.
   - `NoSuchConfigRuleException` for one rule → that rule is skipped, `skipped_rules == 1`, the others are written.
   - Deadline: patch `_monotonic` to jump past 600 s after the AssumeRole call → `DEADLINE_EXCEEDED`, step `deadline`, failed cleanly.
8. **All-or-nothing write (D-P4-1-I).**
   - Patch `app.services.aws_evidence.evidence_service.release_from_quarantine` (the module attribute the service uses) to raise `RuntimeError` on its third call → `AwsPullFailed(WRITE_FAILED)`, step `write`; no Evidence or version rows; **no file under `upload_root / "evidence"`**; exactly one `pull_failed` row.
   - A write failure during a re-pull (v2 of an existing item) → the existing Evidence still has only v1, still `active`, and its blob is intact (`verify_version`).
9. **Caps and truncation (D-P4-1-G).**
   - One rule with six pages of 100 evaluations → the document has 500 evaluations and `truncated: true`; exactly five `GetComplianceDetailsByConfigRule` calls were made (Stubber with five stubs; the sixth page is never requested).
   - 21 pages of 100 findings → 2000 findings kept across the generator documents, each document's `truncated` and the source row's `truncated` are `true`, exactly 20 `GetFindings` calls.
   - 301 active rules → 300 Evidence items (the first 300 by name) and the Config source row has `truncated: True`.
10. **Credential hygiene (D-P4-1-A, F, N).**
    - After a scenario-1 pull run under `caplog.set_level(logging.DEBUG)` (root logger, so botocore's loggers are captured too): none of `"test-session-secret-DO-NOT-LEAK"`, `"test-session-token-DO-NOT-LEAK"`, `"ASIATESTTESTTESTTEST"`, `"test-base-secret"` or `external_id(engagement.id)` appears in `"\n".join(sqlite3.connect(db_path).iterdump())`, in any file's bytes under `upload_root`, in `caplog.text`, or in any `audit_events.metadata_json`.
    - `repr(TemporaryCredentials("AKVALUE1", "SKVALUE2", "STVALUE3", now))` contains `expiration` and none of `AKVALUE1`, `SKVALUE2`, `STVALUE3`.
    - `_service_client`: monkeypatch `boto3.session.Session` with a recorder → it's called with exactly `aws_access_key_id`, `aws_secret_access_key`, `aws_session_token` from the credentials and `region_name`, and `.client(service, config=BOTO_CONFIG)`. `_sts_client`: the recorder shows `Session()` called with **no** credential keyword.
    - `_call(object(), "config", "PutConfigRule")` raises `AssertionError`, and the object is never touched. Source guards on `app/services/aws_evidence.py`: the regex `\.(assume_role|describe_config_rules|get_compliance_details_by_config_rule|get_findings|get_paginator)\(` matches nothing; `boto3.client(` and `boto3.resource(` are absent; `aws_secret_access_key` and `aws_session_token` appear only inside `_service_client`'s body (check with `inspect.getsource`); the `set(AWS_OPERATIONS)` equals the four tuples of D-P4-1-A.
11. **Routes and page (D-P4-1-L, M).**
    - `GET /engagements/{e}/aws-evidence` → 200, `Cache-Control: no-store`, `Referrer-Policy: no-referrer`; the page (after `html.unescape`) contains `external_id(e)` in `data-external-id`, the `json.dumps(..., indent=2)` of the three policies, `data-aws-pull-form`, and no `CyberAssess`. Unknown engagement → 404.
    - `POST …/pull` (form fields only, stubs as in scenario 1) → 200, `data-aws-result`, two `data-aws-source-row`, four `data-aws-evidence-row`, each linking `/evidence/{id}`; the headers as above. A validation error → 200 with `data-aws-error` and the exact message, with the submitted values refilled in the form.
    - `POST` with `Origin: https://evil.example` → 403, `ORIGIN_REJECTED` in the body, `_sts_client` never called, nothing written. With `Origin: http://testserver` (the TestClient host) → proceeds.
    - After one pull, `GET` prefills `account_id`, `role_arn` and `eu-west-1` from `last_pull_inputs`, and the permissions policy block uses that account.
    - `inspect.iscoroutinefunction` is `False` for both handlers. The set of app routes whose path contains `/aws-evidence` is exactly `{("GET", "/engagements/{engagement_id}/aws-evidence"), ("POST", "/engagements/{engagement_id}/aws-evidence/pull")}`.
    - `GET /engagements/{e}` contains `href="/engagements/{e}/aws-evidence"`.
    - Escaping: a role ARN value `arn:aws:iam::111122223333:role/<script>` fails validation, and the refilled form shows `&lt;script&gt;`, never `<script>`.
12. **Structural guards and nothing else moved.**
    - `pages/aws_evidence.html` and `partials/aws_evidence_panel.html` don't match `\|\s*safe\b|overall_score|CyberAssess`.
    - `inspect.signature(evidence_service.receive_version).parameters["file_type"].default is None`, and it's keyword-only.
    - The full suite passes, including unchanged `tests/test_evidence_service.py`, `tests/test_magic_links.py`, `tests/test_white_label.py`, `tests/test_config_security_warnings.py`, `tests/test_no_blended_scoring.py` and `tests/test_remediation_tracking.py`.

## Done criteria

- `tests/test_aws_evidence.py` passes. `.venv/bin/pytest -q` passes in full: **502 + N** (N = new test cases; state the baseline you measured). In a fresh worktree, expect the known one-time `_guard_dev_database_untouched` teardown error described above, and nothing else.
- `git diff main -- tests/` shows **only** the new file.
- `git diff --stat main` shows changes **only** in: `requirements.txt`, `.env.example`, `app/config.py`, `app/services/evidence.py`, `app/services/aws_evidence.py` (new), `app/routers/aws.py` (new), `app/main.py`, `app/templates/pages/aws_evidence.html` (new), `app/templates/partials/aws_evidence_panel.html` (new), `app/templates/pages/engagement_detail.html`, `docs/operations/aws-evidence.md` (new), `tests/test_aws_evidence.py` (new), `tasks/todo.md` and this handoff.
- `git diff main -- app/services/evidence.py` is exactly the signature parameter and the one `_file_type(filename, file_type)` call.
- `git diff --stat main -- app/models alembic/versions app/routers/web.py app/routers/magic.py app/services/magic_links.py app/services/document_processor.py scripts` is empty. `alembic heads` is still exactly `4e8c1a9d2b57`. `grep -rn "relationship(" app/models/` is empty.
- **Smoke test** (per the project rule; record the outputs). A fresh Alembic-built DB, a temporary `upload_dir`, the in-process ASGI `TestClient` (socket binds have been refused in this sandbox before), `AWS_EXTERNAL_ID_SECRET` set, and the `FakeAws` stubs from the test file (there is no real AWS account here):
  1. `GET /engagements/{e}/aws-evidence` → paste the status, the external ID's first 8 characters (not the whole value), and confirm the three policy blocks are present.
  2. `POST …/pull` with one region → paste the source rows, then `SELECT uploaded_by, original_filename, status FROM evidence` and `SELECT evidence_id, version_number, status, file_hash_sha256 FROM evidence_versions`.
  3. Pull again with one changed evaluation → paste the same two queries (one v2, one `superseded`).
  4. `SELECT action, metadata_json FROM audit_events WHERE action LIKE 'aws_evidence.%'`, and confirm by `grep -c` over a `.dump` of the DB and over the upload tree that the stub secret, session token and external ID occur **0** times.
  5. A pull whose Security Hub stub returns `AccessDeniedException` → paste the panel's error text and confirm the row counts didn't change.
  6. **Real AWS**: optional per the Phase 4 exit criterion. Only if the dispatching session supplies a real test account and role. Codex must not attempt it on its own. Otherwise write "Real-account check not run" in Results.
  7. **Browser check**, if a browser is available: open the page, run a stubbed pull from the form. If none is available, say so. Don't claim it.

## Rollback

- **Code:** `git revert`. No schema change, so nothing to downgrade. Evidence rows the adapter created remain as ordinary engagement-level Evidence with `text/plain` blobs, readable on `/evidence/{id}`; the reverted app never writes new ones. `receive_version`'s extra parameter goes away with the revert; no other caller uses it.
- **Data:** nothing is deleted or rewritten. A mistaken pull is undone by archiving its Evidence (`transition_evidence(..., "archived")`), which the next pull respects (D-P4-1-I).
- **Client side:** the client deletes the role, or removes the trust statement, and access ends immediately. No CyberAssess-side credential exists to revoke.

## Open questions (deliberately flagged, not resolved here)

1. **Real-account validation.** The Stubber checks every parameter against the service model, but only a real account proves the IAM policy is sufficient (for example that `hub/default` is the resource Security Hub evaluates for `GetFindings` in every account setup). Run a pull against a consultant-owned test account before the first client use; record it in this file.
2. **External-ID rotation per engagement.** Rotating `AWS_EXTERNAL_ID_SECRET` rotates every engagement's ID at once. Per-engagement rotation or revocation would need stored state (a schema change). Until then, a client revokes by removing the role.
3. **Security Hub v2** (`GetFindingsV2`, `hubv2/*` resources) and OCSF findings. Out of scope for D10's v1.
4. **Mapping AWS evidence to requirements.** Items are engagement-level and reach analysis only through `map_evidence`. A bulk or suggested mapping (for example by Config rule source identifier to control) is D8's "system suggestions" and needs its own design.
5. **Disappeared rules or generators.** Their Evidence stays active and may go stale. A "not seen in the latest pull" marker, or an age warning (P4-2's evidence-reuse warnings), would make that visible.
6. **App-wide CSRF.** Only the pull route checks `Origin`. The other state-changing routes rely on the no-auth, single-user local deployment; a real multi-user deployment needs a general fix, and should narrow `CORSMiddleware`'s wildcard.
7. **Synchronous pulls.** A large account can hold the request for minutes (bounded by the 600 s deadline). A background job with status would need a table.

## Results

_To be filled in by the implementer (Codex) and then the reviewing Claude session. Include:_
- _The Step 0 output (`boto3`/`botocore` versions)._
- _The final public API of `app/services/aws_evidence.py` copied from the code (constants, dataclasses, function signatures), and the exact `permissions_policy("111122223333")` and `trust_policy(...)` output, copied from a Python run, not from this document._
- _Focused and full `pytest -q` output with counts (baseline measured + N)._
- _The smoke-test outputs from Done criteria items 1–5, and the explicit status of items 6 and 7._
- _The `git diff --stat main` output and confirmation that each protected-file diff is empty._
- _Any deviation forced by the code, named explicitly, with the decision it touches. Per the instruction at the top: if the code forces a deviation from this design, stop and report it here; do not pick an alternative._
