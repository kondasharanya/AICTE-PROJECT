"""
Tests for the grant matching engine (no IBM API required).
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from app.models.models import StartupProfile, Grant, StartupStage, GrantStatus
from app.services.matching_engine import _rule_based_score, _domain_matches, _stage_matches


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_startup(**kwargs) -> StartupProfile:
    defaults = dict(
        id="startup-1",
        name="TestStartup",
        domain="EdTech",
        stage=StartupStage.MVP,
        location_country="India",
        location_state="Karnataka",
        dpiit_recognized=True,
        keywords=["AI", "education"],
    )
    defaults.update(kwargs)
    s = MagicMock(spec=StartupProfile)
    for k, v in defaults.items():
        setattr(s, k, v)
    return s


def make_grant(**kwargs) -> Grant:
    defaults = dict(
        id="grant-1",
        title="Test Grant",
        provider="AICTE",
        domains=["EdTech", "AI/ML"],
        stages=["mvp", "early_stage"],
        locations=["India"],
        tags=["AI", "education"],
        status=GrantStatus.OPEN,
        requirements=[],
        funding_amount_min=500000,
        funding_amount_max=2500000,
        funding_currency="INR",
    )
    defaults.update(kwargs)
    g = MagicMock(spec=Grant)
    for k, v in defaults.items():
        setattr(g, k, v)
    return g


# ── Domain matching tests ─────────────────────────────────────────────────────

def test_domain_matches_exact():
    assert _domain_matches("EdTech", ["EdTech", "HealthTech"]) is True

def test_domain_matches_all_domains():
    assert _domain_matches("SaaS", ["All domains"]) is True

def test_domain_matches_partial():
    assert _domain_matches("AI/ML", ["AI/ML", "IoT"]) is True

def test_domain_no_match():
    assert _domain_matches("FinTech", ["AgriTech", "CleanTech"]) is False

def test_stage_matches():
    assert _stage_matches("mvp", ["mvp", "early_stage"]) is True
    assert _stage_matches("scale", ["idea", "prototype"]) is False


# ── Rule-based scoring ────────────────────────────────────────────────────────

def test_rule_based_score_perfect_match():
    startup = make_startup()
    grant = make_grant()
    score, strong, missing = _rule_based_score(startup, grant)
    # Domain(30) + Stage(25) + Location(20) + DPIIT(10) + Keywords(10) = 95
    assert score >= 80
    assert len(strong) >= 3

def test_rule_based_score_no_domain_match():
    startup = make_startup(domain="FinTech")
    grant = make_grant(domains=["AgriTech"])
    score, strong, missing = _rule_based_score(startup, grant)
    # No domain match → lose 30 points
    assert score < 70
    assert any("domain" in m.lower() for m in missing)

def test_rule_based_score_no_dpiit():
    startup = make_startup(dpiit_recognized=False)
    grant = make_grant()
    score, strong, missing = _rule_based_score(startup, grant)
    # No DPIIT bonus
    assert score <= 85

def test_rule_based_score_location_mismatch():
    startup = make_startup(location_state="Maharashtra", location_country="India")
    grant = make_grant(locations=["Karnataka"])
    score, strong, missing = _rule_based_score(startup, grant)
    assert any("location" in m.lower() or "Karnataka" in m for m in missing)
