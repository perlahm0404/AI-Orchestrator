---
# Document Metadata
doc-id: "g-plan-aws-cost-analysis"
title: "AWS Cost Analysis: Lambda-Only Infrastructure"
created: "2026-01-10"
updated: "2026-01-10"
author: "Claude AI"
status: "active"

# Compliance Metadata
compliance:
  soc2:
    controls: ["CC7.3"]
    evidence-type: "documentation"
    retention-period: "7-years"
  iso27001:
    controls: ["A.12.1.1"]
    classification: "internal"
    review-frequency: "quarterly"

# Project Context
project: "ai-orchestrator"
domain: "operator"
relates-to: ["ADR-003", "cm-plan-lambda-migration"]

# Change Control
version: "1.0"
---

# AWS Cost Analysis: Lambda-Only Infrastructure

**Date:** 2026-01-10
**Environment:** Production (CredentialMate)
**Deployment Model:** Lambda + Serverless Services

---

## Cost Breakdown by Service

### 1. Lambda Functions ⚡

**Three Lambda Functions:**
- **BackendApiFunction** (FastAPI wrapper, 512MB, 30s timeout)
- **WorkerFunction** (Document processing, 1024MB, 300s timeout)
- **ReportWorkerFunction** (PDF/CSV generation, 2048MB, 300s timeout)

#### Pricing Model
- **Request charge**: $0.20 per 1M requests
- **Compute charge**: $0.0000166667 per GB-second

#### Usage Estimates (Monthly)

**BackendApiFunction** (API requests):
- Traffic: 100,000 API requests/month (MVP startup)
- Avg duration: 500ms
- Memory: 512MB (0.5GB)
- GB-seconds: 100,000 × 0.5s × 0.5GB = 25,000 GB-seconds

**WorkerFunction** (Document processing):
- Traffic: 1,000 documents/month
- Avg duration: 60s (Bedrock AI parsing)
- Memory: 1024MB (1GB)
- GB-seconds: 1,000 × 60s × 1GB = 60,000 GB-seconds

**ReportWorkerFunction** (Report generation):
- Traffic: 500 reports/month
- Avg duration: 120s (PDF generation)
- Memory: 2048MB (2GB)
- GB-seconds: 500 × 120s × 2GB = 120,000 GB-seconds

#### Lambda Cost Calculation

```
Total Requests: 101,500 requests/month
Request cost: (101,500 / 1,000,000) × $0.20 = $0.02

Total GB-seconds: 25,000 + 60,000 + 120,000 = 205,000 GB-seconds
Compute cost: 205,000 × $0.0000166667 = $3.42

TOTAL LAMBDA: $3.44/month
```

**With Free Tier** (first year):
- Free: 1M requests/month + 400,000 GB-seconds/month
- Your usage: 101,500 requests + 205,000 GB-seconds
- **Cost with free tier: $0/month** (well under limits!)

---

### 2. API Gateway 🌐

**Type:** REST API (not HTTP API, due to CORS requirements)

**Pricing:**
- $3.50 per million API calls
- $0.09/GB data transfer out

**Usage:**
- API requests: 100,000/month
- Avg response size: 10KB
- Data transfer: 100,000 × 10KB = 1GB

**Cost:**
```
API calls: (100,000 / 1,000,000) × $3.50 = $0.35
Data transfer: 1GB × $0.09 = $0.09

TOTAL API GATEWAY: $0.44/month
```

---

### 3. SQS Queues 📬

**Queues:**
- WorkerQueue (FIFO)
- DeadLetterQueue (FIFO)
- ReportQueue (FIFO) - new for ADR-001
- ReportDeadLetterQueue (FIFO) - new for ADR-001

**Pricing:**
- FIFO queues: $0.50 per 1M requests (after free tier)
- Standard queues: $0.40 per 1M requests

**Usage:**
- Worker queue: 1,000 messages/month
- Report queue: 500 messages/month
- DLQ messages: ~50/month (failures)
- Total: ~1,550 messages/month

**Free Tier:** 1M requests/month (covers everything!)

**Cost:**
```
TOTAL SQS: $0/month (within free tier)
```

---

### 4. RDS PostgreSQL 🗄️

**Instance:** db.t4g.micro (2 vCPU, 1GB RAM)

**Pricing:**
- Single-AZ: $0.016/hour = $11.68/month
- Multi-AZ (HA): $0.032/hour = $23.36/month
- Storage (GP3): $0.115/GB-month
- Backup storage: First 20GB free, then $0.095/GB-month

