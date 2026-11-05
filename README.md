# 🚀 AI Grant & Funding Finder for Startups

<div align="center">

**Discover · Match · Apply — Powered by IBM Granite (watsonx.ai)**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![IBM Granite](https://img.shields.io/badge/IBM%20Granite-granite--13b--chat--v2-0043CE?style=flat&logo=ibm&logoColor=white)](https://www.ibm.com/products/watsonx-ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An end-to-end AI-powered platform that **discovers, personalises, matches, and auto-drafts** grant applications for Indian and global startups.

</div>

---

## 📸 Screenshots

> *(Add your screenshots to the `screenshots/` folder before publishing.)*

| Dashboard | AI Matching | Proposal Writer |
|-----------|-------------|-----------------|
| ![Dashboard](screenshots/dashboard.png) | ![Matching](screenshots/architecture.png) | ![LangFlow](screenshots/langflow_workflow.png) |

---

## ✨ Features

- **🔍 Grant Discovery** — 8+ curated Indian & global grants (AICTE, DST, MeitY, BIRAC, NSF) with smart filters
- **🤖 AI Matching** — Hybrid rule-based + IBM Granite scoring (40/60 blend) ranks grants 0–100 for your startup
- **✍️ Proposal Writer** — IBM Granite generates a 9-section professional proposal draft in seconds
- **👤 Startup Profiles** — Domain, stage, location, DPIIT recognition, keyword-based eligibility matching
- **📊 Deadline Tracker** — Live countdown for all open grants
- **🌐 Dual Interface** — Streamlit demo app + FastAPI production backend + static HTML dashboard

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend  (Streamlit · HTML Dashboard · React-ready)           │
│  ├─ Grant Discovery & Search                                    │
│  ├─ AI Matching Dashboard                                       │
│  ├─ Proposal Generator UI                                       │
│  └─ Startup Profile Management                                  │
└────────────────────┬────────────────────────────────────────────┘
                     │ REST API (FastAPI · /api/v1)
┌────────────────────▼────────────────────────────────────────────┐
│  Backend (FastAPI + Python 3.11+)                               │
│  ├─ /api/v1/startups    – Startup profile CRUD                  │
│  ├─ /api/v1/grants      – Grant discovery + AI search           │
│  └─ /api/v1/proposals   – Granite-powered proposal generation   │
└──────┬──────────────┬────────────────────┬──────────────────────┘
       │              │                    │
┌──────▼──────┐ ┌─────▼──────┐  ┌─────────▼────────────────────┐
│  SQLite DB  │ │  Scraper   │  │  IBM watsonx.ai (Granite)    │
│  (SQLAlch.) │ │  Service   │  │  ├─ Eligibility Extraction   │
└─────────────┘ └─────▼──────┘  │  ├─ Match Scoring (0–100)   │
                    Seed +       │  └─ Proposal Generation      │
                    Live APIs    └──────────────────────────────┘
```

---

## 📁 Project Structure

```
AI-Grant-And-Funding-Finder-For-Startups/
│
├── README.md                              # You are here
├── app.json                               # Deployment manifest (Heroku / Railway)
├── app.py                                 # Standalone Streamlit demo
├── docker-compose.yml                     # Full-stack Docker orchestration
├── requirements.txt                       # Root-level Python dependencies
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── app/
│       ├── main.py                        # FastAPI app factory + lifespan
│       ├── core/
│       │   ├── config.py                  # Pydantic-settings (.env reader)
│       │   ├── database.py                # SQLAlchemy engine + session
│       │   └── logging.py                 # Structured logging
│       ├── models/
│       │   └── models.py                  # ORM: StartupProfile · Grant · GrantApplication
│       ├── schemas/
│       │   └── schemas.py                 # Pydantic v2 I/O schemas
│       ├── api/
│       │   └── routes/
│       │       ├── startups.py            # POST/GET /api/v1/startups
│       │       ├── grants.py              # GET/POST /api/v1/grants + /match
│       │       └── proposals.py           # POST /api/v1/proposals/generate
│       └── services/
│           ├── granite_service.py         # IBM watsonx.ai REST wrapper
│           ├── matching_engine.py         # Hybrid rule-based + AI scoring
│           ├── grant_service.py           # DB CRUD + seed loader
│           └── scraper_service.py         # Grant aggregation (8+ sources)
│
├── frontend/
│   └── index.html                         # Static single-page dashboard
│
├── screenshots/
│   ├── dashboard.png
│   ├── langflow_workflow.png
│   └── architecture.png
│
└── docs/
    └── README.md                          # Full developer documentation
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- IBM Cloud account ([Lite tier — free](https://cloud.ibm.com))
- IBM watsonx.ai project with Granite model access

### Option A — Streamlit demo (no server required)

```bash
git clone https://github.com/your-username/AI-Grant-And-Funding-Finder-For-Startups.git
cd AI-Grant-And-Funding-Finder-For-Startups

pip install -r requirements.txt
cp .env.example .env          # fill in your IBM API keys
streamlit run app.py
# Opens at http://localhost:8501
```

### Option B — FastAPI production backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# Swagger UI → http://localhost:8000/api/docs
# HTML dashboard → open frontend/index.html in your browser
```

### Option C — Docker (full stack)

```bash
docker-compose up --build
# API → http://localhost:8000
# Redis → localhost:6379
```

---

## 🔑 IBM Cloud Setup

1. **Create an IBM Cloud account** → [cloud.ibm.com](https://cloud.ibm.com) *(Lite tier is free)*
2. **Create a watsonx.ai project** → [dataplatform.cloud.ibm.com](https://dataplatform.cloud.ibm.com)
3. **Generate an API Key** → IBM Cloud → Manage → Access (IAM) → API Keys → Create
4. **Copy your Project ID** → watsonx.ai → Your Project → Manage → General → Project ID
5. **Update your `.env`:**

```env
IBM_WATSONX_API_KEY=your_api_key_here
IBM_WATSONX_PROJECT_ID=your_project_id_here
IBM_GRANITE_MODEL_ID=ibm/granite-13b-chat-v2
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

---

## 🤖 IBM Granite Use Cases

| Task | Model | Strategy | Output |
|------|-------|----------|--------|
| Eligibility extraction | `granite-13b-chat-v2` | Structured JSON prompt from raw grant text | `{stages, domains, requirements, funding}` |
| Match scoring | `granite-13b-chat-v2` | Startup vs. grant profile comparison | Score 0–100 + explanation |
| Proposal generation | `granite-13b-chat-v2` | Long-form structured prompt | 9-section proposal draft |

**Hybrid Scoring Pipeline:**

| Signal | Rule-based Points |
|--------|-------------------|
| Domain match (with synonym map) | 30 pts |
| Stage match | 25 pts |
| Location match | 20 pts |
| DPIIT recognition bonus | 10 pts |
| Keyword overlap (5 pts each) | up to 15 pts |

Final score = **(rule-based × 0.4) + (IBM Granite AI × 0.6)**

---

## 🏆 Grant Sources

| Grant | Provider | Region | Funding |
|-------|----------|--------|---------|
| AICTE Idea Lab | AICTE | India | ₹5L – ₹25L |
| Startup India SISFS | DPIIT – Startup India | India | ₹20L – ₹50L |
| DST NIDHI Prayas | Dept. of Science & Technology | India | ₹10L – ₹15L |
| MeitY TIDE 2.0 | Ministry of Electronics & IT | India | ₹15L – ₹75L |
| AIM Grants | NITI Aayog | India | ₹10L – ₹1Cr |
| BIRAC BIG | Dept. of Biotechnology | India | ₹50L |
| Karnataka Elevate 100 | Govt. of Karnataka | Karnataka | ₹20L – ₹50L |
| NSF SBIR Phase I | National Science Foundation | USA | $275K |

---

## 🧪 Running Tests

```bash
cd backend
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## 🌊 LangFlow Workflow

The [`langflow_workflow.json`](langflow_workflow.json) file contains the complete LangFlow pipeline for the grant matching and proposal generation flow.

To import: open [LangFlow](https://www.langflow.org/) → **Import JSON** → select `langflow_workflow.json`

---

## 📖 Documentation

Full developer documentation is available in [`docs/README.md`](docs/README.md), covering:

- Detailed architecture walkthrough
- Environment variables reference
- API endpoint catalogue
- Data model schema
- Contributing guide

---

## 📜 License

[MIT License](LICENSE) — Built for the AICTE Innovation Challenge · Powered by IBM Granite (watsonx.ai)
