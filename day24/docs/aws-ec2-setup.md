# Day 24 – Task 1: AWS EC2 Setup and Deployment Guide

This guide walks you through deploying the ShopZone FastAPI backend stack to an AWS EC2 instance using Ubuntu Linux, Docker, and Docker Compose.

---

## 1. Instance Architecture & Sizing Recommendation

For the ShopZone multi-container backend stack (FastAPI + Celery + PostgreSQL + Redis + ChromaDB + Nginx):

| Specification | Free Tier Eligible (Dev/Test) | Recommended Production |
| :--- | :--- | :--- |
| **Instance Type** | `t2.micro` (1 vCPU, 1 GB RAM) or `t3.micro` | `t3.medium` or `t3.large` (2 vCPU, 4–8 GB RAM) |
| **Operating System** | Ubuntu Server 24.04 LTS (x86_64) | Ubuntu Server 24.04 LTS (x86_64) |
| **Storage (EBS)** | 30 GB gp3 SSD (Free Tier max) | 50–100 GB gp3 SSD |
| **Public IP** | Elastic IP (free while attached to running instance) | Elastic IP attached to ALB or EC2 |

> [!NOTE]
> ChromaDB and Celery workers are memory-intensive. On a `t2.micro` (1 GB RAM), you **must enable at least 2 GB of swap memory** to prevent Linux OOM (Out Of Memory) killer from terminating PostgreSQL or ChromaDB.

---

## 2. Security Group Configuration (Firewall Rules)

Create a dedicated Security Group named `shopzone-ec2-sg`. Configure the following inbound and outbound rules:

### Inbound Rules (Traffic Allowed into EC2)

| Type | Protocol | Port Range | Source | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **SSH** | TCP | `22` | `My IP` (e.g. `203.0.113.4/32`) | Secure terminal access. **Never use `0.0.0.0/0`!** |
| **HTTP** | TCP | `80` | `0.0.0.0/0` (Anywhere IPv4) | Web traffic & Certbot ACME challenge |
| **HTTPS** | TCP | `443` | `0.0.0.0/0` (Anywhere IPv4) | Encrypted SSL/TLS traffic |
| **Custom TCP** | TCP | `9090` | `My IP` (Optional) | Prometheus metrics dashboard (restricted) |

> [!IMPORTANT]
> **Do NOT open ports 5432 (Postgres), 6379 (Redis), or 8000 (Backend) to `0.0.0.0/0`**.
> In our Docker architecture, these ports are kept internal to the Docker bridge network. Only Nginx on ports 80 and 443 communicates with the outside world.

### Outbound Rules (Traffic Allowed from EC2 to Internet)

| Type | Protocol | Port Range | Destination | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **All Traffic** | All | All | `0.0.0.0/0` | Package updates, Docker image pulls, LLM API calls |

---

## 3. SSH Key Pair Generation and Secure Connection

### Step 3.1: Generate a Local SSH Key Pair (if not already created)

On your local machine (PowerShell or Bash):

```bash
# Generate a modern ED25519 key pair (recommended over RSA)
ssh-keygen -t ed25519 -C "shopzone-devops" -f ~/.ssh/shopzone_ec2_key
```

### Step 3.2: Secure Key Permissions

On Windows PowerShell:
```powershell
# Ensure only your user has access to the private key
icacls ~/.ssh/shopzone_ec2_key /inheritance:r
icacls ~/.ssh/shopzone_ec2_key /grant:r "$($env:USERNAME):(R)"
```

On Linux / macOS:
```bash
chmod 400 ~/.ssh/shopzone_ec2_key
```

### Step 3.3: Connect via SSH

```bash
ssh -i ~/.ssh/shopzone_ec2_key ubuntu@<EC2_PUBLIC_IP_OR_ELASTIC_IP>
```

---

## 4. EC2 Instance Provisioning Script

Run these commands on your fresh Ubuntu EC2 instance:

```bash
# 1. Update OS packages
sudo apt-get update && sudo apt-get upgrade -y

# 2. Configure 2 GB Swap Memory (protects against low-memory crashes)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 3. Install Docker Engine and Docker Compose Plugin
sudo apt-get install -y ca-certificates curl gnupg lsb-release
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 4. Add 'ubuntu' user to docker group (avoid needing sudo for docker commands)
sudo usermod -aG docker ubuntu
newgrp docker

# Verify installation
docker --version
docker compose version
```

---

## 5. Cloning and Deploying the Stack

```bash
# 1. Clone repository onto EC2
git clone https://github.com/your-username/shopzone.git
cd shopzone

# 2. Copy production environment file
cp day24/.env.example .env

# 3. Edit .env with strong, production-grade secrets
nano .env

# Critical variables to fill:
# - POSTGRES_PASSWORD=...
# - REDIS_PASSWORD=...
# - JWT_SECRET_KEY=... (generate with: openssl rand -hex 32)
# - GEMINI_API_KEY=... / GROQ_API_KEY=...
# - FRONTEND_ORIGINS=https://your-frontend.vercel.app

# 4. Launch the Docker Compose stack using the Day 24 production file
docker compose -f day24/docker-compose.prod.yml up -d --build

# 5. Check running containers
docker compose -f day24/docker-compose.prod.yml ps

# 6. Verify health endpoint
curl -i http://localhost/health
```

---

## 6. Zero-Downtime Application Updates

When you push new code to Git:

```bash
cd ~/shopzone
git pull origin main
docker compose -f day24/docker-compose.prod.yml build backend celery_worker
docker compose -f day24/docker-compose.prod.yml up -d --no-deps backend celery_worker
```
