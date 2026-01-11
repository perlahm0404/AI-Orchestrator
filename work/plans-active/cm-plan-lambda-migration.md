---
# Document Metadata
doc-id: "cm-plan-lambda-migration"
title: "Lambda-Only Infrastructure Migration Plan"
created: "2026-01-10"
updated: "2026-01-10"
author: "Claude AI"
status: "active"

# Compliance Metadata
compliance:
  soc2:
    controls: ["CC7.3", "CC8.1"]
    evidence-type: "documentation"
    retention-period: "7-years"
  iso27001:
    controls: ["A.12.1.1", "A.14.2.2"]
    classification: "confidential"
    review-frequency: "quarterly"

# Project Context
project: "credentialmate"
domain: "operator"
relates-to: ["ADR-003"]

# Change Control
version: "1.0"
---

# Lambda-Only Infrastructure Migration Plan

**Date:** 2026-01-10
**Objective:** Remove EC2 infrastructure and establish Lambda-only deployment
**Status:** Planning Phase

---

## Current Architecture

### Terraform (infra/iac/)
```
✅ KEEP - Shared Infrastructure:
- VPC (modules/vpc)
- RDS PostgreSQL (modules/rds)
- S3 Buckets (modules/s3, modules/s3-reports)
- KMS Keys (modules/kms)
- Secrets Manager (modules/secrets)
- Route53 DNS (modules/route53)
- IAM Roles (modules/iam)
- Security Groups (modules/security_groups)
- CloudWatch (modules/cloudwatch)

❌ REMOVE - EC2-Specific:
- EC2 Module (modules/ec2/)
- EC2 Security Groups (partial)
- EC2 IAM Roles/Profiles (partial)
- Elastic IP
```

### SAM/CloudFormation (infra/lambda/)
```
✅ EXISTS - Lambda Application:
- template.yaml (main SAM template)
- BackendApiFunction (FastAPI + Mangum)
- WorkerFunction (async job processor)
- SQS Queue + Dead Letter Queue
- API Gateway
- Lambda IAM roles
- VPC configuration for RDS access
```

---

## Migration Steps

### Phase 1: Infrastructure Cleanup (Terraform)

**1.1 Remove EC2 Module Reference**
File: `infra/iac/main.tf`
- Remove lines 258-296 (module "ec2" block)
- Remove EC2 outputs (lines 431-441)
- Remove EC2 dependencies in Route53

**1.2 Delete EC2 Module**
```bash
rm -rf infra/iac/modules/ec2/
```

**1.3 Update Security Groups**
File: `infra/iac/modules/security_groups/main.tf`
- Remove EC2-specific security group
- Keep Lambda/RDS security groups

**1.4 Update IAM Module**
File: `infra/iac/modules/iam/main.tf`
- Remove EC2 instance profile
- Remove EC2 IAM role
- Keep Lambda execution roles

**1.5 Remove EC2 from Variables**
File: `infra/iac/variables.tf`
- Remove EC2 instance type variables
- Remove EC2 key pair variables
- Remove any EC2-specific config

---

### Phase 2: Lambda Infrastructure Verification (SAM)

**2.1 Verify SAM Template Completeness**
File: `infra/lambda/template.yaml`

Check for:
- ✅ BackendApiFunction (FastAPI wrapper)
- ✅ WorkerFunction (async job processing)
- ✅ SQS WorkerQueue
- ✅ SQS DeadLetterQueue
- ✅ API Gateway
- ✅ Lambda execution roles
- ✅ VPC configuration
- ✅ Environment variables
- ❓ S3 Reports bucket access (verify)
- ❓ EventBridge rules for scheduled tasks

**2.2 Add Missing Lambda Resources**

**a) S3 Reports Access**
```yaml
# Add to LambdaExecutionRole policies
- PolicyName: CredMateReportsS3Access
  PolicyDocument:
    Version: '2012-10-17'
    Statement:
      - Effect: Allow
        Action:
          - s3:GetObject
          - s3:PutObject
          - s3:DeleteObject
        Resource:
          - !Sub arn:aws:s3:::${Environment}-credmate-reports/*
      - Effect: Allow
        Action:
          - kms:Decrypt
          - kms:Encrypt
          - kms:GenerateDataKey
        Resource: !Ref ReportsKmsKeyArn  # From Terraform output
```

