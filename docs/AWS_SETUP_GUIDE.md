# AWS Phase 2 — Complete Setup Guide

This guide walks you through deploying the AI Decision Intelligence pipeline
on AWS so it runs automatically in the cloud every day.

Think of it this way:
- **Your laptop** runs the pipeline once manually.
- **AWS** runs it automatically, every single day, on its own.

---

## What We Are Building

```
Every day at 3:00 AM:

[EventBridge Alarm Clock]
        │
        ▼
[Lambda — runs the AI pipeline]
        │
        ▼
[S3 — reads raw data, writes results]
        │
        ├──► [Glue — cleans the raw data into processed data]
        │
        └──► [Athena — lets you query the processed data with SQL]
```

---

## What You Need Before Starting

1. An AWS account (free tier works for this project).
2. AWS CLI installed on your computer.
3. Python and this project set up locally (see `README.md`).

---

## Step 0: Create an AWS Account

If you do not have one:
1. Go to `https://aws.amazon.com` and click "Create an AWS Account".
2. Enter your email, name, and credit card (you won't be charged under free tier).
3. Select "Basic support — Free".

---

## Step 1: Create an IAM User (Your AWS Identity)

Think of IAM as the security guard at the AWS building.
You need a badge (access key) to get in.

**In the AWS Console:**
1. Search for "IAM" in the top search bar and open it.
2. Click "Users" on the left, then "Create user".
3. Name: `ai-decision-intelligence-user`
4. Check "Provide user access to the AWS Management Console" → NO (not needed).
5. Click "Next" → "Attach policies directly".
6. Search and attach these policies:
   - `AmazonS3FullAccess`
   - `AWSGlueConsoleFullAccess`
   - `AmazonAthenaFullAccess`
   - `AWSLambda_FullAccess`
   - `AmazonEventBridgeFullAccess`
   - `IAMFullAccess`
   - `CloudFormationFullAccess`
7. Click "Create user".
8. Open the user you just created → "Security credentials" tab.
9. Click "Create access key" → "Command Line Interface (CLI)".
10. Save the **Access Key ID** and **Secret Access Key** — you only see them once.

---

## Step 2: Configure AWS CLI

Open your terminal and run:

```bash
aws configure
```

Enter:
```
AWS Access Key ID:     AKIA...your key...
AWS Secret Access Key: ...your secret...
Default region name:   us-east-1
Default output format: json
```

Test it works:
```bash
aws sts get-caller-identity
```

You should see your account ID and user name printed. If you see an error, re-check your keys.

---

## Step 3: Choose a Bucket Name

S3 bucket names must be **globally unique** — no two people in the world can have the same name.

```
Good:  ai-decision-intelligence-johnsmith-2025
Good:  my-ai-pipeline-acmecorp
Bad:   my-bucket   (too generic, probably taken)
```

Save your chosen name:
```bash
export BUCKET_NAME="ai-decision-intelligence-yourname"   # replace "yourname"
export AWS_REGION="us-east-1"
```

---

## Step 4: Deploy Everything with CloudFormation (Recommended)

CloudFormation is like a recipe card for AWS. You give it one file,
and it creates all the AWS resources automatically.

### 4a. First, upload your Lambda deployment package

Package the project code as a zip for Lambda:
```bash
cd /path/to/ai-decision-intelligence

# Install dependencies into a folder
pip install -r requirements.txt --target lambda_package/

# Copy source code
cp -r src run_pipeline.py config lambda_package/

# Create zip
cd lambda_package && zip -r ../deployment.zip . && cd ..
```

Upload the zip to S3 (create the bucket first):
```bash
# Create bucket
aws s3 mb s3://$BUCKET_NAME --region $AWS_REGION

# Upload deployment package
aws s3 cp deployment.zip s3://$BUCKET_NAME/lambda-package/deployment.zip

# Upload Glue ETL script
aws s3 cp src/aws/glue_etl_script.py s3://$BUCKET_NAME/scripts/glue_etl_script.py
```

### 4b. Deploy the CloudFormation stack

```bash
aws cloudformation deploy \
  --template-file src/aws/cloudformation.yaml \
  --stack-name ai-decision-intelligence \
  --region $AWS_REGION \
  --parameter-overrides BucketName=$BUCKET_NAME \
  --capabilities CAPABILITY_NAMED_IAM
```

This creates:
- S3 bucket (with encryption + versioning)
- IAM roles for Lambda and Glue
- Lambda function
- Glue ETL job
- EventBridge daily schedule (03:00 UTC)
- Athena workgroup

Check status:
```bash
aws cloudformation describe-stacks \
  --stack-name ai-decision-intelligence \
  --query "Stacks[0].StackStatus"
```

When you see `CREATE_COMPLETE`, all resources are ready.

---

## Step 5: Upload Your Data to S3

```bash
# Upload raw data
aws s3 cp data/raw/source.csv s3://$BUCKET_NAME/raw/source.csv

# Verify it uploaded
aws s3 ls s3://$BUCKET_NAME/raw/
```

---

## Step 6: Test Each Service

### 6a. Test Lambda (run the AI pipeline manually)

```bash
aws lambda invoke \
  --function-name ai-decision-intelligence-runner \
  --payload '{"trigger": "manual-test"}' \
  --cli-binary-format raw-in-base64-out \
  response.json

cat response.json
```

You should see the full pipeline JSON output.
Check CloudWatch logs if something goes wrong:
```bash
aws logs tail /aws/lambda/ai-decision-intelligence-runner --follow
```

### 6b. Test Glue ETL Job

```bash
aws glue start-job-run \
  --job-name ai-decision-intelligence-etl \
  --arguments '{"--INPUT_PATH":"s3://'$BUCKET_NAME'/raw/source.csv","--OUTPUT_PATH":"s3://'$BUCKET_NAME'/processed/processed.csv"}'
```

Check status:
```bash
aws glue get-job-runs --job-name ai-decision-intelligence-etl \
  --query "JobRuns[0].{State:JobRunState,Error:ErrorMessage}"
```

### 6c. Test Athena Query

```python
# In Python, after running the Glue job:
from src.aws.athena_ops import query_and_fetch

df = query_and_fetch(
    query="SELECT date, SUM(revenue) AS total_revenue FROM processed_sales GROUP BY date ORDER BY date DESC LIMIT 10",
    database="ai_decision_intelligence",
    output_location=f"s3://{bucket_name}/athena-output/",
    region="us-east-1",
)
print(df)
```

Or from the AWS Console:
1. Go to Athena.
2. Select database: `ai_decision_intelligence`.
3. Set output location: `s3://your-bucket/athena-output/`.
4. Run: `SELECT * FROM processed_sales LIMIT 10`

---

## Step 7: Bootstrap Script (Alternative to CloudFormation)

If you prefer to set up services individually instead of using CloudFormation:

```bash
python -m src.aws.setup \
  --bucket $BUCKET_NAME \
  --region $AWS_REGION \
  --athena-database ai_decision_intelligence \
  --lambda-arn "arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:ai-decision-intelligence-runner" \
  --eventbridge-rule ai-decision-intelligence-daily
```

Replace `YOUR_ACCOUNT_ID` with your 12-digit AWS account ID:
```bash
aws sts get-caller-identity --query Account --output text
```

---

## Step 8: Verify the Schedule

EventBridge runs Lambda every day at 03:00 UTC automatically.

Check the schedule:
```bash
aws events list-rules --name-prefix ai-decision-intelligence
```

See next scheduled run:
```bash
aws events describe-rule --name ai-decision-intelligence-daily \
  --query "{Schedule:ScheduleExpression, State:State}"
```

---

## Full Execution Flow in AWS

```
Daily at 03:00 UTC
        │
EventBridge triggers Lambda
        │
Lambda runs run_pipeline()
        │
Pipeline reads from S3 raw/
        │
Glue (optional) cleans the data → writes to S3 processed/
        │
Anomaly Detection → Root Cause → Forecast → Recommendations → LLM Explanation
        │
Results returned as JSON in Lambda response
        │
CloudWatch Logs store the output permanently
```

---

## Dataset Collection Guide

### Option A: UCI Online Retail Dataset

1. Download from: `https://archive.ics.uci.edu/dataset/352/online+retail`
2. Open the Excel file → Export as CSV.
3. Rename columns to match the schema:

```python
import pandas as pd

df = pd.read_csv("online_retail.csv")
df = df.rename(columns={
    "InvoiceDate": "date",
    "Country": "region",
    "Description": "product",
})
df["category"] = "Retail"      # Add synthetic category
df["campaign"] = "None"        # Add synthetic campaign
df["revenue"] = df["Quantity"] * df["UnitPrice"]
df["orders"] = df["Quantity"].abs()
df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
df = df[["date", "region", "product", "category", "revenue", "orders", "campaign"]]
df.to_csv("data/raw/source.csv", index=False)
```

### Option B: Keep the Synthetic Dataset

The system auto-generates a realistic 240-day synthetic dataset with injected anomalies
when no `data/raw/source.csv` is found. This is perfect for demos and testing.

---

## Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| `AccessDenied` | IAM user missing a permission | Attach the missing policy in IAM |
| `NoSuchBucket` | Wrong bucket name or region | Check `$BUCKET_NAME` and `--region` |
| `Athena FAILED` | Table schema doesn't match CSV headers | Re-run the `CREATE TABLE` DDL or use the bootstrap script |
| `Lambda timeout` | Pipeline takes >300s | Increase Lambda timeout in CloudFormation (max 900s) or reduce dataset |
| `Lambda out of memory` | Prophet needs more RAM | Increase `MemorySize` to 2048 in CloudFormation and redeploy |
| `Glue FAILED` | ETL script can't find the input file | Ensure the S3 path is correct and file is uploaded |
| `Prophet not found` | Dependency missing in Lambda package | Rebuild the zip including `prophet` and its dependencies |

---

## Security Checklist

Before going to production:

- [ ] Never commit `.env` to git — it is in `.gitignore`.
- [ ] IAM user follows least-privilege principle (only the permissions it needs).
- [ ] S3 bucket has public access blocked (done automatically by the CloudFormation template).
- [ ] S3 encryption is enabled (AES-256, done automatically).
- [ ] Lambda has a CloudWatch log group with 30-day retention (done automatically).
- [ ] EventBridge rule targets only the correct Lambda ARN.
- [ ] Rotate access keys every 90 days (IAM → Users → Security credentials → Rotate).
- [ ] Enable CloudTrail for audit logging of all API calls.

---

## Monthly Cost Estimate (Free Tier)

| Service | Free Tier | Paid Rate |
|---------|-----------|-----------|
| Lambda | 1M requests/month | $0.20 per 1M after |
| S3 | 5 GB storage, 20K GET | $0.023/GB after |
| Glue | 10 DPUs free | $0.44 per DPU/hour after |
| Athena | 5 TB scanned free | $5 per TB after |
| EventBridge | 14M events free | $1 per million after |

For a daily pipeline on a ~10MB dataset: **estimated $0–2/month**.

---

## Deleting Everything (Cleanup)

To delete all AWS resources and avoid any charges:

```bash
# Delete the CloudFormation stack (removes Lambda, EventBridge, IAM roles, Glue job)
aws cloudformation delete-stack --stack-name ai-decision-intelligence

# Empty and delete the S3 bucket
aws s3 rm s3://$BUCKET_NAME --recursive
aws s3 rb s3://$BUCKET_NAME
```
