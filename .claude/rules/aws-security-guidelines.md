# AWS Security Guidelines

Binding on the deployment group, and on any agent that touches credentials, IAM, or cloud resources.

## Blast radius

- **Never apply to production without explicit user approval in the current session.** Approval for a dev apply is not approval for prod.
- `terraform plan` freely. `terraform apply` only against dev/test, and only when the task says to.
- **Never run destructive commands** (`terraform destroy`, `aws s3 rb`, `aws rds delete-*`) unless the user asked for that specific action on that specific resource.
- Read the plan output before applying. An apply that shows unexpected replacements is a stop, not a shrug.

## Identity and access

- **Least privilege by default.** Scope IAM policies to the specific actions and resource ARNs required. No `"Action": "*"`, no `"Resource": "*"` outside of documented, justified exceptions.
- Prefer **IAM roles over long-lived access keys**. No IAM users with keys for service-to-service auth.
- Application code authenticates via the instance/task/pod role, never embedded credentials.
- T3 verification runs as the **application's identity**, not yours. See @.claude/rules/testing-standards.md.

## Secrets

- **No secrets in code, Terraform, environment files, or git history.** Not even placeholders that look real.
- Secrets live in AWS Secrets Manager or SSM Parameter Store (SecureString), referenced by ARN.
- Terraform state contains secret values in plaintext — **remote state must be encrypted**, access-controlled, and never committed.
- If you find a committed secret: stop, tell the user, do not attempt to rewrite history on your own.

## Data protection

- Encryption at rest on by default: S3 (SSE-KMS or SSE-S3), RDS, EBS, DynamoDB.
- TLS in transit everywhere. No plaintext internal traffic "because it's in the VPC."
- S3 buckets: block public access unless the bucket's entire purpose is public static hosting, and say so in `design.md`.

## Network

- Databases and internal services in private subnets. No public IPs on data stores.
- Security groups reference other security groups, not CIDR ranges, for internal traffic.
- No `0.0.0.0/0` ingress except on load balancers serving public traffic on 80/443.

## Observability and tagging

- CloudTrail enabled. Application logs to CloudWatch with a defined retention — not infinite, not default.
- Every resource tagged: `Project`, `Environment`, `Owner`, `ManagedBy=terraform`.

## Design gate

`design.md` must carry a **Security Considerations** section covering auth/authz model, data classification, secrets handling, and network exposure. A design without it is incomplete and the architect should not hand it off.
