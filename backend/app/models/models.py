"""
ORM models for the grant finder application.
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, DateTime, Float, Boolean,
    JSON, ForeignKey, Integer, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class StartupStage(str, enum.Enum):
    IDEA = "idea"
    PROTOTYPE = "prototype"
    MVP = "mvp"
    EARLY_STAGE = "early_stage"
    GROWTH = "growth"
    SCALE = "scale"


class GrantStatus(str, enum.Enum):
    OPEN = "open"
    CLOSING_SOON = "closing_soon"
    CLOSED = "closed"
    UPCOMING = "upcoming"


class StartupProfile(Base):
    __tablename__ = "startup_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    domain = Column(String(100), nullable=False)          # e.g. "EdTech", "HealthTech"
    stage = Column(SAEnum(StartupStage), nullable=False)
    location_country = Column(String(100), default="India")
    location_state = Column(String(100), nullable=True)
    founding_year = Column(Integer, nullable=True)
    team_size = Column(Integer, nullable=True)
    annual_revenue = Column(Float, nullable=True)          # INR
    description = Column(Text, nullable=True)
    keywords = Column(JSON, default=list)                  # ["AI", "healthcare", ...]
    dpiit_recognized = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    applications = relationship("GrantApplication", back_populates="startup")


class Grant(Base):
    __tablename__ = "grants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    provider = Column(String(255), nullable=False)          # "AICTE", "DST", "Startup India"
    description = Column(Text, nullable=True)
    eligibility_raw = Column(Text, nullable=True)          # raw NLP-extracted text
    eligibility_structured = Column(JSON, default=dict)    # structured eligibility criteria
    funding_amount_min = Column(Float, nullable=True)
    funding_amount_max = Column(Float, nullable=True)
    funding_currency = Column(String(10), default="INR")
    deadline = Column(DateTime, nullable=True)
    application_url = Column(String(1000), nullable=True)
    source_url = Column(String(1000), nullable=True)
    status = Column(SAEnum(GrantStatus), default=GrantStatus.OPEN)
    domains = Column(JSON, default=list)                   # applicable domains
    stages = Column(JSON, default=list)                    # applicable startup stages
    locations = Column(JSON, default=list)                 # applicable states/countries
    tags = Column(JSON, default=list)
    requirements = Column(JSON, default=list)              # checklist items
    last_scraped_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    applications = relationship("GrantApplication", back_populates="grant")


class GrantApplication(Base):
    __tablename__ = "grant_applications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    startup_id = Column(String, ForeignKey("startup_profiles.id"), nullable=False)
    grant_id = Column(String, ForeignKey("grants.id"), nullable=False)
    match_score = Column(Float, default=0.0)               # 0–100
    match_explanation = Column(Text, nullable=True)
    proposal_draft = Column(Text, nullable=True)           # Granite-generated draft
    status = Column(String(50), default="draft")           # draft / submitted / accepted / rejected
    submitted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    startup = relationship("StartupProfile", back_populates="applications")
    grant = relationship("Grant", back_populates="applications")
