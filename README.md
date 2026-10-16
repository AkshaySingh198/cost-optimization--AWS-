# 💰 AWS Cost Optimization Automation

An automated, serverless FinOps solution built with Python, Boto3, and AWS Lambda to detect, report, and remediate orphaned or underutilized AWS resources, delivering real-time cost savings notifications directly to Slack.

---

## 🏗️ Architecture Overview

```text
┌─────────────────────────┐
│   Amazon EventBridge    │  (Scheduled Daily Cron)
└────────────┬────────────┘
             │ Triggers
             ▼
┌─────────────────────────┐
│       AWS Lambda        │  (Python 3.11 Execution)
│   (src/lamda.py)        │
└──────┬───────────┬──────┘
       │           │
       │ Scans     │ Dispatches Report
       ▼           ▼
┌──────────────┐ ┌──────────────────────────────────────┐
│ AWS Services │ │ Slack Channel (#aws-cost-alerts)     │
│ • EC2 / CW   │ │ (Via Webhook from SSM Parameter Store)│
│ • EBS        │ └──────────────────────────────────────┘
│ • Elastic IP │
│ • Tagging    │
└──────────────┘
```

---

## 🔍 Waste Detection Modules

1. **Unattached EBS Volumes**: Scans for EBS volumes in `available` state incurring detached storage costs. In remediation mode, automatically snapshots before deletion.
2. **Old EBS Snapshots**: Identifies snapshots older than 30 days whose parent volumes no longer exist or are unattached.
3. **Unassociated Elastic IPs**: Detects allocated public IPv4 addresses with no network association ($0.005/hr charge).
4. **Idle EC2 Instances**: Queries Amazon CloudWatch for instances whose 7-day average CPU utilization is below 5%.
5. **Untagged Resources**: Uses the AWS Resource Groups Tagging API to audit resources missing mandatory tags (`Owner`, `Environment`, `Project`).

---

## 🛡️ Safety & FinOps Features

* **Dry-Run by Default**: Safe-mode inspection that detects and calculates monthly savings without making destructive changes.
* **Tag Protection**: Resources tagged `do-not-delete` are explicitly excluded from deletion.
* **Zero Secret Exposure**: Slack Webhook URLs are stored encrypted in **AWS Systems Manager (SSM) Parameter Store**.
* **Zero-Cost Architecture**: Built on AWS Serverless Free Tier (Lambda + EventBridge + SSM + CloudWatch).

---

## 📁 Repository Structure

```text
cost-optimizer/
├── src/
│   ├── detection/
│   │   ├── ebs.py           # Unattached volumes & old snapshot checks
│   │   ├── eip.py           # Unassociated Elastic IP checks
│   │   ├── EC2_IDLE.py      # CloudWatch CPU utilization checks
│   │   └── TAG.py           # Resource Groups Tagging API compliance
│   ├── notifier/
│   │   └── slack.py         # Block Kit formatter & SSM Webhook integration
│   └── lamda.py             # Lambda handler orchestrator
├── terraform/               # Infrastructure as Code (EventBridge, Lambda, IAM)
├── tests/                   # Local unit tests (Pytest + Moto)
├── .gitignore               # Security & runtime ignore rules
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
* AWS CLI v2 configured with IAM credentials (`aws configure`)
* Python 3.11+
* Slack Incoming Webhook URL

### 1. Store Slack Webhook in AWS SSM
```bash
aws ssm put-parameter \
  --name "/cost-optimizer/slack-webhook" \
  --value "https://hooks.slack.com/services/YOUR/WEBHOOK/URL" \
  --type "SecureString" \
  --overwrite
```

### 2. Run Locally
```bash
python -c "import sys; sys.path.insert(0, 'src'); from lamda import lambda_handler; print(lambda_handler({}, None))"
```
