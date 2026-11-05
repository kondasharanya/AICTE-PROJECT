# AICTE AI Grant & Funding Finder for Startups

> **Built with IBM Granite (watsonx.ai) · IBM Cloud Lite Services**

An end-to-end AI-powered platform that discovers, personalizes, matches, and auto-drafts grant applications for Indian and global startups.

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (HTML/JS Dashboard)                                   │
│  ├─ Grant Discovery & Search                                    │
│  ├─ AI Matching Dashboard                                       │
│  ├─ Proposal Generator UI                                       │
│  └─ Startup Profile Management                                  │
└────────────────────┬────────────────────────────────────────────┘
                     │ REST API (FastAPI)
┌────────────────────▼────────────────────────────────────────────┐
│  Backend (FastAPI + Python)                                     │
│  ├─ /api/v1/startups    – Startup profile CRUD                  │
│  ├─ /api/v1/grants      – Grant discovery + search             │
│  └─ /api/v1/proposals   – AI proposal generation               │
└──────┬──────────────┬────────────────────┬──────────────────────┘
       │              │                    │
┌──────▼──────┐ ┌─────▼──────┐  ┌─────────▼────────────────────┐
│  SQLite DB  │ │  Scraper   │  │  IBM watsonx.ai (Granite)    │
│  (SQLAlch.) │ │  Service   │  │  ├─ Eligibility Extraction   │
└─────────────┘ └─────▼──────┘  │  ├─ Match Scoring            │
                    Seed +       │  └─ Proposal Generation      │
                    Live APIs    └──────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- IBM Cloud account (Lite tier)
- IBM watsonx.ai project with Granite model access

### 1. Clone & Configure

```bash
cd "AICTE-AI Grant And Funding Finder For Startups"
# Edit .env with your IBM API keys
```

### 2. Install & Run Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Open Frontend

```
http://localhost:8000/api/docs     → Swagger UI
frontend/public/index.html         → Open directly in browser (demo mode)
```

### 4. Docker (full stack)

```bash
docker-compose up --build
```

---

## 🔑 IBM Cloud Setup

1. **IBM Cloud Account** → [cloud.ibm.com](https://cloud.ibm.com) (Lite tier is free)
2. **watsonx.ai Project** → [dataplatform.cloud.ibm.com](https://dataplatform.cloud.ibm.com)
3. **API Key** → IBM Cloud → Manage → Access → API Keys → Create
4. **Project ID** → watsonx.ai → Your Project → Manage → General → Project ID
5. Update `.env`:
   ```
   IBM_WATSONX_API_KEY=your_key_here
   IBM_WATSONX_PROJECT_ID=your_project_id_here
   IBM_GRANITE_MODEL_ID=ibm/granite-13b-chat-v2
   ```

---

## 📁 Project Structure

```
AICTE-AI Grant And Funding Finder For Startups/
├── .env                          # Environment variables (IBM API keys)
├── docker-compose.yml            # Docker orchestration
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── app/
│       ├── main.py               # FastAPI app entry point
│       ├── core/
│       │   ├── config.py         # Settings (pydantic-settings)
│       │   ├── database.py       # SQLAlchemy engine
│       │   └── logging.py        # Logging config
│       ├── models/models.py      # ORM models
│       ├── schemas/schemas.py    # Pydantic schemas
│       ├── api/routes/
│       │   ├── startups.py       # Startup profile CRUD
│       │   ├── grants.py         # Grant discovery + AI matching
│       │   └── proposals.py      # Proposal generation
│       └── services/
│           ├── granite_service.py    # IBM Granite integration
│           ├── scraper_service.py    # Grant data aggregation (8+ sources)
│           ├── matching_engine.py    # Hybrid AI + rule-based matching
│           └── grant_service.py      # DB operations
├── frontend/
│   └── public/index.html         # Single-page dashboard
├── tests/
│   └── test_matching.py          # Unit tests
└── docs/
    └── README.md
```

---

## 🤖 IBM Granite Use Cases

| Task | Model | Prompt Strategy |
|------|-------|-----------------|
| Eligibility extraction | `granite-13b-chat-v2` | Structured JSON extraction from raw grant text |
| Match scoring | `granite-13b-chat-v2` | Startup vs. grant profile comparison |
| Proposal generation | `granite-13b-chat-v2` | Long-form structured proposal draft |

---

## 🏆 Grant Sources

| Source | Region | Type |
|--------|--------|------|
| AICTE Idea Lab | India | Government |
| Startup India SISFS | India | Government |
| DST NIDHI Prayas | India | Government |
| MeitY TIDE 2.0 | India | Government |
| AIM – NITI Aayog | India | Government |
| BIRAC BIG | India | Government |
| Karnataka Elevate 100 | Karnataka, India | State |
| NSF SBIR Phase I | USA | Federal |

---

## 🧪 Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## 📜 License

MIT License — For educational / AICTE submission purposes.
