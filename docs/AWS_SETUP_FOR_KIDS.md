# AWS Setup Guide (Explained Like You Are 10)

This guide walks through Phase 2: **S3 + Glue + Athena + Lambda + EventBridge**.

## Big Picture
Think of AWS like a smart factory:
1. **S3** is a warehouse for files.
2. **Glue** is a cleaning robot (ETL).
3. **Athena** is a question engine for your data.
4. **Lambda** is a tiny worker that runs code when told.
5. **EventBridge** is an alarm clock that wakes Lambda every day.

---

## 0) Before You Start
- Make an AWS account.
- Make an IAM user with permissions for S3, Glue, Athena, Lambda, and EventBridge.
- Install AWS CLI and configure it:

```bash
aws configure
```

You will type:
- Access key
- Secret key
- Region (example: `us-east-1`)
- Output (`json`)

---

## 1) Create S3 Bucket
Bucket stores raw and processed CSV files.

```bash
python -m src.aws.setup --bucket ai-decision-intelligence-yourname --region us-east-1
```

Then upload data:

```bash
aws s3 cp data/raw/source.csv s3://ai-decision-intelligence-yourname/raw/source.csv
aws s3 cp data/processed/processed.csv s3://ai-decision-intelligence-yourname/processed/processed.csv
```

---

## 2) Glue ETL Job
Create a Glue job in AWS Console:
- Job name: `ai-decision-intelligence-etl`
- Runtime: Python 3
- IAM Role: Glue service role
- Script path in S3: `s3://.../glue/scripts/etl.py`

Minimal ETL script idea:
- Read from `raw/`
- Normalize columns
- Save to `processed/`

Trigger it from code:

```python
from src.aws.glue_ops import start_glue_job
run_id = start_glue_job("ai-decision-intelligence-etl")
print(run_id)
```

---

## 3) Athena Setup
In Athena:
1. Create database: `ai_decision_intelligence`
2. Create table pointing to `s3://.../processed/`
3. Query for trends

Run query from Python:

```python
from src.aws.athena_ops import run_athena_query

result = run_athena_query(
    query="SELECT date, sum(revenue) AS rev FROM processed GROUP BY date ORDER BY date",
    database="ai_decision_intelligence",
    output_location="s3://ai-decision-intelligence-yourname/athena-output/"
)
print(result)
```

---

## 4) Lambda Setup
Lambda should run `run_pipeline()`.

File already provided:
- `src/aws/lambda_handler.py`

In AWS Lambda console:
1. Create function (Python 3.11).
2. Zip project code and upload.
3. Handler should be: `src.aws.lambda_handler.handler`
4. Give role permissions to S3/Glue/Athena.

Test event example:

```json
{"trigger": "manual-test"}
```

---

## 5) EventBridge Schedule
EventBridge runs Lambda every day.

From code:

```python
from src.aws.eventbridge_ops import schedule_lambda_daily
schedule_lambda_daily("ai-decision-intelligence-daily", "arn:aws:lambda:us-east-1:123456789012:function:ai-decision-intelligence-runner")
```

Cron used: `cron(0 3 * * ? *)` = every day at 03:00 UTC.

---

## 6) Full Execution Flow in AWS
1. New file lands in S3 raw folder.
2. Glue job cleans/transforms.
3. Processed file stored in S3.
4. Athena can query it.
5. Lambda runs decision pipeline.
6. EventBridge repeats daily.

---

## 7) Dataset Collection Tips
You can use:
- UCI Online Retail CSV
- Instacart public datasets

Steps:
1. Download CSV locally.
2. Rename headers to required schema (`date, region, product, category, revenue, orders, campaign`).
3. If columns missing, add synthetic fields in `transform.py` or pre-processing notebook.
4. Upload cleaned CSV to `data/raw` and S3 raw path.

---

## 8) Quick Troubleshooting
- **AccessDenied**: IAM role missing permissions.
- **NoSuchBucket**: bucket name typo or wrong region.
- **Athena FAILED**: table schema does not match CSV.
- **Lambda timeout**: increase timeout/memory in Lambda settings.

---

## 9) Security Checklist
- Never commit AWS keys.
- Use IAM least privilege.
- Encrypt S3 bucket (SSE-S3 or SSE-KMS).
- Enable CloudWatch logs for Lambda and Glue.

