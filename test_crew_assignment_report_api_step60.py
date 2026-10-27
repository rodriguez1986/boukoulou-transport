"""Tests du périmètre pays et contrat API, sans monter le routeur en production."""
from pathlib import Path
import pytest
from sqlalchemy import select
from test_crew_assignment_admin_step49 import db, assign
from app.models import Country, Line, Trip
from app.crew_assignment_report_step59 import rapport_anomalies_affectations


def test_country_scope_same_country(db):
    aid = assign(db)
    trip = db.get(Trip, db.scalars(select(Trip.id)).first())
    line = db.get(Line, trip.line_id)
    result = rapport_anomalies_affectations(db, country_id=line.country_id)
    assert result["scanned"] == 1 and result["next_after_id"] == aid


def test_country_scope_other_country(db):
    assign(db)
    result = rapport_anomalies_affectations(db, country_id=99999)
    assert result["scanned"] == 0 and result["anomalies"] == []

@pytest.mark.parametrize("country_id", [0, -1, True, "1", 1.5])
def test_country_scope_rejects_bad_id(db, country_id):
    with pytest.raises(ValueError, match="PAYS_INVALIDE"):
        rapport_anomalies_affectations(db, country_id=country_id)


def test_router_not_mounted():
    source = (Path(__file__).parent / "app" / "main.py").read_text()
    assert "crew_assignment_report_api_step60" not in source


def test_report_api_requires_jwt_and_role():
    source = (Path(__file__).parent / "app" / "crew_assignment_report_api_step60.py").read_text()
    assert "Depends(user)" in source
    assert "Role.COUNTRY_MANAGER" in source and "Role.ADMIN" in source
    assert "country_id=country_id" in source
