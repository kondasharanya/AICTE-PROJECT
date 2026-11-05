"""
Grant data service – loads seed data into DB, manages grant CRUD.
"""
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.models import Grant, GrantStatus, StartupStage
from app.services.scraper_service import grant_scraper
from app.services.granite_service import granite_service

logger = logging.getLogger("grant_finder.grant_service")


class GrantService:

    async def seed_grants(self, db: Session) -> int:
        """Load seed grant data into the database (idempotent)."""
        existing_count = db.query(Grant).count()
        if existing_count > 0:
            logger.info(f"Database already has {existing_count} grants, skipping seed.")
            return existing_count

        raw_grants = await grant_scraper.get_all_grants()
        created = 0

        for raw in raw_grants:
            # Use Granite to extract structured eligibility if configured
            eligibility_structured = {}
            if raw.get("eligibility_raw"):
                try:
                    eligibility_structured = await granite_service.extract_eligibility(raw["eligibility_raw"])
                except Exception as e:
                    logger.warning(f"Eligibility extraction skipped: {e}")

            grant = Grant(
                title=raw["title"],
                provider=raw["provider"],
                description=raw.get("description", ""),
                eligibility_raw=raw.get("eligibility_raw", ""),
                eligibility_structured=eligibility_structured,
                funding_amount_min=raw.get("funding_amount_min"),
                funding_amount_max=raw.get("funding_amount_max"),
                funding_currency=raw.get("funding_currency", "INR"),
                deadline=raw.get("deadline"),
                application_url=raw.get("application_url"),
                source_url=raw.get("source_url"),
                status=GrantStatus.OPEN,
                domains=raw.get("domains", []),
                stages=raw.get("stages", []),
                locations=raw.get("locations", ["India"]),
                tags=raw.get("tags", []),
                requirements=raw.get("requirements", []),
                last_scraped_at=raw.get("last_scraped_at", datetime.utcnow()),
            )
            db.add(grant)
            created += 1

        db.commit()
        logger.info(f"Seeded {created} grants into database.")
        return created

    def get_grants(
        self,
        db: Session,
        domain: Optional[str] = None,
        stage: Optional[str] = None,
        location: Optional[str] = None,
        status: Optional[GrantStatus] = GrantStatus.OPEN,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Grant]:
        query = db.query(Grant)
        if status:
            query = query.filter(Grant.status == status)
        grants = query.offset(offset).limit(limit).all()

        # Apply soft filters (JSON fields)
        filtered = []
        for g in grants:
            if domain and g.domains and "All domains" not in g.domains:
                if not any(domain.lower() in d.lower() or d.lower() in domain.lower() for d in g.domains):
                    continue
            if stage and g.stages:
                if stage not in g.stages:
                    continue
            if location and g.locations:
                if not any(location.lower() in l.lower() or l.lower() in location.lower() for l in g.locations):
                    continue
            filtered.append(g)

        return filtered

    def get_grant_by_id(self, db: Session, grant_id: str) -> Optional[Grant]:
        return db.query(Grant).filter(Grant.id == grant_id).first()


grant_service = GrantService()