**Usage:**
- Storage: 20GB (MVP database)
- Backups: ~5GB (compressed)

**Cost:**
```
Instance (Single-AZ): $11.68/month
Storage (20GB GP3): 20 × $0.115 = $2.30/month
Backup: $0 (within free 20GB)

TOTAL RDS: $13.98/month
```

**⚠️ This cost EXISTS TODAY (shared between EC2 and Lambda models)**

---

### 5. S3 Storage 🪣

**Buckets:**
- `credmate-documents-prod` (provider documents)
- `credmate-reports-prod` (temporary reports, 24hr lifecycle)

**Pricing:**
- Storage: $0.023/GB-month (Standard)
- PUT requests: $0.005 per 1,000 requests
- GET requests: $0.0004 per 1,000 requests

**Usage:**
- Documents: 10GB stored, 100 uploads/month, 500 downloads/month
- Reports: 2GB average (auto-deleted after 24h), 500 uploads/month, 500 downloads/month

**Cost:**
```
Storage: (10GB + 2GB) × $0.023 = $0.28/month
PUT requests: 600 × $0.005/1000 = $0.003/month
GET requests: 1,000 × $0.0004/1000 = $0.0004/month

TOTAL S3: $0.28/month
```

**⚠️ This cost EXISTS TODAY (shared between EC2 and Lambda models)**

---

### 6. VPC Endpoints 🔌

**Lambda in VPC needs access to:**
- Secrets Manager
- S3
- SQS
- DynamoDB (if using DynamoDB for sessions)

**Option A: NAT Gateway** (simpler, higher cost)
- $0.045/hour = $32.85/month
- $0.045/GB data processed = ~$5/month
- **Total: $37.85/month**

**Option B: VPC Endpoints** (complex, lower cost)
- Interface endpoints: $0.01/hour each = $7.30/month per endpoint
- S3 Gateway endpoint: Free!
- Needed: Secrets Manager, SQS, DynamoDB (if used)
- **Total: ~$21.90/month (3 endpoints)**

**Recommended: Option B (VPC Endpoints)**

**Cost:**
```
Secrets Manager endpoint: $7.30/month
SQS endpoint: $7.30/month
DynamoDB endpoint: $7.30/month (if using DynamoDB sessions)
S3 Gateway endpoint: $0/month

TOTAL VPC ENDPOINTS: $21.90/month
```

**⚠️ NEW COST - Lambda-specific**

---

### 7. Secrets Manager 🔐

**Secrets:**
- Combined secret (DB + JWT + Redis + encryption keys)
- ~4 secrets total

**Pricing:**
- $0.40 per secret per month
- $0.05 per 10,000 API calls

**Usage:**
- 4 secrets × $0.40 = $1.60/month
- API calls: ~50,000/month (Lambda cold starts) = $0.25/month

**Cost:**
```
Secret storage: $1.60/month
API calls: $0.25/month

TOTAL SECRETS MANAGER: $1.85/month
```

**⚠️ This cost EXISTS TODAY (shared between EC2 and Lambda models)**

---

### 8. KMS Keys 🔑

**Keys:**
- Secrets encryption key
- S3 reports encryption key
- Database encryption key

**Pricing:**
- $1.00 per key per month
- $0.03 per 10,000 requests

**Usage:**
- 3 keys × $1.00 = $3.00/month
- Requests: ~100,000/month = $0.30/month

**Cost:**
```
Key storage: $3.00/month
Requests: $0.30/month

TOTAL KMS: $3.30/month
```

**⚠️ This cost EXISTS TODAY (shared between EC2 and Lambda models)**

---

### 9. CloudWatch Logs & Monitoring 📊

**Log Groups:**
- `/aws/lambda/BackendApiFunction`
- `/aws/lambda/WorkerFunction`
- `/aws/lambda/ReportWorkerFunction`
- `/aws/apigateway/credmate-prod`
- DLQ alarms

**Pricing:**
- Ingestion: $0.50/GB
- Storage: $0.03/GB-month (after 5GB free)
- Custom metrics: $0.30 per metric

**Usage:**
- Logs: ~2GB/month ingestion, 10GB stored (7-day retention)
- Metrics: 10 custom metrics (DLQ alarms, Lambda errors)

**Cost:**
```
Log ingestion: 2GB × $0.50 = $1.00/month
Log storage: (10GB - 5GB free) × $0.03 = $0.15/month
Custom metrics: 10 × $0.30 = $3.00/month

TOTAL CLOUDWATCH: $4.15/month
```

