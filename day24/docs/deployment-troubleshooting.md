# Day 24 – Deployment Troubleshooting Guide

This guide provides practical solutions for the most common errors encountered when deploying ShopZone across AWS EC2, Nginx, Docker, and Vercel.

---

## 1. HTTP 502 Bad Gateway (Nginx to Backend)

### Symptoms:
The browser or Vercel frontend receives `502 Bad Gateway` when calling `/api/products` or `/health`.

### Root Cause Analysis:
Nginx is running on port 80/443, but cannot reach the backend service on `backend:8000`.

### Diagnostic Steps:
```bash
# 1. Check if backend container is running
docker compose -f day24/docker-compose.prod.yml ps

# 2. Check backend container logs
docker compose -f day24/docker-compose.prod.yml logs --tail=50 backend

# 3. Test direct internal connectivity from Nginx to backend
docker compose -f day24/docker-compose.prod.yml exec nginx wget -qO- http://backend:8000/health
```

### Common Fixes:
- **Backend crashed during startup:** Check if database credentials in `.env` match PostgreSQL container (`POSTGRES_USER` / `POSTGRES_PASSWORD`).
- **Wrong Docker network:** Ensure both `nginx` and `backend` services specify `shopzone-prod-network`.
- **Database healthcheck failing:** Backend container waits for `postgres` to be healthy before starting. Check `docker compose logs postgres`.

---

## 2. CORS Errors (Frontend on Vercel Blocked by Browser)

### Symptoms:
Browser console displays:
`Access to fetch at 'https://api.yourdomain.com/api/products' from origin 'https://shopzone.vercel.app' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present.`

### Root Cause Analysis:
The FastAPI backend's `FRONTEND_ORIGINS` setting does not include the exact Vercel frontend domain.

### Diagnostic & Fix:
1. Note the exact domain in the browser address bar (including `https://` without a trailing slash).
2. SSH into EC2 and update `FRONTEND_ORIGINS` in `.env`:
   ```ini
   FRONTEND_ORIGINS=https://shopzone.vercel.app,https://yourdomain.com,http://localhost:5173
   ```
3. Restart the backend:
   ```bash
   docker compose -f day24/docker-compose.prod.yml restart backend
   ```
4. Clear browser cache and re-test.

---

## 3. Certbot Let's Encrypt Verification Fails (ACME Challenge)

### Symptoms:
`certbot certonly --webroot` fails with:
`Detail: Fetching http://api.yourdomain.com/.well-known/acme-challenge/...: Timeout during connect (likely firewall problem)`

### Common Fixes:
1. **DNS Not Propagated:** Run `dig +short api.yourdomain.com`. If it does not return your EC2 Elastic IP, wait for DNS propagation.
2. **Security Group Port 80 Blocked:** Verify EC2 Security Group allows inbound **HTTP (Port 80)** from `0.0.0.0/0`.
3. **Volume Mount Missing:** Ensure Nginx has `- certbot_www:/var/www/certbot` mounted and Certbot specifies `-w /var/www/certbot`.

---

## 4. Linux Out-Of-Memory (OOM) Killer Terminating Containers

### Symptoms:
Containers unexpectedly exit with code `137` (SIGKILL).

### Root Cause:
ChromaDB, PostgreSQL, or Celery exceeded the physical RAM of a `t2.micro` or `t3.micro` instance.

### Fix:
Verify swap space is active:
```bash
free -h
# If Swap reports 0B, activate 2GB swap:
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 5. Sentry Not Receiving Errors

### Diagnostic Steps:
1. Check if `SENTRY_DSN` is empty:
   ```bash
   docker compose -f day24/docker-compose.prod.yml exec backend python -c "from backend.app.core.config import settings; print('DSN Set:', bool(settings.SENTRY_DSN))"
   ```
2. Verify outbound HTTPS connectivity from the container:
   ```bash
   docker compose -f day24/docker-compose.prod.yml exec backend curl -I https://o0.ingest.sentry.io
   ```
3. Check browser ad-blockers: Extensions like uBlock Origin block requests to `sentry.io` in development. Disable the extension on your frontend site to verify.
