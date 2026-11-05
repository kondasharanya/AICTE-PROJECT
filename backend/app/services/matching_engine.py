"""
Grant matching & personalization engine.
Combines rule-based scoring with IBM Granite AI scoring.
"""
import logging
import time
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session

from app.models.models import Grant, StartupProfile, GrantApplication, StartupStage, GrantStatus
from app.schemas.schemas import GrantMatchResult, GrantRead, GrantSearchRequest
from app.services.granite_service import granite_service

logger = logging.getLogger("grant_finder.matching")


# Domain similarity map – if startup domain is in the value list, it matches the key
DOMAIN_SIMILARITY: dict = {
    "EdTech": ["Education", "E-Learning", "Education Technology", "EdTech"],
    "HealthTech": ["Healthcare", "MedTech", "Health", "Digital Health", "HealthTech"],
    "FinTech": ["Finance", "Financial Technology", "FinTech", "Payments", "InsurTech"],
    "AgriTech": ["Agriculture", "FoodTech", "AgriTech", "Food Technology"],
    "CleanTech": ["Clean Energy", "GreenTech", "Sustainability", "CleanTech", "Renewable Energy"],
    "AI/ML": ["Artificial Intelligence", "Machine Learning", "Data Science", "AI", "ML", "AI/ML"],
    "Biotech": ["Biotechnology", "BioTech", "Life Sciences", "Pharma"],
    "DeepTech": ["Deep Technology", "DeepTech", "Quantum", "Nanotech", "Advanced Materials"],
    "IoT": ["Internet of Things", "IoT", "Smart Devices", "Connected Devices"],
    "SaaS": ["Software", "Cloud", "SaaS", "Enterprise Software", "B2B"],
    "All domains": [],  # special – matches everything
}


def _domain_matches(startup_domain: str, grant_domains: List[str]) -> bool:
    if not grant_domains:
        return True
    if "All domains" in grant_domains:
        return True
    sd = startup_domain.lower()
    for gd in grant_domains:
        if sd in gd.lower() or gd.lower() in sd:
            return True
        # Check similarity map
        for canonical, aliases in DOMAIN_SIMILARITY.items():
            all_names = [canonical] + aliases
            if any(n.lower() == sd for n in all_names) and any(n.lower() == gd.lower() for n in all_names):
                return True
    return False


def _stage_matches(startup_stage: str, grant_stages: List[str]) -> bool:
    if not grant_stages:
        return True
    return startup_stage in grant_stages


def _location_matches(startup_location: str, grant_locations: List[str]) -> bool:
    if not grant_locations:
        return True
    sl = startup_location.lower()
    for loc in grant_locations:
        if loc.lower() == "india" and sl in ["india", ""]:
            return True
        if loc.lower() in sl or sl in loc.lower():
            return True
    return False


def _rule_based_score(startup: StartupProfile, grant: Grant) -> Tuple[float, List[str], List[str]]:
    """
    Fast rule-based scoring before calling Granite.
    Returns (score 0-100, strong_matches, missing_criteria).
    """
    score = 0.0
    strong = []
    missing = []

    # Domain match (30 points)
    if _domain_matches(startup.domain, grant.domains or []):
        score += 30
        strong.append(f"Domain '{startup.domain}' aligns with grant focus areas")
    else:
        missing.append(f"Startup domain '{startup.domain}' may not match grant domains: {', '.join(grant.domains or [])}")

    # Stage match (25 points)
    if _stage_matches(startup.stage.value, grant.stages or []):
        score += 25
        strong.append(f"Startup stage '{startup.stage.value}' is eligible")
    else:
        missing.append(f"Grant targets stages {grant.stages}, startup is at '{startup.stage.value}'")

    # Location match (20 points)
    combined_location = f"{startup.location_state or ''} {startup.location_country or 'India'}".strip()
    if _location_matches(combined_location, grant.locations or []):
        score += 20
        strong.append(f"Location '{combined_location}' matches grant geography")
    else:
        missing.append(f"Grant limited to: {', '.join(grant.locations or [])}")

    # DPIIT bonus (10 points)
    if startup.dpiit_recognized:
        score += 10
        strong.append("DPIIT recognition increases eligibility for Indian government grants")

    # Keyword overlap (15 points)
    startup_keywords = set(k.lower() for k in (startup.keywords or []))
    grant_tags = set(k.lower() for k in (grant.tags or []))
    overlap = startup_keywords & grant_tags
    if overlap:
        kw_score = min(15, len(overlap) * 5)
        score += kw_score
        strong.append(f"Keyword overlap: {', '.join(overlap)}")

    return min(score, 100.0), strong, missing


