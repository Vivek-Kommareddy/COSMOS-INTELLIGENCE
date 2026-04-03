# AI Decision Intelligence System

An enterprise-grade AI system that automatically detects anomalies in business data,
explains root causes, forecasts future trends, and recommends actionable decisions —
with zero human analysis required.

> **This is not a dashboard. This is a decision-making engine.**

---

## Architecture

```
                    ┌─────────────────────────────────────────────────┐
                    │            AI Decision Intelligence              │
                    │                                                 │
  Raw CSV Data ───► │ Ingest ─► Transform ─► Detect ─► Root Cause    │
                    │                           │           │          │
                    │              Forecast ◄───┘           │          │
                    │                  │                    │          │
                    │           Recommend ◄─────────────────┘          │
                    │                  │                               │
                    │            Explain (Claude LLM)                  │
                    │                  │                               │
                    └──────────────────┼──────────────────────────────┘
                                       │
                                       ▼
                            ┌─────────────────────┐
                            │   Structured JSON   │
                            │ anomaly_detected     │
                            │ severity: CRITICAL   │
                            │ root_cause: [...]    │
                            │ recommendation: [...] │
                            │ confidence: 0.87     │
                            └─────────────────────┘
```

---

## Expected Output

```json
{
  "metric": "revenue",
  "anomaly_detected": true,
  "severity": "CRITICAL",
  "change": "-22.4%",
  "anomaly_count": 4,
  "anomaly_dates": ["2025-08-14", "2025-08-20"],
  "root_cause": [
    {
      "driver": "Campaign 'Campaign_A' declined by 18500.00",
      "dimension": "campaign",
      "group_value": "Campaign_A",
      "delta": -18500.0,
      "contribution_pct": -62.1
    },
    {
      "driver": "Region 'West' declined by 7200.00",
      "dimension": "region",
      "group_value": "West",
      "delta": -7200.0,
      "contribution_pct": -24.2
    }
  ],
  "prediction": "Further 18.3% drop expected over the next 7 days",
  "forecast_values": [97800, 96500, 95200, 94100, 93400, 92800, 92100],
  "forecast_confidence_lower": [88000, 86500, 85200, 84100, 83400, 82800, 82100],
  "forecast_confidence_upper": [107800, 106500, 105200, 104100, 103400, 102800, 102100],
  "recommendation": [
    {
      "action": "Restart or optimize 'Campaign_A' — allocate emergency budget increase of 15-25%",
      "priority": "HIGH",
      "expected_impact": "Expected 37-55% revenue recovery within 7 days",
      "timeline": "Immediate (24-48 hours)",
      "owner": "Marketing Team"
    }
  ],
  "confidence": 0.87,
  "explanation": "Revenue has declined 22.4% versus the prior 14-day period, driven primarily by the cessation of Campaign_A (62% of impact) and West region underperformance (24% of impact). Immediate campaign restart is critical to arrest the projected continued decline of 18.3% over the next week.",
  "llm_powered": true,
  "processing_time_ms": 1243.5,
  "timestamp": "2025-08-21T08:00:00+00:00",
  "pipeline_version": "1.0.0"
}
```

---

## Project Structure

```
ai-decision-intelligence/
│
├── config/
│   └── config.yaml              # All tunable parameters
│
├── data/
│   ├── raw/source.csv           # Input data (real or synthetic)
│   └── processed/processed.csv  # Cleaned and aggregated output
│
├── docs/
│   └── AWS_SETUP_GUIDE.md       # Step-by-step AWS Phase 2 guide
│
├── src/
│   ├── ingestion/ingest.py       # Load CSV or generate synthetic data
│   ├── processing/transform.py   # Clean, validate, aggregate
│   ├── anomaly/detect.py         # Isolation Forest + severity scoring
│   ├── root_cause/analyze.py     # Dimensional attribution (% contribution)
│   ├── forecasting/forecast.py   # Prophet + linear fallback + CI
│   ├── recommendation/recommend.py # Priority-ranked action items
│   ├── llm/explain.py            # Anthropic Claude narrative + confidence
│   ├── api/main.py               # FastAPI REST endpoints
│   │
│   ├── aws/
│   │   ├── s3_ops.py             # Upload, download, list (with retry)
│   │   ├── glue_ops.py           # Start Glue jobs, poll to completion
│   │   ├── athena_ops.py         # Execute SQL, fetch results as DataFrame
│   │   ├── lambda_handler.py     # AWS Lambda entry point
│   │   ├── eventbridge_ops.py    # Schedule and manage EventBridge rules
│   │   ├── setup.py              # One-command AWS bootstrap script
│   │   ├── glue_etl_script.py    # ETL script that runs inside AWS Glue
│   │   └── cloudformation.yaml   # Full Infrastructure-as-Code template
│   │
│   └── utils/
│       ├── helpers.py            # Config loading, path management
│       └── logger.py             # Structured JSON logger (CloudWatch-ready)
│
├── tests/
│   ├── conftest.py               # Shared fixtures
│   ├── test_transform.py         # Data processing unit tests
│   ├── test_anomaly.py           # Anomaly detection unit tests
│   ├── test_forecast.py          # Forecasting unit tests
│   ├── test_recommend.py         # Recommendation engine unit tests
│   └── test_pipeline.py          # End-to-end integration test
│
├── .env.example                  # Environment variable template
├── requirements.txt              # Pinned dependencies
└── run_pipeline.py               # CLI pipeline runner
```