**b) Report Worker Lambda Function**
```yaml
ReportWorkerFunction:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: functions/report-worker/
    Handler: handler.lambda_handler
    Runtime: python3.11
    MemorySize: 2048  # PDF generation needs more memory
    Timeout: 300      # 5 minutes for large reports
    Role: !GetAtt LambdaExecutionRole.Arn
    VpcConfig:
      SecurityGroupIds:
        - !Ref LambdaSecurityGroup
      SubnetIds: !Ref PrivateSubnetIds
    Environment:
      Variables:
        S3_REPORTS_BUCKET: !Sub ${Environment}-credmate-reports
        REPORTS_KMS_KEY_ID: !Ref ReportsKmsKeyArn
    Events:
      SQSEvent:
        Type: SQS
        Properties:
          Queue: !GetAtt ReportQueue.Arn
          BatchSize: 1
```

**c) Report SQS Queue**
```yaml
ReportQueue:
  Type: AWS::SQS::Queue
  Properties:
    QueueName: !Sub ${Environment}-credmate-report-queue
    VisibilityTimeout: 300  # Match Lambda timeout
    MessageRetentionPeriod: 86400  # 24 hours
    RedrivePolicy:
      deadLetterTargetArn: !GetAtt ReportDeadLetterQueue.Arn
      maxReceiveCount: 3

ReportDeadLetterQueue:
  Type: AWS::SQS::Queue
  Properties:
    QueueName: !Sub ${Environment}-credmate-report-dlq
    MessageRetentionPeriod: 1209600  # 14 days
```

---

### Phase 3: Deployment Workflow

**3.1 Terraform Deployment (Shared Infrastructure)**
```bash
# Deploy shared infrastructure (VPC, RDS, S3, KMS, etc.)
cd infra/iac
terraform init
terraform plan
terraform apply

# Export outputs for SAM
terraform output -json > outputs.json
```

**3.2 SAM Deployment (Lambda Functions)**
```bash
# Build Lambda functions
cd infra/lambda
sam build

# Deploy to AWS
sam deploy \
  --guided \
  --stack-name credmate-lambda-${ENV} \
  --parameter-overrides \
    Environment=${ENV} \
    VpcId=$(jq -r '.vpc_id.value' ../iac/outputs.json) \
    PrivateSubnetIds=$(jq -r '.private_subnet_ids.value | join(",")' ../iac/outputs.json) \
    RdsSecurityGroupId=$(jq -r '.rds_security_group_id.value' ../iac/outputs.json) \
    CombinedSecretArn=$(jq -r '.combined_secret_arn.value' ../iac/outputs.json) \
    ReportsKmsKeyArn=$(jq -r '.reports_kms_key_arn.value' ../iac/outputs.json)
```

**3.3 Create Deployment Script**
File: `deploy-lambda.sh`
```bash
#!/bin/bash
set -e

ENV=${1:-dev}
echo "🚀 Deploying CredentialMate to Lambda (${ENV})"

# Step 1: Deploy Terraform infrastructure
echo "📦 Deploying shared infrastructure..."
cd infra/iac
terraform workspace select ${ENV} || terraform workspace new ${ENV}
terraform apply -auto-approve
terraform output -json > outputs.json

# Step 2: Build Lambda functions
echo "🔨 Building Lambda functions..."
cd ../lambda
sam build --use-container

# Step 3: Deploy Lambda stack
echo "☁️  Deploying Lambda functions..."
sam deploy \
  --stack-name credmate-lambda-${ENV} \
  --parameter-overrides \
    Environment=${ENV} \
    VpcId=$(jq -r '.vpc_id.value' ../iac/outputs.json) \
    PrivateSubnetIds=$(jq -r '.private_subnet_ids.value | join(",")' ../iac/outputs.json) \
    RdsSecurityGroupId=$(jq -r '.rds_security_group_id.value' ../iac/outputs.json) \
    CombinedSecretArn=$(jq -r '.combined_secret_arn.value' ../iac/outputs.json)

echo "✅ Deployment complete!"
sam list endpoints --stack-name credmate-lambda-${ENV}
```

---

### Phase 4: Application Code Updates

**4.1 Remove Celery Dependencies**
File: `apps/backend-api/requirements.txt`
```diff
- celery[redis]>=5.3.4
- redis>=5.0.0
```

