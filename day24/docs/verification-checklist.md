# Day 24 – DevOps & AWS Verification Checklist

Use this checklist to track local implementation readiness versus actual cloud deployment verification.

---

## Part 1: Local Implementation Readiness (Completed & Verified Locally)

- [x] **Backend Dockerfile Multi-Stage Build:** Non-root user (`thriveni`), dependencies isolated in `/opt/venv`, `/health` healthcheck configured.
- [x] **Structured JSON Application Logging:** Emits machine-readable JSON logs with ISO-8601 timestamps, log level, module, service name, and execution duration.
- [x] **Request ID Correlation:** Middleware extracts or generates `X-Request-ID` and returns it in HTTP response headers.
- [x] **PII & Secrets Scrubbing:** Passwords, API keys, and bearer tokens are masked with `[FILTERED]` in log records and Sentry events.
- [x] **Backend Health Check (`/health`):** Validates database and Redis connectivity without leaking credentials. Returns status 200 when healthy, 503 when degraded.
- [x] **Prometheus Operational Metrics (`/metrics`):** Exposes `http_requests_total`, `http_request_duration_seconds`, and `http_errors_total`.
- [x] **Backend Sentry Integration:** Dynamically activates when `SENTRY_DSN` is provided; no-ops safely when omitted.
- [x] **Frontend Sentry Integration:** Dynamically activates in React/Vite when `VITE_SENTRY_DSN` is configured.
- [x] **Vercel Configuration (`frontend/vercel.json`):** Configures Vite build, `dist` output, HTML5 History Mode rewrites, and asset cache headers.
- [x] **Production Nginx Reverse Proxy Config (`day24/nginx.conf`):** Upstream keepalive, SSE unbuffered streaming for `/ai/`, WebSocket upgrade headers for `/ws`, Certbot webroot challenge location, and HTTPS certificate templates.
- [x] **Production Docker Compose Stack (`day24/docker-compose.prod.yml`):** Internal database/redis isolation, named volumes, and production service definitions.
- [x] **Prometheus Scrape Configuration (`day24/prometheus.yml`):** Configured to scrape `backend:8000/metrics`.
- [x] **Secrets Protection (`.gitignore`):** Excludes `.pem`, `.key`, `.crt`, `.id_rsa`, `.aws/`, `credentials`, `day24/.env`, and `.sentryclirc`.

---

## Part 2: Cloud Deployment Verification (Requires AWS & Domain Approvals)

- [ ] **AWS EC2 Instance Provisioned:** Ubuntu 24.04 LTS instance launched in your AWS account.
- [ ] **Elastic IP Attached:** Static public IPv4 assigned to the EC2 instance.
- [ ] **Security Group Configured:** Port 22 (restricted to My IP), Port 80 (Anywhere), Port 443 (Anywhere).
- [ ] **SSH Access Verified:** Successful connection via SSH key pair (`ssh -i ~/.ssh/key ubuntu@<IP>`).
- [ ] **Domain DNS A-Record Active:** `api.yourdomain.com` points to the EC2 Elastic IP.
- [ ] **Certbot SSL Certificate Issued:** Valid Let's Encrypt certificate generated for the domain.
- [ ] **HTTPS Enforced:** HTTP (port 80) redirects with 301 to HTTPS (port 443).
- [ ] **Vercel Frontend Deployed:** React Vite app live on Vercel with `VITE_API_URL` pointing to backend.
- [ ] **CORS Verified End-to-End:** Vercel frontend communicates with EC2 backend without CORS blocks.
- [ ] **UptimeRobot Monitor Active:** 60-second automated ping monitoring `/health` with email alert contacts.
- [ ] **CloudWatch Monitoring Active:** CPU utilization and RAM metrics reporting in CloudWatch console.
