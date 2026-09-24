# AWS evidence pull

## What this does

The consultant can manually pull active AWS Config rule evaluations and active Security Hub findings into an engagement. The pull assumes a client role through STS using an engagement-bound external ID. The session policy limits the temporary session to three read-only actions. Each Config rule and Security Hub finding generator becomes versioned engagement evidence. No credentials are stored, no AWS write operation is used, and no pull runs on a schedule.

## Client setup

Create a role named `ComplianceEvidenceReadOnly` in the client account. Its trust policy must name the consultant's specific role, not the consultant account root, and must require the external ID shown on the engagement page.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowConsultantEvidencePull",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::<CONSULTANT_ACCOUNT_ID>:role/<CONSULTANT_ROLE_NAME>"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "<EXTERNAL_ID_FROM_THE_ENGAGEMENT_PAGE>"
        }
      }
    }
  ]
}
```

Replace the placeholder principal with the consultant role ARN. Never use an account root principal.

Attach only this inline permissions policy to the client role:

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

## Consultant setup

Set `AWS_EXTERNAL_ID_SECRET` to a random value of at least 32 characters that differs from `SESSION_SECRET`. Rotating it changes every engagement's derived external ID, so each client trust policy must be updated. Use the default AWS credential chain on the machine running the portal; short-lived IAM Identity Center credentials are recommended, and long-lived IAM user keys defeat this design.

The consultant identity needs this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AssumeClientEvidenceRoles",
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::*:role/ComplianceEvidenceReadOnly"
    }
  ]
}
```

## Why each permission

| Action | What it reads | Why `DescribeConfigRules` uses `*` |
|---|---|---|
| `config:DescribeConfigRules` | Active Config rule metadata | AWS does not expose a resource type for this operation, so IAM requires `*`. |
| `config:GetComplianceDetailsByConfigRule` | Compliant and non-compliant evaluations per resource | The account-scoped Config rule ARN covers every opaque rule ID in every selected region. |
| `securityhub:GetFindings` | Active Security Hub findings with severity | The account-scoped `hub/default` ARN covers the account's Security Hub findings in every selected region. |

## What is collected and what is not

The pull requests active Config rules and `COMPLIANT`/`NON_COMPLIANT` evaluations, plus active Security Hub findings filtered to the entered account and region. It groups evidence by Config rule name and Security Hub `GeneratorId`; it does not create resource-inventory evidence. The adapter does not request or store `ResultToken`, `InputParameters`, `Scope`, `OrderingTimestamp`, `ResourceEvaluationId`, finding `Description`, `Remediation`, `ProductFields`, `Resources[].Details`, `Network`, `Process`, `Malware`, or `UserDefinedFields`. It performs no AWS write, has no schedule, and has no continuous monitoring.

## Rotating the external ID secret

Changing `AWS_EXTERNAL_ID_SECRET` changes every engagement's external ID. Update each client trust policy with the newly displayed value before the next pull; a client can revoke access immediately by removing the trust statement or deleting the role.

## Troubleshooting

- `NOT_CONFIGURED` — AWS evidence collection is not configured. Set AWS_EXTERNAL_ID_SECRET in .env to a random value of at least 32 characters that differs from SESSION_SECRET, then restart.
- `INVALID_ACCOUNT_ID` — Enter the client's 12-digit AWS account ID.
- `INVALID_ROLE_ARN` — Enter the role ARN in the form arn:aws:iam::<account-id>:role/<role-name>.
- `ROLE_ACCOUNT_MISMATCH` — The role ARN must belong to the AWS account ID entered.
- `REGIONS_REQUIRED` — Enter at least one AWS region.
- `TOO_MANY_REGIONS` — Pull at most 4 regions at a time.
- `UNKNOWN_REGION` — Unknown or unsupported AWS region: {region}.
- `BASE_CREDENTIALS_UNAVAILABLE` — This machine has no usable AWS credentials for the consultant identity.
- `ASSUME_ROLE_DENIED` — Could not assume the role.
- `TRUST_POLICY_MISSING_EXTERNAL_ID` — The role can be assumed without this engagement's external ID.
- `ASSUMED_ACCOUNT_MISMATCH` — The assumed role belongs to a different AWS account than the one entered.
- `STS_REGION_DISABLED` — AWS STS is not activated in {region}.
- `REGION_NOT_ENABLED` — The temporary session is not valid in {region}; the region may not be enabled for this account.
- `PERMISSION_MISSING` — The role is missing permission {action} in {region}.
- `SESSION_EXPIRED` — The temporary AWS session expired before the pull finished.
- `DEADLINE_EXCEEDED` — The pull took longer than 10 minutes and was stopped.
- `AWS_UNREACHABLE` — Could not reach AWS.
- `AWS_ERROR` — AWS returned an error ({code}) during {step}.
- `WRITE_FAILED` — The AWS data was retrieved but could not be saved as evidence.
- `ORIGIN_REJECTED` — Cross-site requests cannot start an AWS pull.
