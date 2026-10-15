# Day 24 – Task 8: Elastic Load Balancing and EC2 Auto Scaling

This guide explains how AWS Elastic Load Balancing (Application Load Balancer) and EC2 Auto Scaling Groups work together to ensure high availability, automatic failover, and dynamic scaling for ShopZone.

---

## 1. High-Availability Architecture Overview

When migrating from a single EC2 instance to a multi-instance production environment:

```
                  Internet (Clients & Mobile)
                              │ (HTTPS : 443)
                              ▼
            [ Application Load Balancer (ALB) ]
            • SSL/TLS Termination via AWS ACM Certificate
            • Health Checking target instances at /health
            • Round-Robin Traffic Distribution
                              │
             ┌────────────────┴────────────────┐
             │                                 │
             ▼                                 ▼
   [ EC2 Instance #1 (AZ-a) ]       [ EC2 Instance #2 (AZ-b) ]
   • Docker / Nginx / Backend       • Docker / Nginx / Backend
             │                                 │
             └────────────────┬────────────────┘
                              │
                              ▼
            [ Amazon RDS Multi-AZ PostgreSQL ]
            [ Amazon ElastiCache Redis Cluster ]
```

---

## 2. Application Load Balancer (ALB) Setup

An ALB operates at Layer 7 (HTTP/HTTPS) of the OSI model:

### Key Components:
1. **Listeners:**
   - **Port 80 (HTTP):** Action: Redirect to Port 443 (HTTPS) with status code `HTTP_301`.
   - **Port 443 (HTTPS):** Uses a free SSL certificate issued by **AWS Certificate Manager (ACM)**. Forwards to Target Group.
2. **Target Group (`shopzone-tg`):**
   - **Target Type:** Instances
   - **Protocol:** HTTP (Port 80 to Nginx on EC2)
   - **Health Check Path:** `/health`
   - **Health Check Interval:** `15 seconds`
   - **Healthy Threshold:** `2 consecutive passes`
   - **Unhealthy Threshold:** `3 consecutive failures`
   - **Matcher:** `200`

---

## 3. EC2 Auto Scaling Group (ASG)

An Auto Scaling Group automatically provisions or terminates EC2 instances in response to changing traffic demands or server hardware failures.

### Key Components:
1. **Launch Template (`shopzone-lt`):**
   - AMI: Ubuntu 24.04 LTS with Docker pre-installed.
   - Instance Type: `t3.medium`
   - IAM Instance Profile: `ShopZoneEC2Role`
   - Security Group: Accepts HTTP only from the ALB security group.
   - User Data script: Clones code from GitHub and runs `docker compose -f day24/docker-compose.prod.yml up -d`.
2. **Capacity Planning:**
   - **Minimum Capacity:** `2` (Ensures zero downtime across two Availability Zones)
   - **Desired Capacity:** `2`
   - **Maximum Capacity:** `6` (Safety ceiling against runaway cloud costs)

### Scaling Policies:

#### Target Tracking Scaling Policy (Recommended)
- **Metric:** `Average CPU Utilization`
- **Target Value:** `70%`
- **Behavior:**
  - If CPU > 70% for 3 minutes -> Spin up 1 new EC2 instance.
  - If CPU < 40% for 15 minutes -> Terminate 1 instance (scale down).

---

## 4. Database & State Considerations for Auto Scaling

> [!CAUTION]
> **Never scale database containers inside an EC2 Auto Scaling Group!**
> If an instance is terminated by the Auto Scaling Group, any local PostgreSQL or SQLite database file stored on its disk will be lost.

When enabling Auto Scaling:
1. **Database:** Move PostgreSQL out of local Docker into **Amazon RDS for PostgreSQL**.
2. **Cache & Celery Broker:** Move Redis out of local Docker into **Amazon ElastiCache for Redis**.
3. **Stateless Backend:** Keep the FastAPI backend completely stateless so any incoming request can hit any of the running EC2 instances interchangeably.
