"""
API routes – Proposal generation via IBM Granite.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import StartupProfile, GrantApplication
from app.schemas.schemas import ProposalRequest, ProposalResponse
from app.services.grant_service import grant_service
from app.services.matching_engine import matching_engine

router = APIRouter(prefix="/proposals", tags=["Proposal Generation"])


@router.post("/generate", response_model=ProposalResponse)
async def generate_proposal(request: ProposalRequest, db: Session = Depends(get_db)):
    """
    Generate a tailored grant proposal draft using IBM Granite.
    The proposal is stored as a GrantApplication record (status=draft).
    """
    startup = db.query(StartupProfile).filter(StartupProfile.id == request.startup_id).first()
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")

    grant = grant_service.get_grant_by_id(db, request.grant_id)
    if not grant:
        raise HTTPException(status_code=404, detail="Grant not found")

    application = await matching_engine.generate_proposal(
        startup, grant, db, additional_context=request.additional_context or ""
    )

    return ProposalResponse(
        application_id=application.id,
        startup_name=startup.name,
        grant_title=grant.title,
        match_score=application.match_score,
        proposal_draft=application.proposal_draft,
        generated_at=datetime.utcnow(),
    )


@router.get("/{application_id}", response_model=ProposalResponse)
def get_proposal(application_id: str, db: Session = Depends(get_db)):
    """Retrieve a saved proposal draft."""
    app = (
        db.query(GrantApplication)
        .filter(GrantApplication.id == application_id)
        .first()
    )
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    return ProposalResponse(
        application_id=app.id,
        startup_name=app.startup.name,
        grant_title=app.grant.title,
        match_score=app.match_score,
        proposal_draft=app.proposal_draft or "",
        generated_at=app.created_at,
    )


@router.get("/startup/{startup_id}")
def list_startup_proposals(startup_id: str, db: Session = Depends(get_db)):
    """List all proposals for a startup."""
    apps = (
        db.query(GrantApplication)
        .filter(GrantApplication.startup_id == startup_id)
        .all()
    )
    return [
        {
            "application_id": a.id,
            "grant_title": a.grant.title,
            "provider": a.grant.provider,
            "match_score": a.match_score,
            "status": a.status,
            "created_at": a.created_at.isoformat(),
        }
        for a in apps
    ]
