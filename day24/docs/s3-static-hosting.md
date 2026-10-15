# Day 24 – Task 7: Amazon S3 Static Hosting & CloudFront Architecture

This guide explains how static asset hosting works in AWS S3, security pitfalls of public buckets, and the recommended production architecture using CloudFront Origin Access Control (OAC).

---

## 1. Static Website Hosting vs CloudFront CDN

There are two primary ways to host static files (e.g. React build files or product images) in Amazon S3:

### Option A: S3 Website Endpoint (Direct Public Bucket)
- **Mechanism:** Enables "Static website hosting" in S3 bucket properties. Disables S3 Block Public Access.
- **Protocol:** Serves traffic over unencrypted HTTP (no custom HTTPS without CloudFront).
- **Security:** High risk: accidentally leaves uploaded user files or invoices readable by anyone on the internet.
- **Cost:** High egress costs when traffic spikes.

### Option B: Private S3 Bucket + Amazon CloudFront CDN (Production Best Practice)
- **Mechanism:** S3 bucket remains **100% private** with all public access blocked.
- **Protocol:** CloudFront terminates HTTPS at 400+ edge locations globally.
- **Security:** CloudFront signs requests using **Origin Access Control (OAC)**. Only CloudFront is allowed to read from S3. Direct HTTP requests to S3 are rejected with HTTP 403.
- **Performance:** Files are cached close to the customer, drastically reducing latency.

```
End Users (Browsers)
       │ HTTPS
       ▼
[ Amazon CloudFront CDN ] (Global Edge Cache)
       │ AWS SigV4 signed request (OAC)
       ▼
[ Amazon S3 Bucket ] (100% Private, Block Public Access ENABLED)
```

---

## 2. Safe Architecture: Private Bucket with CloudFront OAC

### Step 2.1: S3 Bucket Creation Settings
1. **Bucket Name:** `shopzone-static-assets-prod` (must be globally unique)
2. **Region:** `us-east-1` (or your nearest AWS region)
3. **Block Public Access:** **Keep ENABLED (All 4 checkboxes checked)**
   - Block public ACLs
   - Ignore public ACLs
   - Block public policy
   - Restrict public bucket
4. **Bucket Encryption:** Server-Side Encryption with Amazon S3 managed keys (SSE-S3).

### Step 2.2: CloudFront Origin Access Control (OAC) Bucket Policy

This policy guarantees that **only** your CloudFront distribution can read files from your private bucket:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontServicePrincipalReadOnly",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::shopzone-static-assets-prod/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::123456789012:distribution/EDFDVBD6EXAMPLE"
        }
      }
    }
  ]
}
```

---

## 3. Safe Example: Uploading Static Assets to S3

If using AWS CLI locally or in CI/CD:

```bash
# Sync production frontend build to S3 bucket
aws s3 sync ./frontend/dist s3://shopzone-static-assets-prod/ \
  --delete \
  --cache-control "public, max-age=31536000, immutable" \
  --exclude "index.html"

# Upload index.html with no-cache so users always receive latest version
aws s3 cp ./frontend/dist/index.html s3://shopzone-static-assets-prod/index.html \
  --cache-control "no-cache, no-store, must-revalidate"

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id EDFDVBD6EXAMPLE \
  --paths "/*"
```

---

## 4. Cost Safeguards & Pricing Warnings

> [!WARNING]
> While S3 storage is inexpensive ($0.023 per GB/month), public S3 buckets can fall victim to "denial-of-wallet" attacks if malicious actors repeatedly download massive files.
> By keeping your bucket **private** and putting **CloudFront** with rate limiting in front, you avoid unexpected bandwidth bills.
