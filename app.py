"""
AICTE AI Grant & Funding Finder for Startups
Streamlit Application – main entry point
Run: streamlit run app.py
"""

import streamlit as st
import json
import os
import sqlite3
import uuid
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Optional

# ── Page config (must be first Streamlit call) ─────────────────────────────────
st.set_page_config(
    page_title="AICTE AI Grant Finder",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load .env ──────────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

IBM_WATSONX_API_KEY    = os.getenv("IBM_WATSONX_API_KEY", "")
IBM_WATSONX_PROJECT_ID = os.getenv("IBM_WATSONX_PROJECT_ID", "")
IBM_WATSONX_URL        = os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
IBM_GRANITE_MODEL_ID   = os.getenv("IBM_GRANITE_MODEL_ID", "ibm/granite-13b-chat-v2")

IAM_URL  = "https://iam.cloud.ibm.com/identity/token"
GEN_URL  = f"{IBM_WATSONX_URL}/ml/v1/text/generation?version=2023-05-29"

# ── Seed grant data ────────────────────────────────────────────────────────────
NOW = datetime.utcnow()
GRANTS = [
    {
        "id": "g1",
        "title": "AICTE Idea Lab – Startup Grant 2025",
        "provider": "AICTE",
        "description": "AICTE supports early-stage technology startups affiliated with AICTE-approved institutions for prototype development, PoC, and MVP building in AI, robotics, green energy, and healthcare.",
        "eligibility": "DPIIT registered. Founder from AICTE institution. Stage: idea/prototype/MVP. ≤3 years old.",
        "funding_min": 500_000,
        "funding_max": 2_500_000,
        "currency": "INR",
        "deadline": NOW + timedelta(days=45),
        "url": "https://www.aicte-india.org/schemes/startups",
        "domains": ["EdTech", "HealthTech", "AI/ML", "Robotics", "CleanTech"],
        "stages": ["idea", "prototype", "mvp"],
        "locations": ["India"],
        "tags": ["AICTE", "DPIIT", "student startup"],
        "requirements": ["DPIIT certificate", "AICTE affiliation letter", "Business plan", "Team details"],
    },
    {
        "id": "g2",
        "title": "Startup India Seed Fund Scheme (SISFS)",
        "provider": "DPIIT – Startup India",
        "description": "Provides financial assistance for PoC, prototype development, product trials, market entry, and commercialization through incubators.",
        "eligibility": "DPIIT recognized. Incorporated < 2 years. No prior GoI funding > ₹10L. Incubator-associated.",
        "funding_min": 2_000_000,
        "funding_max": 5_000_000,
        "currency": "INR",
        "deadline": NOW + timedelta(days=90),
        "url": "https://seedfund.startupindia.gov.in",
        "domains": ["All domains"],
        "stages": ["idea", "prototype", "mvp"],
        "locations": ["India"],
        "tags": ["seed fund", "DPIIT", "incubator", "government"],
        "requirements": ["DPIIT certificate", "Incubator letter", "Business plan", "Financial projections (3yr)", "Incorporation certificate"],
    },
    {
        "id": "g3",
        "title": "DST NIDHI Prayas Grant",
        "provider": "Dept. of Science & Technology (DST)",
        "description": "Supports innovators to develop working prototypes from deep-tech ideas. Focus: biotech, nanotech, AI, clean energy.",
        "eligibility": "Indian citizen. Idea-to-prototype stage. Deep-tech focus. Age 18–45 for individuals.",
        "funding_min": 1_000_000,
        "funding_max": 1_500_000,
        "currency": "INR",
        "deadline": NOW + timedelta(days=60),
        "url": "https://dst.gov.in/nidhi",
        "domains": ["DeepTech", "Biotech", "CleanTech", "AI/ML", "Nanotech"],
        "stages": ["idea", "prototype"],
        "locations": ["India"],
        "tags": ["DST", "deep tech", "NIDHI", "innovation"],
        "requirements": ["Innovation description", "Technical feasibility", "Identity proof"],
    },
    {
        "id": "g4",
        "title": "MeitY TIDE 2.0",
        "provider": "MeitY (Ministry of Electronics & IT)",
        "description": "Supports ICT-based startups in AI, IoT, cybersecurity, blockchain with funding, mentoring, and infrastructure.",
        "eligibility": "ICT startup registered in India. DPIIT preferred. Prototype to early commercialization. Revenue < ₹25Cr.",
        "funding_min": 1_500_000,
        "funding_max": 7_500_000,
        "currency": "INR",
        "deadline": NOW + timedelta(days=30),
        "url": "https://tide20.meity.gov.in",
        "domains": ["AI/ML", "IoT", "Cybersecurity", "Blockchain", "EdTech", "FinTech"],
        "stages": ["prototype", "mvp", "early_stage"],
        "locations": ["India"],
        "tags": ["MeitY", "ICT", "technology", "incubation"],
        "requirements": ["DPIIT recognition", "Incorporation certificate", "Product demo", "Revenue proof"],
    },
    {
        "id": "g5",
        "title": "Atal Innovation Mission (AIM)",
        "provider": "NITI Aayog",
        "description": "Grants for startups working on agriculture, health, energy, water, and infrastructure challenges via Atal Incubation Centres.",
        "eligibility": "Indian startup. AIC-associated. Social impact orientation. DPIIT preferred.",
        "funding_min": 1_000_000,
        "funding_max": 10_000_000,
        "currency": "INR",
        "deadline": NOW + timedelta(days=75),
        "url": "https://aim.gov.in",
        "domains": ["AgriTech", "HealthTech", "CleanTech", "WaterTech", "Infrastructure"],
        "stages": ["idea", "prototype", "mvp", "early_stage"],
        "locations": ["India"],
        "tags": ["AIM", "NITI Aayog", "social impact"],
        "requirements": ["AIC support letter", "Problem statement", "Impact description", "Team details"],
    },
    {
        "id": "g6",
        "title": "BIRAC BIG – Biotech Ignition Grant",
        "provider": "BIRAC – Dept. of Biotechnology",
        "description": "Supports early-stage biotech startups and innovators to validate ideas with scientific merit and commercial potential.",
        "eligibility": "Indian biotech startup/innovator. Early stage. Through BIRAC-authorized incubator. Focus: healthcare/agri/industrial biotech.",
        "funding_min": 5_000_000,
        "funding_max": 5_000_000,
        "currency": "INR",
        "deadline": NOW + timedelta(days=50),
        "url": "https://birac.nic.in/big.php",
        "domains": ["Biotech", "HealthTech", "AgriTech"],
        "stages": ["idea", "prototype"],
        "locations": ["India"],
        "tags": ["BIRAC", "biotech", "healthcare"],
        "requirements": ["Biotech concept", "Scientific feasibility", "BIRAC incubator letter", "IP landscape"],
    },
    {
        "id": "g7",
        "title": "Karnataka Elevate 100",
        "provider": "Govt. of Karnataka – KSTDC",
        "description": "Identifies top 100 Karnataka startups and provides funding, mentoring, market access, and government procurement opportunities.",
        "eligibility": "Registered in Karnataka. < 5 years old. DPIIT preferred. Any domain.",
        "funding_min": 2_000_000,
        "funding_max": 5_000_000,
        "currency": "INR",
        "deadline": NOW + timedelta(days=20),
        "url": "https://startup.karnataka.gov.in/elevate",
        "domains": ["All domains"],
        "stages": ["mvp", "early_stage", "growth"],
        "locations": ["Karnataka"],
        "tags": ["Karnataka", "state grant", "Elevate"],
        "requirements": ["Karnataka registration", "DPIIT certificate", "Live product demo", "Pitch deck"],
    },
    {
        "id": "g8",
        "title": "NSF SBIR Phase I Grant",
        "provider": "NSF – USA",
        "description": "Funds US-based small businesses to conduct feasibility research on deep-tech, STEM-based solutions with high commercial potential.",
        "eligibility": "US-incorporated for-profit. < 500 employees. PI primarily employed by company. Deep-tech/STEM focus.",
        "funding_min": 275_000,
        "funding_max": 275_000,
        "currency": "USD",
        "deadline": NOW + timedelta(days=120),
        "url": "https://seedfund.nsf.gov",
        "domains": ["DeepTech", "AI/ML", "Biotech", "CleanTech"],
        "stages": ["idea", "prototype", "mvp"],
        "locations": ["USA"],
        "tags": ["NSF", "SBIR", "USA", "federal"],
        "requirements": ["US incorporation", "Technical narrative", "Commercialization plan", "Budget justification"],
    },
]

# ── IBM Granite helpers ────────────────────────────────────────────────────────

def get_iam_token(api_key: str) -> Optional[str]:
    """Fetch IAM bearer token from IBM Cloud."""
    try:
        resp = httpx.post(
            IAM_URL,
            data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": api_key},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()["access_token"]
    except Exception as e:
        st.warning(f"IBM IAM token error: {e}")
        return None


def granite_generate(prompt: str, max_tokens: int = 800) -> str:
    """Call IBM Granite text generation."""
    if not IBM_WATSONX_API_KEY or IBM_WATSONX_API_KEY == "your_ibm_watsonx_api_key_here":
        return "[Demo Mode] IBM Granite API key not configured. Add your key to .env to enable AI generation."

    token = get_iam_token(IBM_WATSONX_API_KEY)
    if not token:
        return "[Error] Could not obtain IBM IAM token."

    try:
        resp = httpx.post(
            GEN_URL,
            json={
                "model_id": IBM_GRANITE_MODEL_ID,
                "input": prompt,
                "parameters": {
                    "decoding_method": "greedy",
                    "max_new_tokens": max_tokens,
                    "temperature": 0.3,
                    "repetition_penalty": 1.1,
                },
                "project_id": IBM_WATSONX_PROJECT_ID,
            },
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["results"][0]["generated_text"].strip()
    except Exception as e:
        return f"[Granite Error] {e}"


def granite_match_score(startup: dict, grant: dict) -> dict:
    prompt = f"""You are a grant matching expert. Score how well this startup matches this grant.

Startup: {json.dumps(startup, indent=2)}
Grant: {json.dumps({k: grant[k] for k in ['title','provider','eligibility','domains','stages','locations']}, indent=2)}

Respond ONLY with valid JSON like:
{{"score": 82, "explanation": "...", "strengths": ["..."], "gaps": ["..."]}}"""
    raw = granite_generate(prompt, max_tokens=300)
    try:
        raw = raw.strip().strip("```json").strip("```").strip()
        return json.loads(raw)
    except Exception:
        return {"score": 0, "explanation": raw, "strengths": [], "gaps": []}


def granite_proposal(startup: dict, grant: dict, context: str = "") -> str:
    ctx = f"\nExtra context: {context}" if context else ""
    prompt = f"""You are an expert grant writer. Write a professional grant application proposal.

Startup:
- Name: {startup['name']}
- Domain: {startup['domain']}
- Stage: {startup['stage']}
- Description: {startup.get('description', 'N/A')}
- Location: {startup.get('state', '')}, India
- DPIIT Recognized: {startup.get('dpiit', False)}
- Keywords: {', '.join(startup.get('keywords', []))}

Grant: {grant['title']} by {grant['provider']}
Description: {grant['description']}
Requirements: {', '.join(grant['requirements'])}{ctx}

Write a structured proposal with sections:
1. Executive Summary
2. Problem Statement
3. Proposed Solution & Innovation
4. Technology Stack
5. Market Opportunity
6. Team & Capacity
7. Budget Justification
8. Expected Impact & Social Value
9. Conclusion

Be professional, specific, and compelling:"""
    return granite_generate(prompt, max_tokens=1500)


# ── Rule-based match score ─────────────────────────────────────────────────────

def rule_score(startup: dict, grant: dict) -> tuple:
    score = 0
    strong, gaps = [], []

    dom = startup.get("domain", "")
    g_domains = grant.get("domains", [])
    if "All domains" in g_domains or any(dom.lower() in d.lower() or d.lower() in dom.lower() for d in g_domains):
        score += 30; strong.append(f"Domain '{dom}' matches")
    else:
        gaps.append(f"Domain '{dom}' vs grant domains: {', '.join(g_domains)}")

    stage = startup.get("stage", "")
    if stage in grant.get("stages", []):
        score += 25; strong.append(f"Stage '{stage}' is eligible")
    else:
        gaps.append(f"Stage '{stage}' not in {grant.get('stages', [])}")

    loc = (startup.get("state", "") + " India").lower()
    g_locs = [l.lower() for l in grant.get("locations", [])]
    if any(l in loc or loc in l for l in g_locs) or "india" in g_locs:
        score += 20; strong.append("Location eligible")
    else:
        gaps.append(f"Location mismatch: {grant.get('locations', [])}")

    if startup.get("dpiit"):
        score += 10; strong.append("DPIIT recognition boosts eligibility")

    kw = set(k.lower() for k in startup.get("keywords", []))
    tg = set(t.lower() for t in grant.get("tags", []))
    overlap = kw & tg
    if overlap:
        bonus = min(15, len(overlap) * 5)
        score += bonus; strong.append(f"Keyword match: {', '.join(overlap)}")

    return min(int(score), 100), strong, gaps


# ── Formatting helpers ─────────────────────────────────────────────────────────

def fmt_inr(n: float) -> str:
    if n >= 10_000_000: return f"₹{n/10_000_000:.1f} Cr"
    if n >= 100_000:    return f"₹{n/100_000:.0f} L"
    if n >= 1000:       return f"₹{n/1000:.0f} K"
    return f"₹{n:.0f}"


def fmt_funding(g: dict) -> str:
    sym = "$" if g["currency"] == "USD" else "₹"
    lo, hi = g["funding_min"], g["funding_max"]
    def f(n): return f"{n/10_000_000:.1f}Cr" if n >= 10_000_000 else f"{n/100_000:.0f}L" if n >= 100_000 else f"{n/1000:.0f}K" if n >= 1000 else str(int(n))
    if lo == hi: return f"{sym}{f(lo)}"
    return f"{sym}{f(lo)} – {sym}{f(hi)}"


def days_left(dt: datetime) -> int:
    return max(0, (dt - datetime.utcnow()).days)


# ── Styling ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #1c1c1c; }
.ibm-header { background: linear-gradient(90deg,#0f62fe,#0043ce);
  color:white; padding:1.2rem 1.5rem; border-radius:6px; margin-bottom:1.5rem; }
.ibm-header h1 { margin:0; font-size:1.6rem; font-weight:700; }
.ibm-header p  { margin:0.3rem 0 0; font-size:0.9rem; opacity:0.85; }
.grant-card { background:#f8f9ff; border:1px solid #d0e2ff;
  border-radius:6px; padding:1.1rem 1.3rem; margin-bottom:0.8rem; }
.grant-card h4 { margin:0 0 0.3rem; color:#0043ce; font-size:1rem; }
.grant-provider { color:#6f6f6f; font-size:0.82rem; margin-bottom:0.5rem; }
.score-high  { color:#198038; font-weight:700; }
.score-mid   { color:#ff832b; font-weight:700; }
.score-low   { color:#da1e28; font-weight:700; }
.tag { display:inline-block; padding:2px 8px; border-radius:3px;
  font-size:0.72rem; font-weight:600; margin:2px; }
.tag-blue   { background:#d0e2ff; color:#0043ce; }
.tag-green  { background:#defbe6; color:#198038; }
.tag-orange { background:#ffd6a5; color:#8a3800; }
.tag-purple { background:#e8daff; color:#6929c4; }
.tag-red    { background:#fff1f1; color:#a2191f; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ibm-header">
  <h1>🚀 AICTE AI Grant & Funding Finder</h1>
  <p>Powered by <strong>IBM Granite (watsonx.ai)</strong> · IBM Cloud Lite Services · For Indian Startups</p>
</div>
""", unsafe_allow_html=True)

# ── IBM key status badge ────────────────────────────────────────────────────────
if IBM_WATSONX_API_KEY and IBM_WATSONX_API_KEY != "your_ibm_watsonx_api_key_here":
    st.success("✅ IBM watsonx.ai connected – AI features active")
else:
    st.warning("⚠️ IBM API key not set – running in demo mode. Add `IBM_WATSONX_API_KEY` to `.env` to enable Granite AI.")

# ── Sidebar navigation ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📋 Navigation")
    page = st.radio("", [
        "⚡ Dashboard",
        "🔍 Discover Grants",
        "🎯 AI Matching",
        "📝 Generate Proposal",
        "🏢 Startup Profile",
        "🔌 API Info",
    ], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**IBM Services Used**")
    st.markdown("• `ibm/granite-13b-chat-v2`")
    st.markdown("• IBM IAM Authentication")
    st.markdown("• IBM Cloud Lite (free tier)")
    st.markdown("---")
    st.caption("AICTE AI Grant Finder v1.0")

# ── Session state init ─────────────────────────────────────────────────────────
if "profiles" not in st.session_state:
    st.session_state.profiles = []
if "proposals" not in st.session_state:
    st.session_state.proposals = []

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "⚡ Dashboard":
    st.subheader("📊 Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Grants", len(GRANTS))
    c2.metric("Startup Profiles", len(st.session_state.profiles))
    c3.metric("Proposals Generated", len(st.session_state.proposals))
    c4.metric("Funding Range", "₹5L – ₹1Cr+")

    st.markdown("---")
    st.markdown("### 🚀 How to Use This App")
    steps = [
        ("1️⃣ Create Startup Profile", "Go to **🏢 Startup Profile** and fill in your startup details."),
        ("2️⃣ Discover Grants", "Browse **🔍 Discover Grants** to explore 8+ active funding opportunities."),
        ("3️⃣ AI Matching", "Use **🎯 AI Matching** – IBM Granite scores each grant for your startup."),
        ("4️⃣ Generate Proposal", "Go to **📝 Generate Proposal** – Granite drafts a full application."),
    ]
    for title, desc in steps:
        with st.expander(title, expanded=False):
            st.write(desc)

    st.markdown("---")
    st.markdown("### 📌 Closing Soon")
    soon = sorted([g for g in GRANTS if days_left(g["deadline"]) <= 30], key=lambda x: x["deadline"])
    if soon:
        for g in soon:
            dl = days_left(g["deadline"])
            st.markdown(f"""<div class="grant-card">
<h4>{g['title']}</h4>
<div class="grant-provider">{g['provider']}</div>
<span class="tag tag-red">⏰ {dl} days left</span>
<span class="tag tag-blue">{fmt_funding(g)}</span>
</div>""", unsafe_allow_html=True)
    else:
        st.info("No grants closing within 30 days.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DISCOVER GRANTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Discover Grants":
    st.subheader("🔍 Discover Grants")

    col1, col2, col3 = st.columns(3)
    with col1:
        domain_filter = st.selectbox("Filter by Domain", ["All"] + sorted(set(d for g in GRANTS for d in g["domains"] if d != "All domains")))
    with col2:
        stage_filter = st.selectbox("Filter by Stage", ["All", "idea", "prototype", "mvp", "early_stage", "growth"])
    with col3:
        loc_filter = st.selectbox("Filter by Location", ["All", "India", "Karnataka", "USA"])

    search_q = st.text_input("🔎 Search", placeholder="Type keyword, provider, or domain...")

    filtered = []
    for g in GRANTS:
        if domain_filter != "All" and domain_filter not in g["domains"] and "All domains" not in g["domains"]:
            continue
        if stage_filter != "All" and stage_filter not in g["stages"]:
            continue
        if loc_filter != "All" and loc_filter not in g["locations"]:
            continue
        if search_q:
            haystack = f"{g['title']} {g['provider']} {' '.join(g['domains'])} {' '.join(g['tags'])}".lower()
            if search_q.lower() not in haystack:
                continue
        filtered.append(g)

    st.markdown(f"**{len(filtered)} grant(s) found**")

    for g in filtered:
        dl = days_left(g["deadline"])
        dl_tag = f'<span class="tag tag-red">⚠ {dl}d left</span>' if dl <= 14 else f'<span class="tag tag-green">🗓 {dl}d left</span>'
        domain_tags = " ".join(f'<span class="tag tag-blue">{d}</span>' for d in g["domains"][:3])
        stage_tags  = " ".join(f'<span class="tag tag-purple">{s}</span>' for s in g["stages"][:3])
        loc_tags    = " ".join(f'<span class="tag tag-orange">{l}</span>' for l in g["locations"])

        with st.expander(f"**{g['title']}** — {fmt_funding(g)}", expanded=False):
            st.markdown(f"""<div class="grant-card">
<h4>{g['title']}</h4>
<div class="grant-provider">🏛 {g['provider']}</div>
{domain_tags} {stage_tags} {loc_tags} {dl_tag}
</div>""", unsafe_allow_html=True)

            st.markdown(f"**Description:** {g['description']}")
            st.markdown(f"**Eligibility:** {g['eligibility']}")
            st.markdown(f"**Funding:** {fmt_funding(g)}")
            st.markdown(f"**Deadline:** {g['deadline'].strftime('%d %b %Y')} ({dl} days left)")
            st.markdown("**Requirements:**")
            for r in g["requirements"]:
                st.markdown(f"  - {r}")
            st.link_button("🔗 Apply / Learn More", g["url"])

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: AI MATCHING
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🎯 AI Matching":
    st.subheader("🎯 AI-Powered Grant Matching")
    st.markdown("IBM Granite scores each grant against your startup profile and explains the match.")

    if not st.session_state.profiles:
        st.warning("No startup profiles found. Please create one in **🏢 Startup Profile** first.")
        st.stop()

    profile_names = [p["name"] for p in st.session_state.profiles]
    selected_name = st.selectbox("Select Startup Profile", profile_names)
    startup = next(p for p in st.session_state.profiles if p["name"] == selected_name)

    col1, col2 = st.columns(2)
    top_k   = col1.slider("Top K results", 3, 8, 5)
    use_ai  = col2.checkbox("Use IBM Granite AI scoring", value=True,
                             help="Unchecked = rule-based only (faster, no API call)")

    if st.button("🚀 Run AI Matching", type="primary"):
        results = []
        progress = st.progress(0, text="Scoring grants…")

        for i, grant in enumerate(GRANTS):
            rb_score, strong, gaps = rule_score(startup, grant)
            progress.progress((i + 1) / len(GRANTS), text=f"Scoring: {grant['title'][:40]}…")

            if use_ai and rb_score >= 30:
                with st.spinner(f"IBM Granite scoring: {grant['title'][:40]}…"):
                    ai_result = granite_match_score(startup, grant)
                ai_score = float(ai_result.get("score", rb_score))
                explanation = ai_result.get("explanation", "")
                strengths   = ai_result.get("strengths", strong)
                gaps_ai     = ai_result.get("gaps", gaps)
                final_score = round(rb_score * 0.4 + ai_score * 0.6, 1)
            else:
                final_score = float(rb_score)
                explanation = f"Rule-based score: {rb_score}/100"
                strengths, gaps_ai = strong, gaps

            results.append({
                "grant": grant,
                "score": final_score,
                "explanation": explanation,
                "strengths": strengths,
                "gaps": gaps_ai,
            })

        progress.empty()
        results.sort(key=lambda r: r["score"], reverse=True)

        st.markdown(f"### 🏆 Top {top_k} Matches for **{startup['name']}**")
        for rank, r in enumerate(results[:top_k], 1):
            g = r["grant"]
            sc = r["score"]
            color_cls = "score-high" if sc >= 70 else "score-mid" if sc >= 40 else "score-low"
            bar_color = "#198038" if sc >= 70 else "#ff832b" if sc >= 40 else "#da1e28"

            with st.expander(f"#{rank}  {g['title']}  —  Score: {sc:.0f}/100", expanded=(rank <= 3)):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"**Provider:** {g['provider']}")
                    st.markdown(f"**Funding:** {fmt_funding(g)}")
                    st.markdown(f"**Deadline:** {g['deadline'].strftime('%d %b %Y')} ({days_left(g['deadline'])}d left)")
                with col_b:
                    st.markdown(f"<p style='font-size:2.2rem;font-weight:700;color:{bar_color};margin:0'>{sc:.0f}%</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color:{bar_color};font-size:0.8rem;margin:0'>Match Score</p>", unsafe_allow_html=True)

                st.progress(int(sc) / 100)
                st.markdown(f"**AI Analysis:** {r['explanation']}")

                if r["strengths"]:
                    st.markdown("✅ **Strengths:** " + " · ".join(r["strengths"][:3]))
                if r["gaps"]:
                    st.markdown("⚠️ **Gaps:** " + " · ".join(r["gaps"][:2]))

                if st.button(f"📝 Generate Proposal for {g['title'][:30]}…", key=f"prop_{g['id']}"):
                    st.session_state["proposal_grant_id"] = g["id"]
                    st.session_state["proposal_startup"]  = startup
                    st.info("Go to **📝 Generate Proposal** page to generate the full draft.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: GENERATE PROPOSAL
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📝 Generate Proposal":
    st.subheader("📝 Generate Grant Proposal")
    st.markdown("IBM Granite writes a tailored, structured proposal draft for your selected grant.")

    if not st.session_state.profiles:
        st.warning("Create a startup profile first in **🏢 Startup Profile**.")
        st.stop()

    col1, col2 = st.columns(2)
    with col1:
        profile_names = [p["name"] for p in st.session_state.profiles]
        sel_startup_name = st.selectbox("Startup Profile", profile_names)
        startup = next(p for p in st.session_state.profiles if p["name"] == sel_startup_name)
    with col2:
        grant_titles = [g["title"] for g in GRANTS]
        # Pre-select if coming from matching page
        default_idx = 0
        if "proposal_grant_id" in st.session_state:
            ids = [g["id"] for g in GRANTS]
            if st.session_state["proposal_grant_id"] in ids:
                default_idx = ids.index(st.session_state["proposal_grant_id"])
        sel_grant_title = st.selectbox("Grant", grant_titles, index=default_idx)

    grant = next(g for g in GRANTS if g["title"] == sel_grant_title)
    extra_context = st.text_area("Additional Context (optional)",
        placeholder="Pilot results, partnerships, awards, specific tech stack, team expertise…",
        height=100)

    st.markdown("---")
    col_info1, col_info2, col_info3 = st.columns(3)
    col_info1.info(f"**Startup:** {startup['name']}")
    col_info2.info(f"**Grant:** {grant['title'][:35]}…")
    col_info3.info(f"**Funding:** {fmt_funding(grant)}")

    if st.button("✍️ Generate Proposal with IBM Granite", type="primary"):
        with st.spinner("IBM Granite is writing your proposal… (this may take 20–40 seconds)"):
            proposal_text = granite_proposal(startup, grant, extra_context)

        st.success("✅ Proposal generated!")
        st.markdown("### 📄 Generated Proposal Draft")
        st.markdown(f"> *AI-generated by IBM Granite · {IBM_GRANITE_MODEL_ID} · {datetime.now().strftime('%d %b %Y %H:%M')}*")
        st.text_area("Proposal Draft", proposal_text, height=600, label_visibility="collapsed")

        # Save to session
        st.session_state.proposals.append({
            "startup": startup["name"],
            "grant":   grant["title"],
            "text":    proposal_text,
            "created": datetime.now().strftime("%d %b %Y %H:%M"),
        })

        # Download button
        st.download_button(
            label="⬇️ Download Proposal (.txt)",
            data=proposal_text,
            file_name=f"proposal_{startup['name'].replace(' ','_')}_{grant['id']}.txt",
            mime="text/plain",
        )

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: STARTUP PROFILE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏢 Startup Profile":
    st.subheader("🏢 Create Startup Profile")

    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            name    = st.text_input("Startup Name *", placeholder="e.g. TechBridge AI")
            domain  = st.selectbox("Domain / Industry *", [
                "EdTech","HealthTech","FinTech","AgriTech","CleanTech",
                "AI/ML","Biotech","DeepTech","IoT","SaaS","Other"
            ])
            stage   = st.selectbox("Startup Stage *", [
                "idea","prototype","mvp","early_stage","growth","scale"
            ])
        with col2:
            state    = st.text_input("State", placeholder="e.g. Karnataka")
            year     = st.number_input("Founding Year", min_value=2000, max_value=2026, value=2022)
            team     = st.number_input("Team Size", min_value=1, max_value=500, value=5)

        description = st.text_area("Description", placeholder="What does your startup do? Problem, solution, technology…", height=100)
        keywords_raw = st.text_input("Keywords (comma-separated)", placeholder="AI, healthcare, NLP, B2B, SaaS")
        dpiit = st.checkbox("DPIIT Recognized")

        submitted = st.form_submit_button("💾 Save Profile", type="primary")
        if submitted:
            if not name or not domain:
                st.error("Startup Name and Domain are required.")
            else:
                profile = {
                    "id":          str(uuid.uuid4()),
                    "name":        name,
                    "domain":      domain,
                    "stage":       stage,
                    "state":       state,
                    "year":        year,
                    "team":        team,
                    "description": description,
                    "keywords":    [k.strip() for k in keywords_raw.split(",") if k.strip()],
                    "dpiit":       dpiit,
                }
                st.session_state.profiles.append(profile)
                st.success(f"✅ Profile for **{name}** saved!")
                st.balloons()

    if st.session_state.profiles:
        st.markdown("---")
        st.markdown("### 📋 Saved Profiles")
        for p in st.session_state.profiles:
            with st.expander(f"**{p['name']}** — {p['domain']} · {p['stage']}"):
                col1, col2, col3 = st.columns(3)
                col1.markdown(f"**Domain:** {p['domain']}")
                col2.markdown(f"**Stage:** {p['stage']}")
                col3.markdown(f"**DPIIT:** {'✅' if p['dpiit'] else '❌'}")
                if p.get("description"):
                    st.markdown(f"**Description:** {p['description']}")
                if p.get("keywords"):
                    st.markdown(f"**Keywords:** {', '.join(p['keywords'])}")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: API INFO
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔌 API Info":
    st.subheader("🔌 Backend API")
    st.markdown("""
The FastAPI backend is also available (separate from Streamlit).

**Start the API server:**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | Health check |
| `/api/v1/startups/` | POST | Register startup |
| `/api/v1/grants/` | GET | List all grants |
| `/api/v1/grants/search` | POST | AI-powered search |
| `/api/v1/grants/match/{id}` | GET | Personalized matching |
| `/api/v1/proposals/generate` | POST | Generate proposal |

**Swagger UI:** [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
""")

    st.markdown("### ⚙️ IBM Configuration")
    st.code(f"""
IBM_WATSONX_API_KEY    = {"✅ SET" if IBM_WATSONX_API_KEY and IBM_WATSONX_API_KEY != "your_ibm_watsonx_api_key_here" else "❌ NOT SET"}
IBM_WATSONX_PROJECT_ID = {"✅ SET" if IBM_WATSONX_PROJECT_ID and IBM_WATSONX_PROJECT_ID != "your_ibm_watsonx_project_id_here" else "❌ NOT SET"}
IBM_GRANITE_MODEL_ID   = {IBM_GRANITE_MODEL_ID}
IBM_WATSONX_URL        = {IBM_WATSONX_URL}
""", language="ini")

    if not (IBM_WATSONX_API_KEY and IBM_WATSONX_API_KEY != "your_ibm_watsonx_api_key_here"):
        st.info("""
**Get your IBM API keys (free):**
1. Sign up at [cloud.ibm.com](https://cloud.ibm.com) (Lite tier is free)
2. Create a watsonx.ai project at [dataplatform.cloud.ibm.com](https://dataplatform.cloud.ibm.com)
3. Generate API key: IBM Cloud → Manage → Access → API Keys
4. Copy Project ID: watsonx.ai → Your Project → Manage → General
5. Update `.env` with both values and restart: `streamlit run app.py`
""")
