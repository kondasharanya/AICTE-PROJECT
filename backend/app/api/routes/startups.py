"""
API routes – Startup profiles.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.models import StartupProfile
from app.schemas.schemas import StartupProfileCreate, StartupProfileRead

router = APIRouter(prefix="/startups", tags=["Startup Profiles"])


@router.post("/", response_model=StartupProfileRead, status_code=status.HTTP_201_CREATED)
def create_startup(payload: StartupProfileCreate, db: Session = Depends(get_db)):
    """Register a new startup profile."""
    startup = StartupProfile(**payload.model_dump())
    db.add(startup)
    db.commit()
    db.refresh(startup)
    return startup


@router.get("/", response_model=List[StartupProfileRead])
def list_startups(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(StartupProfile).offset(skip).limit(limit).all()


@router.get("/{startup_id}", response_model=StartupProfileRead)
def get_startup(startup_id: str, db: Session = Depends(get_db)):
    startup = db.query(StartupProfile).filter(StartupProfile.id == startup_id).first()
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    return startup


@router.put("/{startup_id}", response_model=StartupProfileRead)
def update_startup(startup_id: str, payload: StartupProfileCreate, db: Session = Depends(get_db)):
    startup = db.query(StartupProfile).filter(StartupProfile.id == startup_id).first()
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    for field, value in payload.model_dump().items():
        setattr(startup, field, value)
    db.commit()
    db.refresh(startup)
    return startup


@router.delete("/{startup_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_startup(startup_id: str, db: Session = Depends(get_db)):
    startup = db.query(StartupProfile).filter(StartupProfile.id == startup_id).first()
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    db.delete(startup)
    db.commit()
