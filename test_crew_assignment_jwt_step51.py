"""Intégration JWT réel + API + SQLite isolée (opt-in passlib/jwt).

Le routeur reste volontairement NON monté dans app.main.
Aucune base réelle n'est utilisée.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
pytest.importorskip("passlib")
pytest.importorskip("jwt")
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.models import User, Role, Country, Line, Trip, Vehicle
from app.security import token
from app.crew_assignment_step48 import CrewAssignmentStep48
from app.crew_assignment_admin_step49 import CrewAssignmentAuditStep49
from app.crew_assignment_api_step50 import router


@pytest.fixture
def env():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as db:
        cg = Country(code="CG", name="Congo", currency="XAF")
        ga = Country(code="GA", name="Gabon", currency="XAF")
        db.add_all([cg, ga]); db.flush()
        line_cg = Line(country_id=cg.id, code="TEST51CG", name="Test CG", fare=1000)
        line_ga = Line(country_id=ga.id, code="TEST51GA", name="Test GA", fare=1000)
        db.add_all([line_cg, line_ga]); db.flush()
        vehicle_cg = Vehicle(country_id=cg.id, code="VEH51CG", plate="CG-51", capacity=40, status="ACTIVE")
        vehicle_ga = Vehicle(country_id=ga.id, code="VEH51GA", plate="GA-51", capacity=40, status="ACTIVE")
        db.add_all([vehicle_cg, vehicle_ga]); db.flush()
        def make_trip(line):
            vehicle = vehicle_cg if line.id == line_cg.id else vehicle_ga
            obj = Trip(line_id=line.id, vehicle_id=vehicle.id,
                       departure_at=datetime.now(timezone.utc) + timedelta(days=1),
                       status="SCHEDULED")
            db.add(obj); db.flush()
            return obj
        trip_cg = make_trip(line_cg)
        trip_ga = make_trip(line_ga)
        def make_user(name, role, country):
            obj = User(username=name, password_hash="not-a-real-hash",
                       role=role, country_id=country.id, is_active=True, token_version=0)
            db.add(obj); db.flush()
            return obj
        admin = make_user("admin51", Role.ADMIN, cg)
        manager_cg = make_user("manager51", Role.COUNTRY_MANAGER, cg)
        manager_ga = make_user("managerga51", Role.COUNTRY_MANAGER, ga)
        driver = make_user("driver51", Role.DRIVER, cg)
        controller = make_user("controller51", Role.CONTROLLER, cg)
        agent = make_user("agent51", Role.AGENT, cg)
        db.commit()
        ids = {key: obj.id for key, obj in locals().copy().items()
               if key in ("admin", "manager_cg", "manager_ga", "driver", "controller", "agent", "trip_cg", "trip_ga")}
    app = FastAPI()
    app.include_router(router)
    def isolated_db():
        with Session() as db:
            yield db
    app.dependency_overrides[get_db] = isolated_db
    client = TestClient(app)
    def headers(name):
        with Session() as db:
            u = db.get(User, ids[name])
            return {"Authorization": "Bearer " + token(u)}
    yield client, Session, ids, headers
    client.close()
    engine.dispose()


def payload(ids, target="driver", trip="trip_cg"):
    return {"target_user_id": ids[target], "trip_id": ids[trip],
            "starts_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()}


def test_jwt_valide_cree_et_audite(env):
    client, Session, ids, headers = env
    r = client.post("/api/step50/crew-assignments",
                    headers=headers("manager_cg"), json=payload(ids))
    assert r.status_code == 201, r.text
    assignment_id = r.json()["assignment_id"]
    with Session() as db:
        a = db.get(CrewAssignmentStep48, assignment_id)
        logs = db.scalars(select(CrewAssignmentAuditStep49).where(
            CrewAssignmentAuditStep49.assignment_id == assignment_id)).all()
        assert a.user_id == ids["driver"] and a.active
        assert len(logs) == 1 and logs[0].actor_id == ids["manager_cg"]


def test_jwt_retrait_et_audit(env):
    client, Session, ids, headers = env
    created = client.post("/api/step50/crew-assignments",
                          headers=headers("admin"), json=payload(ids, "controller"))
    assert created.status_code == 201, created.text
    aid = created.json()["assignment_id"]
    r = client.post("/api/step50/crew-assignments/retirer",
                    headers=headers("manager_cg"), json={"assignment_id": aid})
    assert r.status_code == 200
    with Session() as db:
        assert not db.get(CrewAssignmentStep48, aid).active
        logs = db.scalars(select(CrewAssignmentAuditStep49).where(
            CrewAssignmentAuditStep49.assignment_id == aid)).all()
        assert [l.action for l in logs] == ["ATTRIBUER", "RETIRER"]


@pytest.mark.parametrize("who", ["manager_ga", "driver", "controller", "agent"])
def test_jwt_refus_role_ou_pays(env, who):
    client, Session, ids, headers = env
    r = client.post("/api/step50/crew-assignments",
                    headers=headers(who), json=payload(ids))
    assert r.status_code == 403
    with Session() as db:
        assert db.query(CrewAssignmentStep48).count() == 0


def test_jwt_absent(env):
    client, _, ids, _ = env
    r = client.post("/api/step50/crew-assignments", json=payload(ids))
    assert r.status_code in (401, 403)


def test_jwt_signature_invalide(env):
    client, _, ids, _ = env
    r = client.post("/api/step50/crew-assignments",
                    headers={"Authorization": "Bearer invalid.jwt.signature"},
                    json=payload(ids))
    assert r.status_code == 401


def test_jwt_version_revoquee(env):
    client, Session, ids, headers = env
    old_headers = headers("manager_cg")
    with Session() as db:
        u = db.get(User, ids["manager_cg"])
        u.token_version += 1
        db.commit()
    r = client.post("/api/step50/crew-assignments",
                    headers=old_headers, json=payload(ids))
    assert r.status_code == 401


def test_jwt_compte_desactive(env):
    client, Session, ids, headers = env
    old_headers = headers("manager_cg")
    with Session() as db:
        u = db.get(User, ids["manager_cg"])
        u.is_active = False
        db.commit()
    r = client.post("/api/step50/crew-assignments",
                    headers=old_headers, json=payload(ids))
    assert r.status_code == 401


def test_actor_id_client_ignore(env):
    client, Session, ids, headers = env
    data = payload(ids)
    data["actor_id"] = ids["admin"]
    r = client.post("/api/step50/crew-assignments",
                    headers=headers("manager_cg"), json=data)
    assert r.status_code == 201, r.text
    with Session() as db:
        log = db.scalars(select(CrewAssignmentAuditStep49)).one()
        assert log.actor_id == ids["manager_cg"]


def test_route_non_activee_dans_application(env):
    text = (Path(__file__).parent / "app" / "main.py").read_text()
    assert "crew_assignment_api_step50" not in text