class MatchingEngine:
    """Hybrid matching engine: rule-based + Granite AI scoring."""

    async def find_matches(
        self,
        startup: StartupProfile,
        grants: List[Grant],
        use_ai_scoring: bool = True,
        top_k: int = 10,
    ) -> List[GrantMatchResult]:
        """
        Score and rank grants for a given startup profile.
        """
        start_time = time.time()
        results = []

        for grant in grants:
            if grant.status == GrantStatus.CLOSED:
                continue

            # Rule-based fast score
            rb_score, strong, missing = _rule_based_score(startup, grant)

            # AI scoring via Granite (for top rule-based candidates)
            if use_ai_scoring and rb_score >= 30:
                try:
                    startup_dict = {
                        "name": startup.name,
                        "domain": startup.domain,
                        "stage": startup.stage.value,
                        "description": startup.description,
                        "location_state": startup.location_state,
                        "location_country": startup.location_country,
                        "dpiit_recognized": startup.dpiit_recognized,
                        "keywords": startup.keywords,
                    }
                    grant_dict = {
                        "title": grant.title,
                        "provider": grant.provider,
                        "description": grant.description,
                        "domains": grant.domains,
                        "stages": grant.stages,
                        "locations": grant.locations,
                        "requirements": grant.requirements,
                        "funding_amount_min": grant.funding_amount_min,
                        "funding_amount_max": grant.funding_amount_max,
                        "funding_currency": grant.funding_currency,
                    }
                    ai_score, ai_explanation, ai_missing, ai_strong = await granite_service.compute_match_score(
                        startup_dict, grant_dict
                    )
                    # Blend: 40% rule-based, 60% AI
                    final_score = (rb_score * 0.4) + (ai_score * 0.6)
                    explanation = ai_explanation
                    strong = ai_strong or strong
                    missing = ai_missing or missing
                except Exception as e:
                    logger.warning(f"AI scoring failed for grant {grant.id}, using rule-based: {e}")
                    final_score = rb_score
                    explanation = f"Match based on domain, stage, and location alignment. Score: {rb_score:.0f}/100"
            else:
                final_score = rb_score
                explanation = f"Match based on domain, stage, and location alignment. Score: {rb_score:.0f}/100"

            results.append(
                GrantMatchResult(
                    grant=GrantRead.model_validate(grant),
                    match_score=round(final_score, 1),
                    match_explanation=explanation,
                    strong_matches=strong,
                    missing_criteria=missing,
                )
            )

        # Sort by match score descending
        results.sort(key=lambda r: r.match_score, reverse=True)
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"Matched {len(results)} grants in {elapsed:.1f}ms")
        return results[:top_k]

    async def generate_proposal(
        self,
        startup: StartupProfile,
        grant: Grant,
        db: Session,
        additional_context: str = "",
    ) -> GrantApplication:
        """Generate a Granite-powered proposal and save it to the DB."""
        startup_dict = {
            "name": startup.name,
            "domain": startup.domain,
            "stage": startup.stage.value,
            "description": startup.description or "",
            "location_state": startup.location_state or "",
            "location_country": startup.location_country or "India",
            "dpiit_recognized": startup.dpiit_recognized,
            "keywords": startup.keywords or [],
        }
        grant_dict = {
            "title": grant.title,
            "provider": grant.provider,
            "description": grant.description or "",
            "requirements": grant.requirements or [],
            "funding_amount_min": grant.funding_amount_min,
            "funding_amount_max": grant.funding_amount_max,
            "funding_currency": grant.funding_currency,
        }

        proposal_text = await granite_service.generate_proposal(startup_dict, grant_dict, additional_context)

        rb_score, strong, missing = _rule_based_score(startup, grant)

        application = GrantApplication(
            startup_id=startup.id,
            grant_id=grant.id,
            match_score=rb_score,
            match_explanation=f"Rule-based score: {rb_score:.0f}/100. {'; '.join(strong[:3])}",
            proposal_draft=proposal_text,
            status="draft",
        )
        db.add(application)
        db.commit()
        db.refresh(application)
        return application


matching_engine = MatchingEngine()
