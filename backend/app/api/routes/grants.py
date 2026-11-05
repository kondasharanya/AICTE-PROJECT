"""
API routes – Grant discovery, search, and matching.
"""
import time
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.models import StartupProfile, GrantStatus
from app.schemas.schemas import (
    GrantRead, GrantMatchResult, GrantSearchRequest, GrantSearchResponse
)
from app.services.grant_service import grant_service
from app.services.matching_engine import matching_engine

router = APIRouter(prefix="/grants", tags=["Grant Discovery"])


@router.get("/", response_model=List[GrantRead])
async def list_grants(
    domain: Optional[str] = Query(None, description="Filter by domain (e.g. EdTech)"),
    stage: Optional[str] = Query(None, description="Filter by stage (e.g. mvp)"),
    location: Optional[str] = Query(None, description="Filter by location (e.g. Karnataka)"),
    status: Optional[GrantStatus] = Query(GrantStatus.OPEN),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List all available grants with optional filters."""
    grants = grant_service.get_grants(db, domain=domain, stage=stage, location=location,
                                       status=status, limit=limit, offset=offset)
    return grants


@router.get("/{grant_id}", response_model=GrantRead)
def get_grant(grant_id: str, db: Session = Depends(get_db)):
    """Get full details of a specific grant."""
    grant = grant_service.get_grant_by_id(db, grant_id)
    if not grant:
        raise HTTPException(status_code=404, detail="Grant not found")
    return grant


@router.post("/search", response_model=GrantSearchResponse)
async def search_grants(request: GrantSearchRequest, db: Session = Depends(get_db)):
    """
    AI-powered grant search and matching.
    Provide a startup_id for personalized scoring via IBM Granite.
    """
    start_time = time.time()

    grants = grant_service.get_grants(
        db,
        domain=request.domain,
        stage=request.stage.value if request.stage else None,
        location=request.location,
        status=request.status,
        limit=200,  # Fetch more for matching, then re-rank
    )

    if not grants:
        return GrantSearchResponse(total=0, results=[], query_time_ms=0.0)

    # If startup_id provided, use personalized AI matching
    if request.startup_id:
        startup = db.query(StartupProfile).filter(StartupProfile.id == request.startup_id).first()
        if not startup:
            raise HTTPException(status_code=404, detail="Startup profile not found")

        results = await matching_engine.find_matches(
            startup, grants, use_ai_scoring=True, top_k=request.limit
        )
    else:
        # Keyword-based search without personalization
        results = []
        for grant in grants[: request.limit]:
            results.append(
                GrantMatchResult(
                    grant=GrantRead.model_validate(grant),
                    match_score=50.0,
                    match_explanation="General listing – provide a startup profile for personalized scoring.",
                    strong_matches=[],
                    missing_criteria=[],
                )
            )

    elapsed = (time.time() - start_time) * 1000
    return GrantSearchResponse(total=len(results), results=results, query_time_ms=round(elapsed, 2))


@router.get("/match/{startup_id}", response_model=GrantSearchResponse)
async def match_grants_for_startup(
    startup_id: str,
    top_k: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Get AI-matched grants for a specific startup (ranked by match score).
    Uses IBM Granite for intelligent matching.
    """
    start_time = time.time()
    startup = db.query(StartupProfile).filter(StartupProfile.id == startup_id).first()
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")

    grants = grant_service.get_grants(db, status=GrantStatus.OPEN, limit=200)
    results = await matching_engine.find_matches(startup, grants, use_ai_scoring=True, top_k=top_k)

    elapsed = (time.time() - start_time) * 1000
    return GrantSearchResponse(total=len(results), results=results, query_time_ms=round(elapsed, 2))