**⚠️ NEW COST - Lambda generates more logs than EC2**

---

### 10. DynamoDB (Sessions) 🗂️

**Table:** SessionsTable (JWT session storage)

**Pricing (On-Demand):**
- Write requests: $1.25 per million
- Read requests: $0.25 per million
- Storage: $0.25/GB-month

**Usage:**
- Writes: 10,000 sessions/month
- Reads: 100,000 session checks/month
- Storage: 0.5GB

**Cost:**
```
Writes: 10,000 / 1,000,000 × $1.25 = $0.01/month
Reads: 100,000 / 1,000,000 × $0.25 = $0.03/month
Storage: 0.5GB × $0.25 = $0.13/month

TOTAL DYNAMODB: $0.17/month
```

**⚠️ NEW COST - Lambda-specific (EC2 used Redis)**

---

### 11. Route53 🌍

**Hosted Zone:** credentialmate.com

**Pricing:**
- Hosted zone: $0.50/month
- Queries: $0.40 per million (first 1B queries)

**Usage:**
- DNS queries: 500,000/month

**Cost:**
```
Hosted zone: $0.50/month
Queries: 0.5M × $0.40/1M = $0.20/month

TOTAL ROUTE53: $0.70/month
```

**⚠️ This cost EXISTS TODAY (shared between EC2 and Lambda models)**

---

### 12. Data Transfer 📡

**Pricing:**
- Data out to internet: $0.09/GB (first 10TB)
- Data in: Free

**Usage:**
- API responses: 1GB/month
- Document downloads: 2GB/month
- Total: 3GB/month

**Cost:**
```
Data transfer out: 3GB × $0.09 = $0.27/month

TOTAL DATA TRANSFER: $0.27/month
```

---

## Total Monthly Cost Summary

### NEW Lambda-Only Costs

| Service | Monthly Cost | Notes |
|---------|--------------|-------|
| **Lambda Functions** | $0.00 | Within free tier (first year) |
| API Gateway | $0.44 | 100K requests |
| SQS Queues | $0.00 | Within free tier |
| VPC Endpoints | $21.90 | **REQUIRED for Lambda** |
| CloudWatch Logs | $4.15 | More verbose than EC2 |
| DynamoDB Sessions | $0.17 | Replaces Redis |
| Data Transfer | $0.27 | |
| **SUBTOTAL (NEW)** | **$26.93/month** | |

### Shared Costs (Exist in Both Models)

| Service | Monthly Cost | Notes |
|---------|--------------|-------|
| RDS PostgreSQL | $13.98 | db.t4g.micro |
| S3 Storage | $0.28 | Documents + Reports |
| Secrets Manager | $1.85 | 4 secrets |
| KMS Keys | $3.30 | 3 keys |
| Route53 | $0.70 | DNS hosting |
| **SUBTOTAL (SHARED)** | **$20.11/month** | |

### **TOTAL LAMBDA INFRASTRUCTURE: $47.04/month**

---

## Cost Comparison: EC2 vs Lambda

### EC2 Model (Current)

| Service | Monthly Cost |
|---------|--------------|
| EC2 t3.medium | $30.48 |
| Elastic IP | $3.60 |
| EBS Storage (30GB) | $3.00 |
| **EC2 Subtotal** | **$37.08** |
| Shared Infrastructure | $20.11 |
| **TOTAL EC2** | **$57.19/month** |

### Lambda Model (Proposed)

| Service | Monthly Cost |
|---------|--------------|
| Lambda + API Gateway + SQS | $0.44 |
| VPC Endpoints | $21.90 |
| CloudWatch Logs | $4.15 |
| DynamoDB | $0.17 |
| Data Transfer | $0.27 |
| **Lambda Subtotal** | **$26.93** |
| Shared Infrastructure | $20.11 |
| **TOTAL LAMBDA** | **$47.04/month** |

---

## Cost Comparison Summary

| Metric | EC2 | Lambda | Difference |
|--------|-----|--------|------------|
| **Monthly Cost** | $57.19 | $47.04 | **-$10.15 (18% savings)** |
| **Fixed Costs** | $37.08 | $26.93 | Lower baseline |
| **Scales with traffic?** | No | Yes | Lambda cheaper at low traffic |
| **Free tier eligible?** | No | Yes | First year ~$3-4/month cheaper |

---

## Cost Sensitivity Analysis

### Scenario 1: Low Traffic (Current MVP)
- 100K requests/month
- **Lambda: $47.04/month** ✅ Better
- **EC2: $57.19/month**