**4.2 Remove Celery Config Files**
```bash
find apps/backend-api -name "celeryconfig.py" -delete
find apps/backend-api -name "celery_app.py" -delete
find apps/worker-tasks -name "celery*.py" -delete
```

**4.3 Update Report Generation to Use SQS**
File: `apps/backend-api/src/contexts/reports/services/report_service.py`

**Before (Celery):**
```python
from celery_app import celery

@celery.task
def generate_report(job_id: str):
    # Generate report
    pass

# Trigger
generate_report.delay(job_id)
```

**After (SQS + Lambda):**
```python
import boto3
import json

sqs = boto3.client('sqs')

def queue_report_generation(job_id: str):
    """Queue report generation job to SQS."""
    sqs.send_message(
        QueueUrl=os.getenv('REPORT_QUEUE_URL'),
        MessageBody=json.dumps({
            'job_id': job_id,
            'timestamp': datetime.utcnow().isoformat()
        })
    )
```

---

### Phase 5: Docker/Docker-Compose Cleanup

**5.1 Remove EC2-Specific Docker Files**
```bash
# Keep Dockerfiles for local development
# Remove docker-compose production configs (EC2-specific)
rm -f docker-compose.prod.yml
rm -f docker-compose.ec2.yml
```

**5.2 Update docker-compose.yml for Local Dev Only**
File: `docker-compose.yml`
- Keep for local development
- Add comment: "# LOCAL DEVELOPMENT ONLY - Production uses Lambda"
- Remove any EC2-specific volumes/configs

---

### Phase 6: Documentation Updates

**6.1 Update Deployment Docs**
- Remove EC2 deployment instructions
- Add Lambda deployment guide
- Update architecture diagrams
- Add SAM CLI installation guide

**6.2 Update README**
- Change "Deployment: EC2" → "Deployment: AWS Lambda"
- Update cost estimates (EC2 vs Lambda)
- Update architecture section

**6.3 Create Lambda-Specific Docs**
- `docs/deployment/lambda-deployment.md`
- `docs/architecture/lambda-architecture.md`
- `docs/troubleshooting/lambda-debugging.md`

---

## Validation Checklist

After migration, verify:

- [ ] Terraform deploys successfully (no EC2 resources)
- [ ] SAM builds all Lambda functions
- [ ] SAM deploys to AWS
- [ ] API Gateway routes to BackendApiFunction
- [ ] FastAPI endpoints respond correctly
- [ ] Database connection works (RDS via VPC)
- [ ] SQS queue processes messages
- [ ] Worker Lambda executes async jobs
- [ ] S3 uploads work (documents + reports)
- [ ] KMS encryption/decryption works
- [ ] Secrets Manager access works
- [ ] CloudWatch logs stream correctly
- [ ] All tests pass in Lambda environment

---

## Rollback Plan

If Lambda deployment fails:

1. **DO NOT** destroy Terraform infrastructure (RDS, VPC persist)
2. Redeploy EC2 temporarily:
   ```bash
   git revert <ec2-removal-commit>
   cd infra/iac
   terraform apply
   ```
3. Investigate Lambda issues
4. Fix and retry Lambda deployment

---

## Cost Comparison

### EC2 (Current)
- t3.medium: $30/month
- Elastic IP: $3.60/month
- Data transfer: ~$10/month
- **Total: ~$43.60/month** (always running)

### Lambda (Target)
- API requests: 1M/month = $0.20
- Compute (512MB): $8.33/month
- Data transfer: ~$10/month
- **Total: ~$18.53/month** (scales to zero)

**Savings: ~$25/month (57% reduction)**

---

## Timeline

- **Phase 1** (Infrastructure Cleanup): 1 hour
- **Phase 2** (Lambda Verification): 2 hours
- **Phase 3** (Deployment Workflow): 1 hour
- **Phase 4** (Code Updates): 3 hours
- **Phase 5** (Docker Cleanup): 30 minutes
- **Phase 6** (Documentation): 1 hour

**Total: ~8.5 hours**

---

## Next Steps

1. ✅ Review this plan
2. Execute Phase 1 (remove EC2 from Terraform)
3. Execute Phase 2 (verify/complete SAM template)
4. Create deployment scripts
5. Update ADR-001 for Lambda architecture
6. Test deployment to dev environment
7. Deploy to production
