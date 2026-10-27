"""Tests HTTP des routes, avec identité injectée depuis le serveur.

Ces tests n'exercent pas le décodage JWT réel (passlib non installé).
"""
from datetime import datetime, timezone
from types import SimpleNamespace
import pytest
pytest.importorskip("passlib", reason="JWT security module requires passlib")
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.db import get_db
from app.security import user
from app.crew_assignment_api_step50 import router
from app.crew_assignment_admin_step49 import AffectationRefusee
import app.crew_assignment_api_step50 as api


@pytest.fixture
def client(monkeypatch):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[user] = lambda: SimpleNamespace(id=19)
    app.dependency_overrides[get_db] = lambda: object()
    return TestClient(app)


def test_creer_acteur_non_controlable_par_client(client, monkeypatch):
    appels = []
    def fake(db, **kw):
        appels.append(kw)
        return 44
    monkeypatch.setattr(api, "attribuer", fake)
    data = {"target_user_id": 20, "trip_id": 33,
            "starts_at": "2026-10-25T09:00:00+00:00", "actor_id": 9999}
    r = client.post("/api/step50/crew-assignments", json=data)
    assert r.status_code == 201
    assert r.json()["assignment_id"] == 44
    assert appels[0]["actor_id"] == 19
    assert "actor_id" not in r.json()


def test_retirer(client, monkeypatch):
    appels = []
    monkeypatch.setattr(api, "retirer", lambda db, **kw: appels.append(kw))
    r = client.post("/api/step50/crew-assignments/retirer",
                    json={"assignment_id": 12})
    assert r.status_code == 200 and r.json()["retire"]
    assert appels[0]["actor_id"] == 19


def test_consulter(client, monkeypatch):
    monkeypatch.setattr(api, "consulter", lambda db, **kw: ({"id": 1, "role": "DRIVER"},))
    r = client.get("/api/step50/crew-assignments/voyage/33")
    assert r.status_code == 200 and r.json()["affectations"][0]["id"] == 1


@pytest.mark.parametrize("path,method,payload", [
    ("/api/step50/crew-assignments", "post", {"trip_id": 4}),
    ("/api/step50/crew-assignments/retirer", "post", {"assignment_id": -2}),
    ("/api/step50/crew-assignments/voyage/0", "get", None),
])
def test_parametres_invalides(client, path, method, payload):
    r = getattr(client, method)(path, **({"json": payload} if payload is not None else {}))
    assert r.status_code == 422


@pytest.mark.parametrize("endpoint,method,payload", [
    ("/api/step50/crew-assignments", "post", {"target_user_id": 2,
      "trip_id": 3, "starts_at": "2026-10-25T09:00:00+00:00"}),
    ("/api/step50/crew-assignments/retirer", "post", {"assignment_id": 1}),
    ("/api/step50/crew-assignments/voyage/3", "get", None),
])
def test_erreurs_ne_divulguent_pas_contexte(client, monkeypatch, endpoint, method, payload):
    def refuser(*a, **kw):
        raise AffectationRefusee("CIBLE_SECRETE_123")
    monkeypatch.setattr(api, {"post": "attribuer" if endpoint.endswith("assignments") else "retirer",
                              "get": "consulter"}[method], refuser)
    r = getattr(client, method)(endpoint, **({"json": payload} if payload else {}))
    assert r.status_code == 403
    assert "CIBLE_SECRETE_123" not in r.text


def test_router_non_monte():
    from pathlib import Path
    main = (Path(__file__).parent / "app" / "main.py").read_text()
    assert "crew_assignment_api_step50" not in main
