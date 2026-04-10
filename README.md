# Cosmos Intelligence
## Enterprise Autonomous Business Intelligence Platform

> Turn raw business data into executive decisions in seconds.
> Not just "what happened" — but why, what's next, and what to do.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/framework-FastAPI-00a000.svg)](https://fastapi.tiangolo.com/)
[![Claude AI](https://img.shields.io/badge/AI-Claude%20%7C%20Anthropic-000000.svg)](https://www.anthropic.com/)
[![AWS-Native](https://img.shields.io/badge/cloud-AWS%20Native-FF9900.svg)](https://aws.amazon.com/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## What This Platform Does

Cosmos Intelligence is an enterprise-grade AI system that automatically transforms raw business data into **actionable intelligence through five levels of progressive analysis**:

```
Level 1: SURFACE METRICS      Raw facts (revenue declined 22.4%)
    ↓
Level 2: ROOT CAUSE           Why it happened (Campaign A stopped, -62% impact)
    ↓
Level 3: FORECAST             What's next (further 18% drop expected)
    ↓
Level 4: RECOMMENDATIONS      What to do (restart campaign, +15-25% budget)
    ↓
Level 5: SIMULATION           What if scenarios (revenue impact modeling)
```

Unlike traditional dashboards that show "what happened," Cosmos Intelligence **explains why, predicts what's next, recommends actions, and helps executives simulate decisions** — all automatically, in seconds.

### Key Capabilities

- **Anomaly Detection**: Isolation Forest multi-metric analysis detects revenue, volume, and price anomalies with severity scoring
- **Root Cause Attribution**: 9-dimension breakdown (region, product, campaign, category, etc.) with contribution percentages
- **Forecasting**: Prophet + linear regression with confidence intervals for 7-14 day horizons
- **Executive Recommendations**: Priority-ranked action items with impact estimates and ownership
- **AI Explanations**: Claude-powered natural language narratives that executives can understand and act on
- **Data Privacy**: Complete hard-delete flow — raw data, processed, outputs, and AI context all deletable on demand
- **REST API**: FastAPI endpoints for programmatic access, batch processing, and integration

---

## Architecture

### 7-Stage Intelligence Pipeline

```
Raw CSV Data
    │
    ├─→ [1. INGEST]        Load CSV or synthetic data, validate schema
    │
    ├─→ [2. TRANSFORM]     Clean, validate, aggregate by dimensions
    │
    ├─→ [3. DETECT]        Isolation Forest multi-metric anomaly detection
    │                       (tracks revenue, orders, avg_order_value)
    │
    ├─→ [4. ATTRIBUTE]      Root cause: dimensional breakdown with
    │                       contribution % across 9 dimensions
    │
    ├─→ [5. FORECAST]       Prophet + linear fallback, 7-14 day horizon,
    │                       confidence intervals
    │
    ├─→ [6. RECOMMEND]      Priority-ranked actions with impact & ownership
    │
    └─→ [7. SYNTHESIZE]     Claude LLM: executive narrative + confidence

    Structured JSON Output
    (anomaly, severity, root_cause[], forecast[], recommendation[])
    │
    └─→ [API RESPONSE]      REST endpoint, HTML report, or save to S3
```

### New Endpoints (v2.0)

- **POST /chat** — AI Chat Assistant: Ask questions about your dataset, get Claude-powered answers grounded in uploaded data
- **DELETE /session** — Data Deletion: Hard-delete all session data (raw CSV, processed, outputs, AI context)

### Key Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | React SPA (optional) | Interactive dashboard and chat UI |
| **API** | FastAPI | REST endpoints, auto-doc at /docs |
| **Anomaly Detection** | scikit-learn (Isolation Forest) | Multi-metric unsupervised detection |
| **Root Cause** | Pandas, NumPy | Dimensional attribution analysis |
| **Forecasting** | Prophet, Linear Regression | Time-series prediction with CI |
| **Recommendations** | Custom scoring engine | Priority & impact calculation |
| **LLM** | Anthropic Claude (Haiku/Sonnet) | Natural language explanations |
| **Cloud** | AWS (S3, Glue, Athena, Lambda, EventBridge) | Scalable cloud deployment |

---

## Quick Start

### 1. Setup (Local)

```bash
# Clone repository
git clone https://github.com/your-org/cosmos-intelligence.git
cd cosmos-intelligence

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add ANTHROPIC_API_KEY for LLM explanations
```

### 2. Run the Pipeline

```bash
# Run the full intelligence pipeline
make run

# Or with CLI output
python run_pipeline.py --pretty

# Generate HTML executive brief
make demo

# Generate JSON output only
make json
```

### 3. Start the API

```bash
make api
# Open browser to http://localhost:8000/docs
```

### 4. Run Tests

```bash
pytest -v --cov=src tests/
# 44 test cases covering all pipeline stages
```

---

## API Reference

All endpoints return structured JSON. Responses include timestamps, processing time, and confidence scores.

### System & Health

```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2025-04-07T12:30:45Z",
  "uptime_seconds": 3600.5
}
```

### Full Intelligence Pipeline

```bash
GET /analyze
```

Executes all 7 stages: ingest → transform → detect → attribute → forecast → recommend → synthesize.

Response includes:
- `anomaly_detected` (boolean)
- `severity` (CRITICAL, WARNING, NORMAL)
- `root_cause[]` with dimension, group_value, delta, contribution_pct
- `forecast_values[]` (7-day predictions)
- `forecast_confidence_lower/upper` (95% confidence intervals)
- `recommendation[]` with action, priority, expected_impact, timeline, owner
- `explanation` (Claude-generated narrative)
- `confidence` (0.0-1.0 overall confidence score)

### Forecast Only

```bash
GET /forecast
```

Returns 7-day forecast with confidence intervals (skips anomaly detection and root cause).

Response:
```json
{
  "prediction": "Revenue forecast shows 5.2% growth over 7 days",
  "forecast_values": [102000, 103400, 104900, ...],
  "confidence_lower": [95000, 96400, 97900, ...],
  "confidence_upper": [109000, 110400, 111900, ...],
  "model": "Prophet",
  "periods": 7,
  "timestamp": "2025-04-07T12:30:45Z"
}
```

### Upload & Analyze

```bash
POST /upload
Content-Type: multipart/form-data

file: <your-csv>
```

Uploads a CSV, processes it, and runs the full pipeline.

Response: Full `DecisionResponse` JSON.

### AI Chat Assistant (NEW)

```bash
POST /chat
Content-Type: application/json

{
  "question": "Which region is driving the revenue decline?",
  "context": { /* pipeline output JSON */ }
}
```

Response:
```json
{
  "answer": "The West region is the primary driver, with a 24% contribution to the overall decline. Campaign A's cessation accounts for 62% of the impact...",
  "llm_powered": true,
  "timestamp": "2025-04-07T12:30:45Z"
}
```

### Delete Session Data (NEW)

```bash
DELETE /session
```

Permanently hard-deletes all session data:
- Raw CSV upload
- Processed data
- Generated outputs
- AI context cache

Response:
```json
{
  "status": "deleted",
  "timestamp": "2025-04-07T12:30:45Z",
  "items_deleted": ["raw_csv", "processed_data", "outputs", "ai_context"]
}
```

---

## Project Structure

```
cosmos-intelligence/
│
├── config/
│   └── config.yaml                 # All tunable parameters
│
├── data/
│   ├── raw/source.csv              # Input CSV (user-provided or generated)
│   └── processed/processed.csv     # Cleaned and aggregated output
│
├── docs/
│   ├── AWS_SETUP_GUIDE.md         # Step-by-step AWS deployment
│   └── cosmos-intelligence-architecture.docx  # Technical architecture
│
├── src/
│   ├── api/
│   │   └── main.py                 # FastAPI app, 7 endpoints, auto-doc
│   │
│   ├── ingestion/
│   │   └── ingest.py               # Load CSV, validate schema, synthetic gen
│   │
│   ├── processing/
│   │   └── transform.py            # Clean, validate, aggregate by dimensions
│   │
│   ├── anomaly/
│   │   └── detect.py               # Isolation Forest, multi-metric, severity
│   │
│   ├── root_cause/
│   │   └── analyze.py              # 9-dimension attribution, contribution %
│   │
│   ├── forecasting/
│   │   └── forecast.py             # Prophet + linear fallback, confidence CI
│   │
│   ├── recommendation/
│   │   └── recommend.py            # Priority scoring, impact, ownership
│   │
│   ├── llm/
│   │   └── explain.py              # Claude API, deterministic fallback
│   │
│   ├── aws/
│   │   ├── s3_ops.py               # S3 upload/download with retry
│   │   ├── glue_ops.py             # AWS Glue job orchestration
│   │   ├── athena_ops.py           # SQL query via Athena
│   │   ├── lambda_handler.py       # Lambda entry point
│   │   ├── eventbridge_ops.py      # Schedule with EventBridge
│   │   ├── setup.py                # One-command AWS bootstrap
│   │   ├── glue_etl_script.py      # ETL in AWS Glue
│   │   └── cloudformation.yaml     # Infrastructure-as-Code
│   │
│   ├── reporting/
│   │   ├── html_report.py          # Executive HTML brief generator
│   │   └── cli_output.py           # Rich CLI formatting
│   │
│   └── utils/
│       ├── helpers.py              # Config loading, path management
│       └── logger.py               # Structured JSON logging (CloudWatch-ready)
│
├── tests/
│   ├── conftest.py                 # Shared test fixtures
│   ├── test_transform.py           # Data processing (8 cases)
│   ├── test_anomaly.py             # Anomaly detection (8 cases)
│   ├── test_forecast.py            # Forecasting (7 cases)
│   ├── test_recommend.py           # Recommendations (8 cases)
│   └── test_pipeline.py            # End-to-end integration (13 cases)
│
├── .env.example                    # Environment variable template
├── requirements.txt                # Pinned dependencies (Python 3.10+)
├── Makefile                        # CLI shortcuts
├── run_pipeline.py                 # Standalone CLI runner
├── Dockerfile                      # Container definition
└── README.md                       # This file
```

---

## Configuration

### config.yaml Reference

Key settings that control pipeline behavior:

| Setting | Default | Type | Description |
|---------|---------|------|-------------|
| `data.lookback_days` | 14 | int | Historical window for anomaly detection |
| `data.comparison_days` | 14 | int | Prior period for % change calculation |
| `anomaly.contamination` | 0.08 | float | Expected fraction of anomalous points (0.0-1.0) |
| `anomaly.tracked_metrics` | [revenue, orders, avg_order_value] | list | Metrics included in multi-metric detection |
| `forecast.periods` | 7 | int | Days to forecast ahead |
| `forecast.include_confidence_intervals` | true | bool | Include 95% CI in forecast |
| `llm.model` | claude-haiku-4-5-20251001 | str | Claude model (haiku=fast, sonnet=high quality) |
| `llm.max_tokens` | 300 | int | Max tokens in LLM explanation |
| `llm.fallback_to_deterministic` | true | bool | Use template if API fails |
| `api.enable_auth` | false | bool | Require X-API-Key header on requests |
| `aws.s3_upload_on_complete` | false | bool | Auto-upload results to S3 after run |
| `aws.region` | us-east-1 | str | AWS region for cloud deployment |

### Environment Variables

Set these in `.env` (never in config.yaml):

```bash
ANTHROPIC_API_KEY=sk-ant-...                  # Anthropic API key for Claude
API_KEY=cosmos-secret-2025                    # Optional: API key for /analyze endpoint
AWS_ACCESS_KEY_ID=AKIA...                     # AWS credentials (if using Phase 2)
AWS_SECRET_ACCESS_KEY=...
OPENTELEMETRY_ENDPOINT=http://localhost:4317  # Optional: observability
```

---

## AWS Deployment (Phase 2)

For cloud-scale processing:

```bash
# One-command deployment via CloudFormation
aws cloudformation deploy \
  --template-file src/aws/cloudformation.yaml \
  --stack-name cosmos-intelligence \
  --parameter-overrides BucketName=cosmos-intelligence-yourname \
  --capabilities CAPABILITY_NAMED_IAM
```

### Architecture

| Service | Role |
|---------|------|
| **S3** | Store raw uploads, processed data, outputs, and audit logs |
| **Glue** | Serverless ETL: clean and transform at scale |
| **Athena** | SQL queries on processed data in S3 |
| **Lambda** | Stateless pipeline execution (triggered by API or schedule) |
| **EventBridge** | Schedule pipeline daily (or on-demand) |
| **CloudWatch** | Logs, metrics, alarms (structured JSON logging) |
| **IAM** | Fine-grained role-based access control |
| **KMS** | Optional encryption for sensitive data |

See **[AWS_SETUP_GUIDE.md](docs/AWS_SETUP_GUIDE.md)** for step-by-step instructions.

---

## Data Privacy & Deletion

Cosmos Intelligence is designed for enterprise data privacy compliance.

### Hard Delete Flow

When `DELETE /session` is called, the system permanently removes:

1. **Raw CSV Upload** — Original user-provided data file
2. **Processed Data** — Cleaned and aggregated dataset
3. **Pipeline Outputs** — JSON results and HTML reports
4. **AI Context Cache** — Embedding cache used for /chat endpoint
5. **Audit Logs** — Session metadata and processing timestamps

All files are deleted from:
- Local filesystem (if running locally)
- AWS S3 (if using cloud deployment)
- CloudWatch logs (log retention policy enforced)

### No Data Retention Without Consent

- Cosmos Intelligence does **not** retain data beyond the session
- No background processes access deleted data
- No analytics tracking of user uploads
- GDPR/CCPA compliant deletion procedures

### Audit Trail

All deletions are logged to CloudWatch (JSON format):
```json
{
  "timestamp": "2025-04-07T12:30:45Z",
  "event": "session_delete",
  "session_id": "sess_abc123",
  "items_deleted": 5,
  "duration_ms": 234
}
```

---

## LLM Integration

### Anthropic Claude

Cosmos Intelligence uses **Claude by Anthropic** for intelligent explanations.

**Default Model**: `claude-haiku-4-5-20251001` (fast, cost-efficient, 100k context window)

**Alternative**: `claude-sonnet-4-6` (higher quality, more detail, 200k context window)

Switch models in `config.yaml`:

```yaml
llm:
  model: claude-sonnet-4-6  # Upgrade for higher quality
  max_tokens: 500
```

### Fallback Behavior

If `ANTHROPIC_API_KEY` is not set or the API fails:

1. System automatically generates a deterministic explanation using rule-based templates
2. `llm_powered: false` in response JSON indicates fallback mode
3. All other pipeline stages (anomaly, forecast, recommend) continue normally

### Context Strategy

For the `/chat` endpoint, the entire pipeline output is passed to Claude as structured context:

```json
{
  "question": "Which region is driving the decline?",
  "context": {
    "anomaly_detected": true,
    "root_cause": [...],
    "forecast": [...],
    "recommendation": [...]
  }
}
```

This allows Claude to answer follow-up questions grounded in your specific data.

---

## Running Tests

### Test Suite

44 test cases covering all pipeline stages:

```bash
# Run all tests with coverage
pytest -v --cov=src --cov-report=term-missing tests/

# Run specific test file
pytest tests/test_anomaly.py -v

# Run fast test suite (no slow integration tests)
pytest tests/ -x
```

### Test Coverage

| Module | Tests | Coverage |
|--------|-------|----------|
| Transform | 8 | Data cleaning, aggregation, edge cases |
| Anomaly | 8 | Isolation Forest, severity scoring, multi-metric |
| Forecast | 7 | Prophet, confidence intervals, fallback |
| Recommend | 8 | Priority scoring, impact calculation, ownership |
| Pipeline | 13 | End-to-end integration, API contract |

### Sample Output

```
tests/test_anomaly.py::test_isolation_forest_detects_outliers PASSED
tests/test_forecast.py::test_prophet_confidence_intervals PASSED
tests/test_recommend.py::test_recommendation_priority_scoring PASSED
===================== 44 passed in 2.34s =====================
```

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Runtime** | Python 3.10+ | Type safety, dataclass support, modern async |
| **Web Framework** | FastAPI | Async, auto-doc generation, Pydantic validation |
| **ML** | scikit-learn | Isolation Forest unsupervised learning |
| **Time Series** | Prophet, statsmodels | Robust forecasting with seasonality |
| **Data** | Pandas, NumPy | Standard data manipulation |
| **LLM** | Anthropic Claude | Enterprise AI, low latency, high accuracy |
| **Visualization** | Plotly | Interactive HTML reports, easy embedding |
| **Testing** | pytest | Fast, fixture-based, excellent coverage tools |
| **Cloud** | AWS S3, Glue, Athena, Lambda, EventBridge | Serverless, auto-scaling, pay-per-use |
| **Logging** | Structured JSON, CloudWatch | Searchable logs, production-ready |
| **Container** | Docker | Local dev → cloud deployment consistency |

---

## Performance Characteristics

### Latency

- **Full Pipeline**: 1-3 seconds (local machine)
- **Forecast Only**: 500ms
- **API Response Time**: Includes processing + LLM (typically 2-5s with Claude)

### Concurrency

- **FastAPI**: Async/await supports 1000+ concurrent requests
- **AWS Lambda**: Auto-scales to match request volume
- **Glue ETL**: Distributed processing on up to 100 DPUs

### Data Scale

- **CSV Input**: Tested up to 1M rows
- **Time Series Window**: 14-90 days recommended
- **Dimensions**: Supports 9+ dimensions (region, product, campaign, etc.)

---

## Production Checklist

Before deploying to production:

- [ ] Set `ANTHROPIC_API_KEY` in secrets manager
- [ ] Enable API key authentication: `api.enable_auth: true`
- [ ] Configure AWS S3 bucket for outputs
- [ ] Set up CloudWatch alarms for Lambda failures
- [ ] Enable VPC for Lambda (if processing sensitive data)
- [ ] Configure KMS encryption for S3 buckets
- [ ] Review IAM roles and restrict permissions
- [ ] Set up log retention policies (90 days recommended)
- [ ] Test DELETE /session endpoint with sample data
- [ ] Document runbook for incidents

---

## Roadmap

### Phase 1: Core Platform (Current)
- Multi-metric anomaly detection
- Root cause attribution
- Forecasting with confidence intervals
- AI-powered recommendations
- REST API
- HTML executive briefs
- Local + AWS deployment

### Phase 2: Multi-Tenant SaaS
- User authentication & authorization
- Organization/workspace isolation
- Custom metric configuration
- Role-based access control
- Usage metering & billing integration

### Phase 3: Real-Time Streaming
- Kafka/Kinesis integration
- Sub-second anomaly detection
- Real-time dashboards
- Alert notifications

### Phase 4: Custom ML Models
- Fine-tune Claude on your business data
- Custom anomaly detection models
- Domain-specific language models

---

## Support & Contributing

### Issues & Bugs

Open an issue with:
- Your config.yaml (redact sensitive values)
- Sample CSV data (or describe schema)
- Expected vs. actual output
- Full stack trace

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit with clear messages (`git commit -m "Add X feature"`)
4. Push and open a pull request

### Architecture Questions?

See **[cosmos-intelligence-architecture.docx](docs/cosmos-intelligence-architecture.docx)** for detailed technical design.

---

## License

MIT License — See LICENSE file for full terms.

---

## Acknowledgments

Built with:
- **Anthropic Claude** for intelligent explanations
- **Facebook Prophet** for robust forecasting
- **scikit-learn** for anomaly detection
- **FastAPI** for the REST API framework

---

**Last Updated**: April 7, 2025
**Version**: 2.0.0
**Status**: Production Ready
