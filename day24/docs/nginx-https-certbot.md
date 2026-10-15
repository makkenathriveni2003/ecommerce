# Day 24 – Task 2: Nginx Reverse Proxy, Domain Setup & Let's Encrypt HTTPS

This guide explains how Nginx acts as the single entrypoint for the ShopZone backend, how domain names and DNS records connect to AWS EC2, and how to automate SSL/TLS certificates using Certbot and Let's Encrypt.

---

## 1. Why Use Nginx as a Reverse Proxy?

Instead of directly exposing Uvicorn (FastAPI) on port 80/443:

```
Clients (Browser / Mobile / Vercel)
               │ (Port 80 / 443)
               ▼
     [ Nginx Reverse Proxy ]
        ├── SSL Termination (HTTPS -> HTTP)
        ├── GZip Response Compression
        ├── HTTP Request Buffering & Keepalive
        ├── Security Headers (HSTS, CSP, X-Frame-Options)
        ├── SSE Streaming (Buffering disabled for /ai/)
        ├── WebSocket Upgrades (/ws)
        └── Health Probing (/health, /metrics)
               │ (Private Docker Network)
               ▼
     [ FastAPI / Uvicorn ] (Port 8000)
```

1. **SSL Offloading:** Handles TLS encryption/decryption so Python workers focus on business logic.
2. **WebSocket & SSE Support:** Handles long-running connections and streaming without consuming ASGI threads unnecessarily.
3. **Defense in Depth:** Prevents direct network access to Uvicorn, PostgreSQL, Redis, or ChromaDB.

---

## 2. Domain & DNS Configuration Requirements

> [!IMPORTANT]
> **HTTPS CANNOT be issued for an arbitrary raw IP address.**
> Let's Encrypt issues certificates only for valid, registered Fully Qualified Domain Names (FQDNs) where domain ownership can be verified via the ACME HTTP-01 challenge.

### DNS Records to Create at your Domain Registrar (Namecheap, GoDaddy, Cloudflare, Route 53):

| Type | Host / Name | Value / Points To | TTL | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **A** | `api` | `<EC2_ELASTIC_IP>` | 300 (Auto) | Directs `api.yourdomain.com` to the EC2 instance |
| **A** | `@` (Root) | `<EC2_ELASTIC_IP>` | 300 (Auto) | Directs root domain (if backend hosted on root) |
| **CNAME** | `www` | `yourdomain.com` | 300 (Auto) | Canonical alias |

### Verify DNS Propagation:
```bash
# Verify using nslookup or dig:
nslookup api.yourdomain.com
dig +short api.yourdomain.com
```
Both must return your EC2 Elastic IP before proceeding with Certbot!

---

## 3. Obtaining Let's Encrypt Certificates with Certbot

We use the official Docker image `certbot/certbot` with the `webroot` plugin to obtain certificates without taking Nginx offline.

### Step 3.1: Run Certbot Challenge Request

On your EC2 terminal:

```bash
docker run -it --rm --name certbot \
  -v shopzone_certbot_conf:/etc/letsencrypt \
  -v shopzone_certbot_www:/var/www/certbot \
  certbot/certbot certonly --webroot \
  -w /var/www/certbot \
  -d api.yourdomain.com \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email
```

### Step 3.2: Verify Certificate Files
```bash
docker run --rm -v shopzone_certbot_conf:/etc/letsencrypt alpine ls -lh /etc/letsencrypt/live/api.yourdomain.com/
```
You will see:
- `fullchain.pem` – The server certificate bundled with intermediate CA certificates.
- `privkey.pem` – The secret private key (kept strictly secure).

---

## 4. Enabling HTTPS and HTTP-to-HTTPS Redirection

Once the certificate files exist:

### Step 4.1: Update `day24/nginx.conf`
1. Uncomment the HTTP-to-HTTPS redirect in the port 80 server block:
   ```nginx
   server {
       listen 80;
       server_name api.yourdomain.com;
       location /.well-known/acme-challenge/ {
           root /var/www/certbot;
       }
       location / {
           return 301 https://$host$request_uri;
       }
   }
   ```
2. In the port 443 server block, replace `yourdomain.com` with `api.yourdomain.com` and uncomment the block.

### Step 4.2: Reload Nginx Configuration (Zero-Downtime)
```bash
docker compose -f day24/docker-compose.prod.yml exec nginx nginx -s reload
```

### Step 4.3: Test HTTPS Endpoint
```bash
curl -I https://api.yourdomain.com/health
# Expected: HTTP/2 200 OK with strict-transport-security header
```

---

## 5. Automated Certificate Renewal (Systemd Timer / Cron)

Let's Encrypt certificates are valid for 90 days. Set up a bi-weekly renewal cron job:

```bash
# Open crontab:
crontab -e

# Add this line (runs at 03:00 on the 1st and 15th of each month):
0 3 1,15 * * docker run --rm -v shopzone_certbot_conf:/etc/letsencrypt -v shopzone_certbot_www:/var/www/certbot certbot/certbot renew --webroot -w /var/www/certbot && docker compose -f /home/ubuntu/shopzone/day24/docker-compose.prod.yml exec -T nginx nginx -s reload
```
