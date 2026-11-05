"""
Pydantic schemas for request/response validation.
"""
from __future__ import annotations
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, Field
from app.models.models import StartupStage, GrantStatus


# ── Startup Profile ────────────────────────────────────────────────────────────

class StartupProfileCreate(BaseModel):
    name: str
    domain: str
    stage: StartupStage
    location_country: str = "India"
    location_state: Optional[str] = None
    founding_year: Optional[int] = None
    team_size: Optional[int] = None
    annual_revenue: Optional[float] = None
    description: Optional[str] = None
    keywords: List[str] = []
    dpiit_recognized: bool = False


class StartupProfileRead(StartupProfileCreate):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Grant ──────────────────────────────────────────────────────────────────────

class GrantRead(BaseModel):
    id: str
    title: str
    provider: str
    description: Optional[str]
    eligibility_structured: Dict[str, Any] = {}
    funding_amount_min: Optional[float]
    funding_amount_max: Optional[float]
    funding_currency: str
    deadline: Optional[datetime]
    application_url: Optional[str]
    source_url: Optional[str]
    status: GrantStatus
    domains: List[str] = []
    stages: List[str] = []
    locations: List[str] = []
    tags: List[str] = []
    requirements: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True


class GrantMatchResult(BaseModel):
    grant: GrantRead
    match_score: float = Field(..., ge=0, le=100)
    match_explanation: str
    missing_criteria: List[str] = []
    strong_matches: List[str] = []


# ── Grant Application / Proposal ──────────────────────────────────────────────

class ProposalRequest(BaseModel):
    startup_id: str
    grant_id: str
    additional_context: Optional[str] = None


class ProposalResponse(BaseModel):
    application_id: str
    startup_name: str
    grant_title: str
    match_score: float
    proposal_draft: str
    generated_at: datetime


# ── Search ────────────────────────────────────────────────────────────────────

class GrantSearchRequest(BaseModel):
    startup_id: Optional[str] = None
    query: Optional[str] = None
    domain: Optional[str] = None
    stage: Optional[StartupStage] = None
    location: Optional[str] = None
    min_funding: Optional[float] = None
    max_funding: Optional[float] = None
    status: Optional[GrantStatus] = GrantStatus.OPEN
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class GrantSearchResponse(BaseModel):
    total: int
    results: List[GrantMatchResult]
    query_time_ms: float