### Scenario 2: Medium Traffic (Growing)
- 1M requests/month
- Lambda: ~$52/month (compute costs increase)
- EC2: $57.19/month ✅ Still better with Lambda

### Scenario 3: High Traffic (Established)
- 10M requests/month
- Lambda: ~$85/month (compute + API Gateway)
- EC2: $77/month (need t3.large) ✅ EC2 becomes competitive

### Scenario 4: Very High Traffic
- 50M+ requests/month
- Lambda: $200+/month
- EC2: $150/month ✅ EC2 wins at scale

---

## Key Cost Drivers for Lambda

### Top 3 Costs:

1. **VPC Endpoints: $21.90/month (47% of Lambda costs)**
   - REQUIRED for Lambda to access Secrets Manager, SQS in private subnets
   - Alternative: NAT Gateway ($37.85/month) - even more expensive
   - No way to avoid this if Lambda needs VPC access

2. **CloudWatch Logs: $4.15/month (9%)**
   - Lambda generates verbose logs
   - Can reduce with shorter retention (7 days → 3 days)

3. **DynamoDB: $0.17/month (0.4%)**
   - Cheap, scales automatically
   - Replaces Redis ($0 in EC2 via Docker)

---

## Cost Optimization Opportunities

### Immediate Savings (Year 1)

**Use AWS Free Tier:**
- Lambda: 1M requests + 400K GB-seconds/month = **~$3.44/month savings**
- API Gateway: Not in free tier
- Total first-year savings: **~$41/year**

### Long-Term Optimizations

**1. Lambda Compute Savings Plan** (after traffic stabilizes)
- 1-year commitment: 17% discount
- 3-year commitment: 28% discount
- Savings: ~$1/month (not worth it at current traffic)

**2. Reserved Capacity RDS** (if staying with RDS)
- 1-year reserved: 35% discount = $9.08/month (save $4.90/month)
- 3-year reserved: 60% discount = $5.59/month (save $8.39/month)
- **Recommended: 1-year reserved** = **$58.80/year savings**

**3. S3 Intelligent Tiering** (for old documents)
- Auto-moves infrequent documents to cheaper tiers
- Potential: $0.05/month savings (minimal at 10GB)

**4. Reduce CloudWatch Retention**
- 7 days → 3 days: Save $0.08/month
- Not worth the complexity

---

## Hidden Costs & Considerations

### ⚠️ Costs NOT Included Above

**1. Bedrock AI (Document Parsing)**
- Claude Sonnet: $3 per 1M input tokens, $15 per 1M output tokens
- Usage: 1,000 docs/month × 2K tokens avg = 2M tokens/month
- **Cost: ~$6-10/month** (depends on doc complexity)
- **⚠️ This cost EXISTS TODAY (shared between both models)**

**2. SNS/SES (Email Notifications)**
- Not included in SAM template (if needed)
- SES: $0.10 per 1,000 emails
- Potential: $1-2/month

**3. WAF (Web Application Firewall)** - Optional
- $5/month + $1 per rule
- Not recommended for MVP (adds $5-10/month)

**4. CloudFront CDN** - Optional
- $0.085/GB data transfer
- Not needed for MVP API (adds $5-15/month)

---

## Final Recommendation

### Lambda is Cost-Effective IF:
- ✅ Traffic < 5M requests/month
- ✅ Spiky/unpredictable load
- ✅ Want auto-scaling
- ✅ Want zero-downtime deploys
- ✅ Don't mind VPC endpoint costs

### EC2 is Better IF:
- ✅ Traffic > 10M requests/month (consistent)
- ✅ Need persistent processes (background jobs)
- ✅ Want full control over infrastructure
- ✅ Already managing EC2 (operational knowledge)

---

## Bottom Line

**Lambda Monthly Cost: $47.04/month**

**Breakdown:**
- Lambda compute + API Gateway: $0.44
- VPC Endpoints: $21.90 (unavoidable)
- CloudWatch: $4.15
- DynamoDB: $0.17
- Data transfer: $0.27
- Shared (RDS, S3, KMS, etc.): $20.11

**vs EC2: $57.19/month**

**Savings: $10.15/month (18%)**
**Annual savings: $121.80/year**

**Recommendation: Proceed with Lambda** ✅
- Cheaper at current traffic levels
- Better scalability
- Simpler operations (no server management)
- Free tier benefits first year

**Watch out for:** VPC endpoint costs are unavoidable at $21.90/month.
