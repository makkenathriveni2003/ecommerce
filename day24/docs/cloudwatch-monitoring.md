# Day 24 – Task 9: Amazon CloudWatch Monitoring and Alarms

This guide explains how to monitor EC2 infrastructure metrics, collect memory and disk metrics via the CloudWatch Agent, stream Docker application logs, and configure alert alarms.

---

## 1. CloudWatch Metrics Architecture

By default, Amazon EC2 reports **hypervisor-level metrics** to CloudWatch every 5 minutes (or 1 minute with detailed monitoring):
- `CPUUtilization`
- `NetworkIn` / `NetworkOut`
- `DiskReadBytes` / `DiskWriteBytes`
- `StatusCheckFailed_Instance` / `StatusCheckFailed_System`

> [!NOTE]
> The EC2 hypervisor **cannot see inside the operating system**. Therefore, **RAM (Memory) Utilization** and **Filesystem Disk Usage** are NOT available by default. You must install the **Unified CloudWatch Agent** to collect them.

---

## 2. Installing the Unified CloudWatch Agent on EC2

### Step 2.1: Attach IAM Role to EC2
Ensure your EC2 instance has an IAM Role with `CloudWatchAgentServerPolicy` attached.

### Step 2.2: Install Agent Package on Ubuntu
```bash
sudo wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb
```

### Step 2.3: CloudWatch Agent Configuration (`/opt/aws/amazon-cloudwatch-agent/bin/config.json`)
```json
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "root"
  },
  "metrics": {
    "metrics_collected": {
      "mem": {
        "measurement": [
          "mem_used_percent"
        ]
      },
      "disk": {
        "measurement": [
          "used_percent"
        ],
        "resources": [
          "/"
        ]
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/nginx/access.log",
            "log_group_name": "/shopzone/production/nginx-access",
            "log_stream_name": "{instance_id}"
          },
          {
            "file_path": "/var/log/nginx/error.log",
            "log_group_name": "/shopzone/production/nginx-error",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
```

### Step 2.4: Start the Agent
```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/bin/config.json
```

---

## 3. Recommended CloudWatch Alarms & SNS Alerts

Create an **Amazon SNS (Simple Notification Service)** topic named `shopzone-devops-alerts` and subscribe your email address.

Configure the following alarms:

### Alarm 1: High CPU Utilization
- **Metric:** `AWS/EC2 > CPUUtilization`
- **Threshold:** `>= 80% for 2 consecutive 5-minute periods`
- **Action:** Send message to SNS `shopzone-devops-alerts`.
- **Reason:** Indicates runaway Celery background tasks or high web traffic requiring instance scale-up.

### Alarm 2: High Memory Utilization (OOM Risk)
- **Metric:** `CWAgent > mem_used_percent`
- **Threshold:** `>= 85% for 2 consecutive 1-minute periods`
- **Action:** Send message to SNS `shopzone-devops-alerts`.
- **Reason:** Prevents Linux kernel from abruptly killing PostgreSQL or ChromaDB.

### Alarm 3: Instance Status Check Failed (Hardware Failure)
- **Metric:** `AWS/EC2 > StatusCheckFailed`
- **Threshold:** `>= 1 for 2 consecutive periods`
- **Action:** Send message to SNS topic + **EC2 Action: Recover Instance**.

### Alarm 4: High HTTP 5xx Server Error Rate
- **Metric:** `AWS/ApplicationELB > HTTPCode_Target_5XX_Count`
- **Threshold:** `>= 10 errors over 5 minutes`
- **Action:** Send message to SNS `shopzone-devops-alerts`.

---

## 4. Verification in CloudWatch Console

Before marking alarms as active:
1. Open AWS Management Console > **CloudWatch > Metrics > All metrics**.
2. Select namespace `AWS/EC2` and verify `CPUUtilization` is actively plotting data points.
3. Select namespace `CWAgent` and verify `mem_used_percent` is reporting.
4. Select **CloudWatch > In alarm** to ensure all thresholds are configured in state `OK`.
