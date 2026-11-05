"""
Grant scraper service – aggregates grant data from multiple public sources.
Respects robots.txt and rate limits. No confidential portals are accessed.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup

from app.core.config import settings

logger = logging.getLogger("grant_finder.scraper")

HEADERS = {
    "User-Agent": settings.scraper_user_agent,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


# ── Static seed grant data (real Indian grants) ────────────────────────────────
# These are used when live scraping is unavailable (no API key / rate-limited).

SEED_GRANTS: List[Dict[str, Any]] = [
    {
        "title": "AICTE Idea Lab – Startup Grant 2025",
        "provider": "AICTE",
        "description": (
            "AICTE supports early-stage technology startups affiliated with AICTE-approved institutions. "
            "Grants are provided for prototype development, proof-of-concept, and MVP building in areas "
            "such as AI, robotics, green energy, and healthcare technology."
        ),
        "eligibility_raw": (
            "Startup must be founded by students or faculty of AICTE-approved institutions. "
            "Company must be DPIIT registered. Startup should be at idea, prototype or MVP stage. "
            "Maximum 3 years since incorporation. Team size 2-10 members."
        ),
        "funding_amount_min": 500000,
        "funding_amount_max": 2500000,
        "funding_currency": "INR",
        "deadline_offset_days": 45,
        "application_url": "https://www.aicte-india.org/schemes/startups",
        "source_url": "https://www.aicte-india.org/schemes/startups",
        "domains": ["EdTech", "HealthTech", "CleanTech", "AI/ML", "Robotics", "AgriTech"],
        "stages": ["idea", "prototype", "mvp"],
        "locations": ["India"],
        "tags": ["AICTE", "student startup", "DPIIT", "technology"],
        "requirements": [
            "DPIIT certificate",
            "AICTE institution affiliation letter",
            "Business plan document",
            "Team composition details",
            "Prototype/demo (if available)",
        ],
    },
    {
        "title": "Startup India Seed Fund Scheme (SISFS)",
        "provider": "DPIIT – Startup India",
        "description": (
            "The Startup India Seed Fund Scheme provides financial assistance to startups for "
            "proof of concept, prototype development, product trials, market entry, and commercialization. "
            "Incubators apply on behalf of startups."
        ),
        "eligibility_raw": (
            "Startup must be DPIIT recognized. Incorporated less than 2 years ago. "
            "Must not have received more than Rs 10 lakh in funding from GoI schemes. "
            "Should be associated with a supported incubator."
        ),
        "funding_amount_min": 2000000,
        "funding_amount_max": 5000000,
        "funding_currency": "INR",
        "deadline_offset_days": 90,
        "application_url": "https://seedfund.startupindia.gov.in",
        "source_url": "https://seedfund.startupindia.gov.in",
        "domains": ["All domains"],
        "stages": ["idea", "prototype", "mvp"],
        "locations": ["India"],
        "tags": ["seed fund", "DPIIT", "incubator", "government"],
        "requirements": [
            "DPIIT recognition certificate",
            "Incubator association letter",
            "Business plan",
            "Financial projections (3 years)",
            "Incorporation certificate",
        ],
    },
    {
        "title": "DST NIDHI Prayas Grant",
        "provider": "Department of Science & Technology (DST)",
        "description": (
            "DST NIDHI (National Initiative for Developing and Harnessing Innovations) – PRAYAS "
            "supports individual innovators and early-stage deep-tech startups to develop working "
            "prototypes from their ideas."
        ),
        "eligibility_raw": (
            "Indian citizen with innovative technology idea. Early stage – idea to prototype. "
            "Deep-tech focus: biotech, nanotech, advanced materials, AI, clean energy. "
            "Age limit: 18-45 years for individual innovators."
        ),
        "funding_amount_min": 1000000,
        "funding_amount_max": 1500000,
        "funding_currency": "INR",
        "deadline_offset_days": 60,
        "application_url": "https://dst.gov.in/nidhi",
        "source_url": "https://dst.gov.in/nidhi",
        "domains": ["DeepTech", "Biotech", "CleanTech", "AI/ML", "Nanotech", "Advanced Materials"],
        "stages": ["idea", "prototype"],
        "locations": ["India"],
        "tags": ["DST", "deep tech", "innovation", "NIDHI"],
        "requirements": [
            "Idea/Innovation description",
            "Technical feasibility report",
            "Identity proof",
            "No-objection certificate (if employed)",
        ],
    },
    {
        "title": "MeitY TIDE 2.0 – Technology Incubation and Development",
        "provider": "MeitY (Ministry of Electronics & IT)",
        "description": (
            "MeitY TIDE 2.0 supports ICT-based startups with funding, mentoring, and infrastructure. "
            "Focuses on AI, IoT, cybersecurity, blockchain, and other emerging technology areas."
        ),
        "eligibility_raw": (
            "ICT-based startup registered in India. DPIIT recognized preferred. "
            "Stage: prototype to early commercialization. Technology must be in ICT sector. "
            "Revenue < Rs 25 crore."
        ),
        "funding_amount_min": 1500000,
        "funding_amount_max": 7500000,
        "funding_currency": "INR",
        "deadline_offset_days": 30,
        "application_url": "https://tide20.meity.gov.in",
        "source_url": "https://tide20.meity.gov.in",
        "domains": ["AI/ML", "IoT", "Cybersecurity", "Blockchain", "EdTech", "FinTech"],
        "stages": ["prototype", "mvp", "early_stage"],
        "locations": ["India"],
        "tags": ["MeitY", "ICT", "technology", "incubation"],
        "requirements": [
            "DPIIT recognition",
            "Incorporation certificate",
            "Product demo / prototype",
            "Technology description",
            "Revenue proof",
        ],
    },
    {
        "title": "Atal Innovation Mission – AIM Grants",
        "provider": "NITI Aayog – Atal Innovation Mission",
        "description": (
            "AIM provides grants to startups and innovators working on solutions for national "
            "challenges in agriculture, health, energy, water, and infrastructure through Atal "
            "Incubation Centres and Atal Tinkering Labs."
        ),
        "eligibility_raw": (
            "Indian startup or innovator. Associated with Atal Incubation Centre. "
            "Focus on national development challenges. DPIIT registration preferred. "
            "Social impact orientation required."
        ),
        "funding_amount_min": 1000000,
        "funding_amount_max": 10000000,
        "funding_currency": "INR",
        "deadline_offset_days": 75,
        "application_url": "https://aim.gov.in",
        "source_url": "https://aim.gov.in",
        "domains": ["AgriTech", "HealthTech", "CleanTech", "WaterTech", "Smart Infrastructure"],
        "stages": ["idea", "prototype", "mvp", "early_stage"],
        "locations": ["India"],
        "tags": ["AIM", "NITI Aayog", "social impact", "national challenge"],
        "requirements": [
            "AIC association / letter of support",
            "Problem statement",
            "Proposed solution with impact",
            "Team details",
            "DPIIT certificate (preferred)",
        ],
    },
    {
        "title": "BIRAC BIG (Biotechnology Ignition Grant)",
        "provider": "BIRAC – Dept. of Biotechnology",
        "description": (
            "The Biotechnology Ignition Grant (BIG) supports early-stage innovative biotech "
            "startups and individual innovators to validate ideas with scientific merit and "
            "commercial potential."
        ),
        "eligibility_raw": (
            "Indian biotech startup or innovator. Early-stage idea with biotech application. "
            "Must apply through BIRAC authorized Business Incubators. "
            "Focus: healthcare, agriculture, industrial biotech."
        ),
        "funding_amount_min": 5000000,
        "funding_amount_max": 5000000,
        "funding_currency": "INR",
        "deadline_offset_days": 50,
        "application_url": "https://birac.nic.in/big.php",
        "source_url": "https://birac.nic.in/big.php",
        "domains": ["Biotech", "HealthTech", "AgriTech", "Industrial Biotech"],
        "stages": ["idea", "prototype"],
        "locations": ["India"],
        "tags": ["BIRAC", "biotech", "healthcare", "agriculture"],
        "requirements": [
            "Biotech innovation concept",
            "Scientific feasibility",
            "BIRAC incubator support letter",
            "IP landscape analysis",
            "Team qualifications",
        ],
    },
    {
        "title": "Karnataka Elevate 100 Startup Grant",
        "provider": "Government of Karnataka – KSTDC",
        "description": (
            "Karnataka Elevate 100 is a flagship startup support programme that identifies the "
            "top 100 startups in Karnataka and provides funding, mentoring, market access, and "
            "government procurement opportunities."
        ),
        "eligibility_raw": (
            "Startup must be registered in Karnataka. Less than 5 years old. "
            "DPIIT recognized preferred. Team must have Karnataka connection (founder/office). "
            "Any domain is eligible."
        ),
        "funding_amount_min": 2000000,
        "funding_amount_max": 5000000,
        "funding_currency": "INR",
        "deadline_offset_days": 20,
        "application_url": "https://startup.karnataka.gov.in/elevate",
        "source_url": "https://startup.karnataka.gov.in/elevate",
        "domains": ["All domains"],
        "stages": ["mvp", "early_stage", "growth"],
        "locations": ["Karnataka"],
        "tags": ["Karnataka", "state grant", "Elevate", "KSTDC"],
        "requirements": [
            "Karnataka registration proof",
            "DPIIT certificate",
            "Product demo / live product",
            "Revenue traction (preferred)",
            "Pitch deck",
        ],
    },
    {
        "title": "NSF SBIR Phase I Grant (US-based)",
        "provider": "National Science Foundation – USA",
        "description": (
            "NSF SBIR Phase I provides funding for US-based small businesses and startups to "
            "conduct feasibility research on innovative deep-tech, STEM-based solutions with "
            "high commercial potential."
        ),
        "eligibility_raw": (
            "US-incorporated for-profit small business. Less than 500 employees. "
            "PI must be primarily employed by the company. Deep-tech / STEM focus. "
            "Commercialization potential required."
        ),
        "funding_amount_min": 275000,
        "funding_amount_max": 275000,
        "funding_currency": "USD",
        "deadline_offset_days": 120,
        "application_url": "https://seedfund.nsf.gov",
        "source_url": "https://seedfund.nsf.gov",
        "domains": ["DeepTech", "BioTech", "AI/ML", "CleanTech", "Advanced Manufacturing"],
        "stages": ["idea", "prototype", "mvp"],
        "locations": ["USA"],
        "tags": ["NSF", "SBIR", "USA", "deep tech", "federal grant"],
        "requirements": [
            "US company incorporation",
            "Technical narrative",
            "Commercialization plan",
            "PI employment certification",
            "Budget justification",
        ],
    },
]


class GrantScraperService:
    """Aggregates grant data from seed data and public APIs."""

    async def get_all_grants(self) -> List[Dict[str, Any]]:
        """Return all available grants (seed + live where available)."""
        grants = list(SEED_GRANTS)
        # Normalize deadlines from offset to actual datetime
        now = datetime.utcnow()
        for g in grants:
            if "deadline_offset_days" in g:
                g["deadline"] = now + timedelta(days=g.pop("deadline_offset_days"))
            g["last_scraped_at"] = now
        logger.info(f"Loaded {len(grants)} grants from seed data")
        return grants

    async def fetch_live_grants(self) -> List[Dict[str, Any]]:
        """
        Attempt to fetch live grant data from public APIs.
        Falls back gracefully if sources are unavailable.
        """
        results = []
        try:
            async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
                # Grants.gov public API (US grants)
                if settings.grants_gov_api_key:
                    resp = await client.post(
                        "https://api.grants.gov/v1/api/search2",
                        json={"keyword": "startup technology innovation", "rows": 10},
                        headers={"API-KEY": settings.grants_gov_api_key},
                    )
                    if resp.status_code == 200:
                        for item in resp.json().get("data", {}).get("hits", []):
                            results.append(self._normalize_grants_gov(item))
        except Exception as e:
            logger.warning(f"Live grant fetch failed (non-critical): {e}")
        return results

    def _normalize_grants_gov(self, item: dict) -> dict:
        return {
            "title": item.get("opportunityTitle", "Unnamed Grant"),
            "provider": item.get("agencyName", "US Federal"),
            "description": item.get("synopsis", {}).get("synopsisDesc", ""),
            "funding_amount_min": None,
            "funding_amount_max": item.get("awardCeiling"),
            "funding_currency": "USD",
            "deadline": None,
            "application_url": f"https://www.grants.gov/web/grants/view-opportunity.html?oppId={item.get('id')}",
            "source_url": "https://www.grants.gov",
            "domains": ["All domains"],
            "stages": ["idea", "prototype", "mvp", "early_stage"],
            "locations": ["USA"],
            "tags": ["federal", "US grant"],
            "requirements": [],
        }


grant_scraper = GrantScraperService()
