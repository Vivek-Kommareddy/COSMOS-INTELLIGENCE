<div align="center">

# ✦ COSMOS INTELLIGENCE

### Enterprise Autonomous Business Intelligence Platform

**Architected by [Vivek Kommareddy](https://github.com/Vivek-Kommareddy)**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js_16-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![Claude AI](https://img.shields.io/badge/Claude_AI-Anthropic-FF6B35?style=for-the-badge)](https://www.anthropic.com/)
[![AWS](https://img.shields.io/badge/AWS_App_Runner-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<br/>

> **"Here's what's happening, why it's happening, what will happen next, and what you should do."**
>
> Cosmos Intelligence transforms raw business data into executive decisions in seconds — not just "what happened," but the complete intelligence chain from anomaly to action.

<br/>

🌐 **[Live Demo](https://6nmkmjhh5i.us-east-1.awsapprunner.com)** · 📡 **[API Health](https://bpc53g62fh.us-east-1.awsapprunner.com/health)** · 📂 **[Repository](https://github.com/Vivek-Kommareddy/COSMOS-INTELLIGENCE)**

</div>

---

## What Makes This Different

Traditional business intelligence tools answer one question: *"What happened?"*

Cosmos Intelligence answers five:

| Level | Question | What You Get |
|-------|----------|--------------|
| **1 · Surface Metrics** | What happened? | KPIs, revenue, orders, AOV with period-over-period change |
| **2 · Root Cause** | Why did it happen? | 9-dimension attribution with % contribution per factor |
| **3 · Forecast** | What will happen? | 7–14 day predictions with 95% confidence intervals |
| **4 · Recommendations** | What should I do? | Priority-ranked action items with impact estimates |
| **5 · Simulation** | What if I do X? | Claude AI-powered scenario modeling and impact analysis |

Upload any CSV. Get a full executive intelligence brief in under 3 seconds.

---

## Architecture

### The 7-Stage Intelligence Pipeline

```
 ┌─────────────────────────────────────────────────────────────────┐
 │                    COSMOS INTELLIGENCE ENGINE                    │
 │              Architected by Vivek Kommareddy                    │
 └─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Raw CSV Input    │
                    │  (any business    │
                    │   data format)    │
                    └─────────┬─────────┘
                              │
          ┌───────────────────▼───────────────────┐
          │                                       │
  ┌───────▼────────┐                    ┌─────────▼────────┐
  │  1. INGEST     │                    │                   │
  │                │   Load CSV/Excel,  │   Auto-detect     │
  │  Schema        │◄──────────────────►│   schema, types,  │
  │  Detection     │                    │   date columns    │
  └───────┬────────┘                    └──────────────────┘
          │
  ┌───────▼────────┐
  │  2. TRANSFORM  │   Clean nulls, validate ranges,
  │                │   aggregate by date & dimensions,
  │  Data Quality  │   compute period-over-period deltas
  └───────┬────────┘
          │
  ┌───────▼────────┐
  │  3. DETECT     │   Isolation Forest (unsupervised ML)
  │                │   Multi-metric: revenue + orders + AOV
  │  Anomaly       │   Severity: CRITICAL / WARNING / NORMAL
  │  Detection     │   Contamination threshold: configurable
  └───────┬────────┘
          │
  ┌───────▼────────┐
  │  4. ATTRIBUTE  │   9-Dimension root cause breakdown:
  │                │   Region · Product · Campaign · Category
  │  Root Cause    │   Channel · Segment · Time · SKU · Agent
  │  Analysis      │   Each with delta % and contribution score
  └───────┬────────┘
          │
  ┌───────▼────────┐
  │  5. FORECAST   │   Facebook Prophet + Linear Regression
  │                │   7–14 day forward projection
  │  Predictive    │   95% confidence interval upper/lower bands
  │  Modeling      │   Seasonal decomposition & trend isolation
  └───────┬────────┘
          │
  ┌───────▼────────┐
  │  6. RECOMMEND  │   Playbook-driven action generation
  │                │   Priority scoring (P1–P3), impact estimate,
  │  Action        │   timeline, owner assignment
  │  Engine        │   Cross-references forecast + root cause
  └───────┬────────┘
          │
  ┌───────▼────────┐
  │  7. SYNTHESIZE │   Anthropic Claude (Haiku / Sonnet)
  │                │   Grounded narrative from structured data
  │  Claude LLM    │   Executive-readable language
  │  Explanation   │   Confidence score + fallback mode
  └───────┬────────┘
          │
  ┌───────▼─────────────────────────────────────────────┐
  │              STRUCTURED JSON OUTPUT                  │
  │  anomaly_detected · severity · root_cause[]          │
  │  forecast_values[] · CI_lower · CI_upper             │
  │  recommendation[] · explanation · confidence         │
  └─────────────────────────────────────────────────────┘
          │
          ├──► REST API Response  (FastAPI /analyze)
          ├──► HTML Executive Brief
          ├──► AI Chat Context   (/chat endpoint)
          └──► AWS S3 Storage    (optional)
```

### System Architecture

```
┌────────────────────────────────────────────────────────────┐
│                     AWS CLOUD LAYER                        │
│                                                            │
│  ┌─────────────────────┐    ┌─────────────────────────┐  │
│  │   AWS App Runner     │    │   AWS App Runner         │  │
│  │   FRONTEND           │    │   BACKEND API            │  │
│  │   Next.js 16.2.3     │◄──►│   FastAPI + Python 3.10 │  │
│  │   0.25vCPU / 1GB RAM │    │   0.25vCPU / 0.5GB RAM  │  │
│  └──────────┬──────────┘    └─────────────┬───────────┘  │
│             │                              │               │
│  ┌──────────▼──────────┐    ┌─────────────▼───────────┐  │
│  │   AWS ECR            │    │   AWS ECR                │  │
│  │   cosmos-client      │    │   cosmos-server          │  │
│  │   (private registry) │    │   (private registry)     │  │
│  └─────────────────────┘    └─────────────────────────┘  │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  AWS Supporting Services                              │ │
│  │  S3 · Glue · Athena · Lambda · EventBridge           │ │
│  │  CloudWatch · IAM · KMS                              │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                   AI INTELLIGENCE LAYER                    │
│                                                            │
│  ┌──────────────────┐  ┌──────────────────┐              │
│  │  Anthropic Claude │  │  Facebook Prophet │              │
│  │  Haiku / Sonnet   │  │  Time-Series      │              │
│  │  Natural Language │  │  Forecasting      │              │
│  │  Explanation      │  │                   │              │
│  └──────────────────┘  └──────────────────┘              │
│                                                            │
│  ┌──────────────────┐  ┌──────────────────┐              │
│  │  scikit-learn     │  │  Custom Scoring   │              │
│  │  Isolation Forest │  │  Recommendation   │              │
│  │  Anomaly Detection│  │  Engine           │              │
│  └──────────────────┘  └──────────────────┘              │
└────────────────────────────────────────────────────────────┘
```

---

## AI Engines — How Intelligence Is Generated

### Engine 1: Anomaly Detection (scikit-learn Isolation Forest)

Cosmos uses **Isolation Forest**, an unsupervised machine learning algorithm that detects outliers by randomly partitioning data. Unlike supervised methods, it requires no labeled training data — it learns what "normal" looks like from your own dataset.

- Tracks **three metrics simultaneously**: `revenue`, `orders`, `avg_order_value`
- Assigns severity: `CRITICAL` (contamination > threshold), `WARNING`, or `NORMAL`
- Contamination parameter configurable in `config.yaml` (default: `0.08` = 8% expected anomaly rate)
- Returns anomaly score per data point for drill-down analysis

### Engine 2: Root Cause Attribution (Pandas + NumPy)

When an anomaly is detected, the attribution engine performs a **9-dimensional breakdown** — breaking the drop/spike by every available dimension and computing what percentage of the total change each segment accounts for:

```
Dimensions analyzed:
  ├── Region         (Northeast, South, West, Midwest)
  ├── Product / SKU
  ├── Campaign
  ├── Category
  ├── Channel
  ├── Customer Segment
  ├── Time-of-Day / Day-of-Week
  ├── Sales Agent
  └── Geography (Zip / County)
```

Each dimension returns: `delta`, `contribution_pct`, `group_value`, and `confidence`.

### Engine 3: Forecasting (Facebook Prophet + Linear Regression)

**Prophet** is Facebook's open-source time-series forecasting library, designed for business data with seasonal trends. Cosmos uses it to project the next 7–14 days of revenue with full uncertainty quantification:

- **Seasonal decomposition**: extracts trend, weekly seasonality, and yearly seasonality
- **95% confidence intervals**: returns both `lower` and `upper` bands
- **Linear regression fallback**: automatically activates when Prophet fails (insufficient data)
- Handles missing data, outliers, and irregular time series natively

### Engine 4: Recommendation Engine (Custom Scoring)

A **playbook-driven system** that cross-references the anomaly detection result, root cause breakdown, and forecast trajectory to generate prioritized action items:

- Scores recommendations by **priority** (P1/P2/P3), **expected impact** (revenue %, timeline), and **owner** (Marketing, Ops, Finance)
- References a curated playbook of response patterns mapped to anomaly types
- Returns ranked list with: `action`, `priority`, `expected_impact`, `timeline`, `owner`

### Engine 5: Claude LLM — Two Specific Use Points (Anthropic)

Anthropic Claude is used in **exactly two places** in the codebase — both require the user to provide an `ANTHROPIC_API_KEY` in the `.env` file. Without it, both fall back to deterministic template responses automatically.

**Use Point 1 — `llm/explain.py` (Stage 7 of /analyze pipeline)**

After data is uploaded and the full 6-stage analysis completes, Claude generates a concise 3-sentence executive narrative. The entire structured pipeline output is passed as grounded context — Claude never invents numbers:

```
Prompt context passed to Claude:
  METRIC SIGNALS:   revenue/orders/AOV with % change + anomaly flags
  ROOT CAUSE:       top contributing dimensions with % attribution
  FORECAST:         7-14 day prediction
  RECOMMENDED ACTIONS: P1/P2/P3 priority actions
→ Claude outputs: 3-sentence executive briefing
```

**Use Point 2 — `llm/chat.py` (POST /chat endpoint)**

After data has been uploaded and analyzed, users can ask natural language follow-up questions via the AI assistant. Claude answers grounded entirely in the pipeline context — no generic responses:

```json
POST /chat
{
  "question": "Which region is driving the decline?",
  "context": { /* full pipeline output */ },
  "api_key": "sk-ant-..." // optional: user's own key
}
→ Claude outputs: data-specific answer (max 3 sentences)
```

**Important**: The `confidence` score (0.0–0.95) returned in the response is computed **deterministically** — it is NOT generated by Claude. It is calculated based on signal strength: anomaly severity, revenue delta magnitude, root cause count, forecast consistency, etc.

- **Model**: `claude-haiku-4-5-20251001` (configurable to `claude-sonnet-4-6` in config.yaml)
- **Max tokens**: 300 (explain.py) / 200 (chat.py)
- **Fallback**: 100% deterministic template fallback for both use points when API is unavailable

---

## Live Deployment

```
Production Frontend:  https://6nmkmjhh5i.us-east-1.awsapprunner.com
API Health Check:     https://bpc53g62fh.us-east-1.awsapprunner.com/health
```

**Infrastructure specs (AWS App Runner + ECR):**

| Service | Specs | Monthly Cost |
|---------|-------|--------------|
| Frontend (Next.js) | 0.25 vCPU / 1.0 GB RAM | ~$5/month idle |
| Backend (FastAPI) | 0.25 vCPU / 0.5 GB RAM | ~$3/month idle |
| Container Registry | ECR private repositories | Cents |

**Total idle cost: ~$8/month** — designed for presentation and enterprise demo scale.

---

## Quick Start

### Local Development

```bash
# Clone repository
git clone https://github.com/Vivek-Kommareddy/COSMOS-INTELLIGENCE.git
cd COSMOS-INTELLIGENCE

# Backend setup
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Run the full 7-stage pipeline
make run
# or
python run_pipeline.py --pretty --html

# Start API server (http://localhost:8000/docs)
make api

# Run frontend
cd client && npm install && npm run dev   # → http://localhost:3000
```

### Run Tests (44 test cases)

```bash
pytest -v --cov=src tests/
```

### Docker (Single Command)

```bash
docker-compose up --build
```

---

## API Reference

Base URL (production): `https://bpc53g62fh.us-east-1.awsapprunner.com`

All endpoints return structured JSON with `timestamp`, `processing_time_ms`, and `confidence`.

### `GET /health`
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2026-04-10T12:30:45Z",
  "uptime_seconds": 86400
}
```

### `GET /analyze` — Full 7-Stage Pipeline
Runs all engines: ingest → transform → detect → attribute → forecast → recommend → synthesize.

```json
{
  "anomaly_detected": true,
  "severity": "CRITICAL",
  "root_cause": [
    { "dimension": "region", "group_value": "West", "delta": -0.32, "contribution_pct": 62.4 }
  ],
  "forecast_values": [102000, 103400, 104900],
  "forecast_confidence_lower": [95000, 96400, 97900],
  "forecast_confidence_upper": [109000, 110400, 111900],
  "recommendation": [
    {
      "action": "Reactivate Campaign A in West region",
      "priority": "P1",
      "expected_impact": "+15-25% revenue recovery",
      "timeline": "48 hours",
      "owner": "Marketing"
    }
  ],
  "explanation": "Revenue declined 22.4% primarily driven by the West region...",
  "confidence": 0.87,
  "llm_powered": true
}
```

### `GET /forecast` — 7-Day Forecast Only
```bash
GET /forecast
```
Returns Prophet-powered 7-day predictions with upper/lower 95% confidence bands.

### `POST /upload` — Upload Your CSV
```bash
POST /upload
Content-Type: multipart/form-data
file: <your-business-data.csv>
```
Uploads, processes, and runs the full pipeline on your dataset. Returns full `DecisionResponse`.

### `POST /chat` — AI Q&A (Claude-Powered)
```bash
POST /chat
Content-Type: application/json

{
  "question": "Which region is driving the decline?",
  "context": { /* pipeline output */ }
}
```
Ask any question about your data. Claude answers grounded in your specific dataset.

### `DELETE /session` — Hard Delete All Data
```bash
DELETE /session
```
Permanently and irreversibly deletes: raw CSV → processed data → pipeline outputs → AI context cache. GDPR/CCPA compliant.

```json
{
  "status": "deleted",
  "items_deleted": ["raw_csv", "processed_data", "outputs", "ai_context"],
  "timestamp": "2026-04-10T12:30:45Z"
}
```

---

## Project Structure

```
COSMOS-INTELLIGENCE/
│
├── server/                              # FastAPI backend (Python 3.10+)
│   │
│   ├── app/engine/                      # Core intelligence engine
│   │   ├── api/
│   │   │   └── main.py                  # FastAPI app — all 7 REST endpoints + CORS
│   │   │
│   │   ├── ingestion/
│   │   │   └── ingest.py                # Stage 1 — Load CSV, auto-detect schema
│   │   │
│   │   ├── processing/
│   │   │   └── transform.py             # Stage 2 — Clean, validate, aggregate
│   │   │
│   │   ├── anomaly/
│   │   │   └── detect.py                # Stage 3 — Isolation Forest multi-metric
│   │   │
│   │   ├── root_cause/
│   │   │   └── analyze.py               # Stage 4 — 9-dimension root cause attribution
│   │   │
│   │   ├── forecasting/
│   │   │   └── forecast.py              # Stage 5 — Prophet + linear regression
│   │   │
│   │   ├── recommendation/
│   │   │   └── recommend.py             # Stage 6 — Playbook-driven action engine
│   │   │
│   │   ├── llm/
│   │   │   ├── explain.py               # Stage 7 — Claude API: executive narrative
│   │   │   └── chat.py                  # Claude API: AI Q&A for /chat endpoint
│   │   │
│   │   ├── aws/
│   │   │   ├── s3_ops.py                # S3 upload/download
│   │   │   ├── glue_ops.py              # AWS Glue ETL orchestration
│   │   │   ├── athena_ops.py            # SQL queries via Athena
│   │   │   ├── lambda_handler.py        # Lambda entry point
│   │   │   ├── eventbridge_ops.py       # EventBridge scheduling
│   │   │   ├── setup.py                 # One-command AWS bootstrap
│   │   │   ├── glue_etl_script.py       # ETL script for Glue jobs
│   │   │   └── cloudformation.yaml      # Infrastructure-as-Code
│   │   │
│   │   ├── reporting/
│   │   │   ├── html_report.py           # HTML executive brief generator
│   │   │   └── cli_output.py            # Rich CLI formatting
│   │   │
│   │   └── utils/
│   │       ├── helpers.py               # Config loading, path management
│   │       └── logger.py                # Structured JSON logging (CloudWatch-ready)
│   │
│   ├── data/
│   │   ├── raw/source.csv               # Demo dataset (the project runs on this)
│   │   └── processed/processed.csv      # Cleaned & aggregated pipeline output
│   │
│   ├── tests/                           # 44 pytest test cases
│   │   ├── conftest.py                  # Shared test fixtures
│   │   ├── test_transform.py            # 8 cases — data cleaning & aggregation
│   │   ├── test_anomaly.py              # 8 cases — Isolation Forest, severity
│   │   ├── test_forecast.py             # 7 cases — Prophet, confidence intervals
│   │   ├── test_recommend.py            # 8 cases — priority, impact scoring
│   │   └── test_pipeline.py             # 13 cases — end-to-end integration
│   │
│   ├── config/
│   │   └── config.yaml                  # All tunable pipeline parameters
│   │
│   ├── run_pipeline.py                  # 7-stage CLI orchestrator
│   ├── requirements.txt                 # Pinned Python dependencies
│   └── Dockerfile                       # Backend container build
│
├── client/                              # Next.js 16.2.3 frontend
│   ├── app/
│   │   ├── page.tsx                     # Landing page (hero, pipeline, features)
│   │   ├── layout.tsx                   # Root layout + metadata
│   │   ├── upload/
│   │   │   ├── page.tsx                 # File upload + demo trigger
│   │   │   └── UploadClient.tsx         # Client-side upload component
│   │   ├── dashboard/
│   │   │   └── page.tsx                 # Interactive results dashboard + AI chat
│   │   └── api/
│   │       └── health/route.ts          # Frontend health check endpoint
│   │
│   ├── components/
│   │   └── PlotlyChart.tsx              # Interactive chart component
│   │
│   ├── next.config.ts                   # standalone output (90% size reduction)
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── data/
│   └── sample_datasets/                 # 3 sample datasets for testing
│       ├── sample_retail_sales.csv      # Retail industry employees dataset
│       ├── sample_ecommerce.csv         # E-commerce industry employees dataset
│       └── sample_saas_metrics.csv      # SaaS/Tech industry employees dataset
│
├── docs/
│   └── cosmos-intelligence-platform-documentation.docx
│
├── .env.example                         # Environment variable template
├── .gitignore
├── .dockerignore
├── Makefile                             # make run / make api / make demo
├── Dockerfile                           # Root multi-stage container build
├── docker-compose.yml                   # Local dev orchestration
└── README.md
```

---

## Configuration

### `config.yaml` Reference

| Setting | Default | Description |
|---------|---------|-------------|
| `anomaly.contamination` | `0.08` | Expected anomaly fraction (0.0–1.0) |
| `anomaly.tracked_metrics` | `[revenue, orders, avg_order_value]` | Metrics for multi-metric detection |
| `forecast.periods` | `7` | Days to forecast ahead |
| `forecast.include_confidence_intervals` | `true` | Include 95% CI bands |
| `llm.model` | `claude-haiku-4-5-20251001` | Swap to `claude-sonnet-4-6` for higher quality |
| `llm.max_tokens` | `300` | Max tokens in LLM narrative |
| `llm.fallback_to_deterministic` | `true` | Template fallback if API unavailable |
| `api.enable_auth` | `false` | Require `X-API-Key` header |
| `data.lookback_days` | `14` | Historical window for analysis |
| `aws.region` | `us-east-1` | AWS region for cloud services |

### Environment Variables (`.env`)

```bash
ANTHROPIC_API_KEY=sk-ant-...        # Required for LLM explanations
API_KEY=cosmos-secret-2025          # Optional: API key auth
AWS_ACCESS_KEY_ID=AKIA...           # AWS credentials (cloud deployment)
AWS_SECRET_ACCESS_KEY=...
```

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend** | Next.js 16.2.3, React, Framer Motion | SSR, 3D animations, standalone Docker build |
| **Backend** | FastAPI, Python 3.10+, Uvicorn | Async, auto-docs, Pydantic validation |
| **Anomaly Detection** | scikit-learn (Isolation Forest) | Unsupervised, no labeled data required |
| **Forecasting** | Facebook Prophet, statsmodels | Seasonal decomposition, robust CI |
| **Data Processing** | Pandas, NumPy | Fast aggregation, transformation |
| **LLM** | Anthropic Claude (Haiku/Sonnet) | Grounded, low-hallucination business narrative |
| **Visualization** | Plotly | Interactive HTML reports |
| **Testing** | pytest (44 cases) | Full coverage across all pipeline stages |
| **Containerization** | Docker, docker-compose | Dev-to-prod consistency |
| **Cloud Hosting** | AWS App Runner | Managed, auto-scaling, zero-ops |
| **Container Registry** | AWS ECR (private) | Secure image storage |
| **Cloud Storage** | AWS S3 | Raw data, outputs, audit logs |
| **ETL** | AWS Glue | Serverless data transformation at scale |
| **Query Engine** | AWS Athena | SQL on S3 without infrastructure |
| **Scheduling** | AWS EventBridge | Pipeline scheduling, event routing |
| **Observability** | AWS CloudWatch | Structured JSON logs, alarms |
| **Security** | AWS IAM, KMS | Fine-grained access control, encryption |
| **Styling** | Tailwind CSS | Rapid UI development |
| **UI Animations** | Three.js, Framer Motion | Premium 3D dashboard effects |

---

## Data Privacy

Cosmos Intelligence is built with **zero-retention by design**:

1. Data is processed **in-memory** — never persisted without explicit user action
2. `DELETE /session` permanently removes: raw CSV, processed data, all pipeline outputs, AI context cache
3. No background processes, no analytics tracking of uploaded data
4. **GDPR/CCPA compliant** deletion procedures
5. All `.md`, `CLAUDE*`, and `AGENTS*` files are excluded from Docker images via `.dockerignore`

---

## Performance

| Metric | Value |
|--------|-------|
| Full 7-stage pipeline | 1–3 seconds |
| Forecast only | ~500ms |
| API with Claude | 2–5 seconds (LLM latency) |
| Concurrent requests (FastAPI async) | 1,000+ |
| CSV input tested up to | 1M rows |
| Test suite | 44 cases, ~2.3s runtime |

---

## Deployment — AWS App Runner

```bash
# Build and push to ECR (automated script)
./deploy_to_ecr.sh

# Or manually via CloudFormation
aws cloudformation deploy \
  --template-file server/app/engine/aws/cloudformation.yaml \
  --stack-name cosmos-intelligence \
  --capabilities CAPABILITY_NAMED_IAM
```

AWS services provisioned:

| Service | Role |
|---------|------|
| **App Runner** | Managed container hosting — frontend + backend |
| **ECR** | Private Docker image registry |
| **S3** | Raw uploads, processed data, output storage |
| **Glue** | Serverless ETL at dataset scale |
| **Athena** | SQL analytics on S3 |
| **Lambda** | Serverless pipeline execution |
| **EventBridge** | Scheduled pipeline runs |
| **CloudWatch** | Logs, metrics, alarms |
| **IAM** | Role-based access, `AppRunnerECRAccessRole` |
| **KMS** | Optional encryption for sensitive data |

---

## Test Suite

```bash
# Full suite with coverage
pytest -v --cov=src --cov-report=term-missing tests/

# Individual modules
pytest tests/test_anomaly.py -v
pytest tests/test_forecast.py -v
```

| Module | Tests | What's Covered |
|--------|-------|----------------|
| Transform | 8 | Data cleaning, aggregation, edge cases |
| Anomaly | 8 | Isolation Forest, severity scoring, multi-metric |
| Forecast | 7 | Prophet, confidence intervals, linear fallback |
| Recommend | 8 | Priority scoring, impact calculation, ownership |
| Pipeline | 13 | End-to-end integration, API contract |

---

## Roadmap

- **Phase 1** ✅ Core platform — anomaly detection, root cause, forecasting, recommendations, REST API, AWS deployment
- **Phase 2** — Multi-tenant SaaS: user auth, workspace isolation, RBAC, billing
- **Phase 3** — Real-time streaming: Kafka/Kinesis, sub-second detection, live dashboards
- **Phase 4** — Custom ML: fine-tuned Claude on business data, domain-specific models

---

## License

MIT License — see [LICENSE](LICENSE) for full terms.

---

<div align="center">

**✦ ARCHITECTED BY VIVEK KOMMAREDDY ✦**

[GitHub](https://github.com/Vivek-Kommareddy) · [Repository](https://github.com/Vivek-Kommareddy/COSMOS-INTELLIGENCE)

*Cosmos Intelligence — Where raw data becomes executive decisions.*

</div>
