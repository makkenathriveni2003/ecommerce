# Day 24 – Task 6: AWS IAM and Least Privilege Security Architecture

This guide explains AWS Identity and Access Management (IAM), why using the AWS Root Account for deployments is dangerous, and how to apply the Principle of Least Privilege.

---

## 1. Core IAM Concepts Explained for Beginners

| Concept | What It Is | ShopZone Analogy |
| :--- | :--- | :--- |
| **Root User** | The account owner created with email/password. Has unrestricted access to every resource and billing. | The building owner with master keys to all safes. |
| **IAM User** | An individual identity (e.g. `devops-thriveni`) with specific, limited permissions. | An employee with an assigned keycard. |
| **IAM Policy** | A JSON document explicitly defining what actions are **Allowed** or **Denied** on which resources. | The security rules dictating which rooms a keycard unlocks. |
| **IAM Role** | A temporary identity that can be assumed by applications, EC2 instances, or GitHub Actions without hardcoding passwords. | A visitor badge given for a specific task that expires automatically. |
| **Instance Profile** | A container that passes an IAM Role to an Amazon EC2 instance. | A badge assigned to a machine inside the data center. |

---

## 2. Why Never Use Root Account Credentials

1. **Unrestricted Blast Radius:** If a root password or root access key leaks (e.g. accidentally committed to GitHub), an attacker can delete all databases, launch thousands of crypto-mining GPU instances, and rack up tens of thousands of dollars in debt within minutes.
2. **No Audit Granularity:** CloudTrail logs will only show actions taken by "Root", preventing you from determining which team member or process performed the action.
3. **No Revocation Without Changing Passwords:** Root credentials cannot be scoped to temporary access.

### Recommended Best Practice:
1. Enable Multi-Factor Authentication (MFA) on your AWS Root User immediately.
2. Lock away the root credentials and **only** use them for closing the account or changing AWS billing support plans.
3. Create an IAM admin group or CI/CD deployment role with least privilege for all daily work.

---

## 3. IAM Roles vs Permanent Access Keys

> [!TIP]
> **Never store permanent AWS Access Keys (`AKIA...`) on your EC2 instance!**
> Instead, attach an **IAM Role with an EC2 Instance Profile**.

When an IAM Role is attached to an EC2 instance:
- AWS dynamically generates short-lived credentials via the EC2 Instance Metadata Service (`http://169.254.169.254/latest/meta-data/iam/security-credentials/`).
- Credentials rotate automatically every few hours.
- If the EC2 server is ever compromised, the attacker does not acquire permanent AWS credentials.

---

## 4. Minimal Least-Privilege Policies for ShopZone

### Policy 1: EC2 CloudWatch Logging & Metrics (`ShopZoneCloudWatchPolicy`)

Grants permission to send logs and metrics from the EC2 instance to CloudWatch:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudWatchLogsAndMetrics",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams",
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*"
    }
  ]
}
```

### Policy 2: S3 Media Storage Access (`ShopZoneS3Policy`)

Grants backend access only to the dedicated ShopZone media bucket:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowBucketOperations",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": "arn:aws:s3:::shopzone-production-assets"
    },
    {
      "Sid": "AllowObjectOperations",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::shopzone-production-assets/*"
    }
  ]
}
```

### Policy 3: GitHub Actions CI/CD Deployment Role (`ShopZoneGithubDeployRole`)

Uses OpenID Connect (OIDC) instead of static AWS keys:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowECRImagePush",
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "arn:aws:ecr:*:*:repository/shopzone-backend"
    }
  ]
}
```