---

## Setup (Local)

### 1. Clone and create virtual environment

```bash
git clone https://github.com/your-repo/ai-decision-intelligence.git
cd ai-decision-intelligence

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env — at minimum set ANTHROPIC_API_KEY for LLM-powered explanations
```

### 3. Run the pipeline

```bash
python run_pipeline.py --pretty
```

### 4. Start the REST API

```bash
uvicorn src.api.main:app --reload
```

API docs auto-generated at: `http://localhost:8000/docs`

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System health and uptime |
| `/analyze` | GET | Full AI decision pipeline |
| `/forecast` | GET | Revenue forecast only (7-day) |
| `/decision` | GET | Alias for `/analyze` (executive-facing) |

### Example call

```bash
curl http://localhost:8000/analyze | python3 -m json.tool
```

### Optional API key authentication

Set `enable_auth: true` in `config.yaml` and `API_KEY=...` in `.env`.
Then pass `X-API-Key: your-key` header on all requests.

---

## Using Your Own Dataset

The system works with any CSV that has these columns:

| Column | Type | Example |
|--------|------|---------|
| `date` | YYYY-MM-DD | 2025-01-15 |
| `region` | string | East, West, North, South |
| `product` | string | Laptop, Chair |
| `category` | string | Electronics, Furniture |
| `revenue` | float | 4500.00 |
| `orders` | integer | 120 |
| `campaign` | string | Campaign_A, None |

Place your file at `data/raw/source.csv` before running.

### Recommended datasets
- **UCI Online Retail** — `https://archive.ics.uci.edu/dataset/352/online+retail`
- **Instacart Market Basket** — available on Kaggle

---

## LLM Integration (Anthropic Claude)

Set `ANTHROPIC_API_KEY` in `.env`. The system uses `claude-haiku-4-5-20251001` by default
(fast, cost-efficient). Switch to `claude-sonnet-4-6` for higher narrative quality:

```yaml
# config/config.yaml
llm:
  model: claude-sonnet-4-6
```

If no API key is set, the system falls back to a deterministic narrative automatically.

---

## Running Tests

```bash
pytest -v --cov=src --cov-report=term-missing
```

Tests cover:
- Data transformation (8 cases)
- Anomaly detection (8 cases)
- Forecasting (7 cases)
- Recommendation engine (8 cases)
- End-to-end pipeline (13 cases)

---

## AWS Phase 2 — Cloud Deployment

See the complete step-by-step guide: [`docs/AWS_SETUP_GUIDE.md`](docs/AWS_SETUP_GUIDE.md)

### Quick summary

| Service | Role |
|---------|------|
| **S3** | Store raw and processed data |
| **Glue** | ETL: clean and transform data in the cloud |
| **Athena** | Query processed data with SQL |
| **Lambda** | Run the full pipeline serverlessly |
| **EventBridge** | Schedule pipeline to run daily at 03:00 UTC |

### One-command infrastructure deployment

```bash
# Deploy all AWS resources via CloudFormation
aws cloudformation deploy \
  --template-file src/aws/cloudformation.yaml \
  --stack-name ai-decision-intelligence \
  --parameter-overrides BucketName=ai-decision-intelligence-yourname \
  --capabilities CAPABILITY_NAMED_IAM
```

---

## Configuration Reference

Key settings in `config/config.yaml`:

| Setting | Default | Description |
|---------|---------|-------------|
| `anomaly.contamination` | `0.08` | Expected fraction of anomalous data points |
| `forecast.periods` | `7` | Days to forecast ahead |
| `llm.model` | `claude-haiku-4-5-20251001` | Claude model for explanations |
| `api.enable_auth` | `false` | Enable X-API-Key authentication |
| `aws.s3_upload_on_complete` | `false` | Auto-upload results to S3 after pipeline run |

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Isolation Forest | Unsupervised — no labeled anomaly data required |
| Multi-variate detection | Uses `revenue + orders + revenue_per_order` — catches quantity and price anomalies |
| % contribution scores | Moves beyond "biggest drop" to statistically attributable causation |
| Prophet + linear fallback | Graceful degradation — works even if Prophet is not installed |
| Anthropic Claude | Best-in-class reasoning for executive narrative generation |
| Structured JSON output | Machine-readable by downstream systems (alerting, dashboards, Slack bots) |
| Tenacity retry | AWS API calls are retried automatically with exponential backoff |

---

## Author

Built as a solo enterprise AI system using Python + AWS.
