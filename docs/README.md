# Developer Documentation

## AICTE AI Grant & Funding Finder for Startups

> Deep-dive technical reference for contributors, reviewers, and developers.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Repository Layout](#repository-layout)
3. [Local Development Setup](#local-development-setup)
4. [Environment Variables Reference](#environment-variables-reference)
5. [Backend Architecture](#backend-architecture)
6. [IBM Granite Integration](#ibm-granite-integration)
7. [Matching Engine](#matching-engine)
8. [API Reference](#api-reference)
9. [Data Models](#data-models)
10. [Frontend (Streamlit + HTML Dashboard)](#frontend)
11. [Running Tests](#running-tests)
12. [Docker Deployment](#docker-deployment)
13. [Grant Data Sources](#grant-data-sources)
14. [Contributing](#contributing)

---

## System Overview

The platform has two complementary interfaces:

| Interface | Entry Point | Purpose |
|-----------|-------------|---------|
| **Streamlit App** | `app.py` | Quick-start standalone demo — no backend server needed |
| **FastAPI Backend** | `backend/app/main.py` | Production REST API + React/HTML frontend |

Both share the same IBM Granite integration logic and the same grant data seed.

---

## Repository Layout

```
AI-Grant-And-Funding-Finder-For-Startups/
│
├── README.md                         # Project overview & quick start
├── app.json                          # Deployment manifest (Heroku / Railway)
├── app.py                            # Standalone Streamlit application
├── docker-compose.yml                # Full-stack Docker orchestration
├── requirements.txt                  # Root-level Python dependencies
│
├── backend/                          # FastAPI production backend
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── app/
│       ├── main.py                   # App factory + lifespan hooks
│       ├── core/
│       │   ├── config.py             # Pydantic-settings (reads .env)
│       │   ├── database.py           # SQLAlchemy engine + session factory
│       │   └── logging.py            # Structured logging setup
│       ├── models/
│       │   └── models.py             # ORM: StartupProfile, Grant, GrantApplication
│       ├── schemas/
│       │   └── schemas.py            # Pydantic v2 request/response schemas
│       ├── api/
│       │   └── routes/
│       │       ├── startups.py       # POST/GET /api/v1/startups
│       │       ├── grants.py         # GET/POST /api/v1/grants
│       │       └── proposals.py      # POST /api/v1/proposals/generate
│       └── services/
│           ├── granite_service.py    # IBM watsonx.ai REST wrapper
│           ├── matching_engine.py    # Hybrid rule-based + AI scoring
│           ├── grant_service.py      # DB CRUD + seed loader
│           └── scraper_service.py    # Grant aggregation (8+ sources)
│
├── frontend/
│   └── index.html                    # Static single-page dashboard
│
├── screenshots/
│   ├── dashboard.png                 # App screenshot
│   ├── langflow_workflow.png         # LangFlow pipeline diagram
│   └── architecture.png             # System architecture diagram
│
└── docs/
    └── README.md                     # This file
```

---

## Local Development Setup

### Prerequisites

- Python 3.11+
- An IBM Cloud account (Lite tier is sufficient)
- A watsonx.ai project with Granite model access

### Step 1 — Clone and configure

```bash
git clone https://github.com/your-username/AI-Grant-And-Funding-Finder-For-Startups.git
cd AI-Grant-And-Funding-Finder-For-Startups
cp .env.example .env          # fill in your IBM keys
```

### Step 2A — Run the Streamlit demo (no server required)

```bash
pip install -r requirements.txt
streamlit run app.py
# Opens at http://localhost:8501
```

### Step 2B — Run the FastAPI backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# API docs at http://localhost:8000/api/docs
```

### Step 3 — Open the HTML dashboard

```
frontend/index.html   →  open directly in any browser (points to localhost:8000)
```

---

## Environment Variables Reference

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `IBM_WATSONX_API_KEY` | — | ✅ | IBM Cloud API key |
| `IBM_WATSONX_PROJECT_ID` | — | ✅ | watsonx.ai project ID |
| `IBM_WATSONX_URL` | `https://us-south.ml.cloud.ibm.com` | — | Regional endpoint |
| `IBM_GRANITE_MODEL_ID` | `ibm/granite-13b-chat-v2` | — | Granite model |
| `IBM_COS_API_KEY` | — | — | Cloud Object Storage key |
| `IBM_DISCOVERY_API_KEY` | — | — | Watson Discovery key |
| `DATABASE_URL` | `sqlite:///./grant_finder.db` | — | SQLAlchemy DSN |
| `REDIS_URL` | `redis://localhost:6379/0` | — | Redis DSN |
| `APP_ENV` | `development` | — | `development` / `production` |
| `SECRET_KEY` | `changeme` | ✅ (prod) | Session signing key |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | — | CORS origins (comma-sep) |
| `SCRAPER_REQUEST_DELAY_SECONDS` | `2` | — | Polite crawl delay |

---

## Backend Architecture

The FastAPI app is built with a strict layered architecture:

```
Request → Router → Service → Model / External API → Response
```

### Layers

| Layer | Location | Responsibility |
|-------|----------|---------------|
| **Routers** | `api/routes/` | HTTP binding, validation, error codes |
| **Services** | `services/` | Business logic, AI calls, DB operations |
| **Models** | `models/models.py` | SQLAlchemy ORM (SQLite / PostgreSQL) |
| **Schemas** | `schemas/schemas.py` | Pydantic v2 I/O contracts |
| **Core** | `core/` | Config, DB engine, logging |

### Startup Lifecycle (`lifespan`)

1. `setup_logging()` — structured JSON logs
2. `Base.metadata.create_all()` — creates tables if absent
3. `grant_service.seed_grants()` — inserts 8 curated grants on first run
4. App starts accepting requests

---

## IBM Granite Integration

All AI calls flow through `GraniteService` in [`backend/app/services/granite_service.py`](../backend/app/services/granite_service.py).

### Authentication

Every call obtains a fresh IAM bearer token:

```
IBM Cloud IAM  →  POST /identity/token (apikey grant)  →  access_token
```

### NLP Tasks

| Task | Method | Max Tokens | Temperature | Output |
|------|--------|-----------|-------------|--------|
| Eligibility extraction | `extract_eligibility()` | 400 | 0.1 | JSON object |
| Match scoring | `compute_match_score()` | 500 | 0.2 | JSON `{score, explanation, strong_matches, missing_criteria}` |
| Proposal drafting | `generate_proposal()` | 1500 | 0.4 | 9-section Markdown text |

### Prompt Strategy

All prompts use **structured JSON output** instructions with explicit key lists and the instruction `Return ONLY valid JSON` to minimise parsing failures. Markdown code fences are stripped before `json.loads()`.

---

## Matching Engine

[`matching_engine.py`](../backend/app/services/matching_engine.py) implements a **hybrid scoring** pipeline:

### Rule-based score (max 100 pts)

| Signal | Points |
|--------|--------|
| Domain match (with synonym map) | 30 |
| Stage match | 25 |
| Location match | 20 |
| DPIIT recognition bonus | 10 |
| Keyword overlap (5 pts each, max 3) | 15 |

### AI blending

```
if rule_score >= 30:
    final = (rule_score × 0.4) + (granite_ai_score × 0.6)
else:
    final = rule_score   # skip Granite call to save quota
```

Results are sorted descending and the top-K returned.

---

## API Reference

Base path: `/api/v1`

### Startups

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/startups/` | Create a startup profile |
| `GET` | `/startups/{id}` | Retrieve a startup profile |
| `PUT` | `/startups/{id}` | Update a startup profile |
| `DELETE` | `/startups/{id}` | Delete a startup profile |

### Grants

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/grants/` | List grants with optional filters |
| `GET` | `/grants/{id}` | Full grant detail |
| `POST` | `/grants/search` | AI-powered keyword + profile search |
| `GET` | `/grants/match/{startup_id}` | Personalized top-K ranked matches |

### Proposals

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/proposals/generate` | Generate Granite proposal draft |
| `GET` | `/proposals/{id}` | Retrieve saved draft |

### System

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Liveness + version info |
| `GET` | `/api/docs` | Swagger UI |
| `GET` | `/api/redoc` | ReDoc UI |

---

## Data Models

### StartupProfile

```python
id              UUID (PK)
name            String(255)
domain          String(100)       # "EdTech", "HealthTech", ...
stage           Enum              # idea / prototype / mvp / early_stage / growth / scale
location_country String
location_state  String
founding_year   Integer
team_size       Integer
annual_revenue  Float (INR)
description     Text
keywords        JSON[]
dpiit_recognized Boolean
```

### Grant

```python
id                      UUID (PK)
title                   String(500)
provider                String(255)
description             Text
eligibility_raw         Text
eligibility_structured  JSON{}
funding_amount_min/max  Float
funding_currency        String(10)   # INR / USD
deadline                DateTime
status                  Enum         # open / closing_soon / closed / upcoming
domains                 JSON[]
stages                  JSON[]
locations               JSON[]
tags                    JSON[]
requirements            JSON[]
```

### GrantApplication

```python
id                  UUID (PK)
startup_id          FK → StartupProfile
grant_id            FK → Grant
match_score         Float (0–100)
match_explanation   Text
proposal_draft      Text    # Granite-generated
status              String  # draft / submitted / accepted / rejected
submitted_at        DateTime
```

---

## Frontend

### Streamlit App (`app.py`)

Four pages navigated via a sidebar radio:

| Page | Features |
|------|----------|
| **🏠 Home** | KPI metrics, deadline countdown, how-it-works steps |
| **🔍 Discover Grants** | Filter by domain / stage / location, keyword search, grant cards |
| **🤖 AI Matching** | Select startup profile → ranked matches with score bars, strength/gap analysis |
| **✍️ Proposal Writer** | Select startup + grant → Granite generates 9-section proposal |
| **👤 My Profile** | Create / manage startup profiles |

### HTML Dashboard (`frontend/index.html`)

Static single-page app that calls the FastAPI backend at `http://localhost:8000/api/v1`.

---

## Running Tests

```bash
cd backend
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## Docker Deployment

```bash
# Full stack (API + Redis)
docker-compose up --build

# API only
docker build -t grant-finder ./backend
docker run -p 8000:8000 --env-file .env grant-finder
```

Services:

| Container | Image | Port |
|-----------|-------|------|
| `grant-finder-api` | Python 3.13 / Dockerfile | 8000 |
| `grant-finder-redis` | redis:7-alpine | 6379 |

---

## Grant Data Sources

| Grant | Provider | Region | Max Funding |
|-------|----------|--------|-------------|
| AICTE Idea Lab | AICTE | India | ₹25L |
| SISFS | DPIIT – Startup India | India | ₹50L |
| DST NIDHI Prayas | Dept. of Science & Technology | India | ₹15L |
| MeitY TIDE 2.0 | Ministry of Electronics & IT | India | ₹75L |
| Atal Innovation Mission | NITI Aayog | India | ₹1Cr |
| BIRAC BIG | Dept. of Biotechnology | India | ₹50L |
| Karnataka Elevate 100 | Govt. of Karnataka | Karnataka | ₹50L |
| NSF SBIR Phase I | National Science Foundation | USA | $275K |

Live data is fetched from the Grants.gov public API when `GRANTS_GOV_API_KEY` is set.

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit with a clear message
4. Open a pull request against `main`

Please make sure `pytest tests/ -v` passes before opening a PR.

---

*Built for the AICTE Innovation Challenge · Powered by IBM Granite (watsonx.ai)*
