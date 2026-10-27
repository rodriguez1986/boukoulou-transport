"""Tests d'intégration FastAPI/JWT en mémoire, sans PostgreSQL réel.

L'absence de passlib (dépendance historique de security.py) entraîne un skip
explicite : ne jamais prétendre avoir testé le JWT dans ce cas.
"""
import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
pytest.importorskip("passlib", reason="Dépendance historique requise pour security.py")
import jwt
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.db import get_db
from app.models import User, Country
from app.payment_api_step45 import router
from app import security


TEST_PAYMENT_JWT_SECRET = "step64-payment-jwt-test-only-key-32-bytes-minimum"
TEST_PAYMENT_INVALID_SECRET = "step64-invalid-signature-test-key-32-bytes-minimum"


class FakeDB:
    def __init__(self, role="AGENT", country_code="CG", active=True, token_version=3):
        self.u = SimpleNamespace(
            id=17, username="caissier-test", role=SimpleNamespace(value=role),
            country_id=7, is_active=active, token_version=token_version)
        self.country = SimpleNamespace(code=country_code)

    def get(self, model, identifier):
        if model is User and identifier == 17:
            return self.u
        if model is Country and identifier == 7:
            return self.country
        return None


@pytest.fixture
def client_factory(monkeypatch):
    monkeypatch.setattr(security, "SECRET", TEST_PAYMENT_JWT_SECRET)
    def factory(db=None):
        db = db or FakeDB()
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_db] = lambda: db
        return TestClient(app), db
    return factory


def jwt_header(*, sub="17", tv=3, exp=None, secret=None):
    if exp is None:
        exp = datetime.now(timezone.utc) + timedelta(minutes=10)
    token = jwt.encode({"sub": sub, "tv": tv, "exp": exp},
                       TEST_PAYMENT_JWT_SECRET if secret is None else secret, algorithm="HS256")
    return {"Authorization": "Bearer " + token}


PAYLOAD = {"pays": "CG", "canal": "AGENCE", "moyen": "ESPECES",
           "action": "CONFIRMER_ESPECES"}
URL = "/api/step45/payment-access/verifier"


def test_valide(client_factory):
    client, _ = client_factory()
    r = client.post(URL, json=PAYLOAD, headers=jwt_header())
    assert r.status_code == 200, r.text
    assert r.json()["autorise"] is True
    assert r.json()["operation_executee"] is False


def test_sans_token(client_factory):
    client, _ = client_factory()
    assert client.post(URL, json=PAYLOAD).status_code in (401, 403)


def test_signature_invalide(client_factory):
    client, _ = client_factory()
    assert client.post(URL, json=PAYLOAD, headers=jwt_header(secret=TEST_PAYMENT_INVALID_SECRET)).status_code == 401


def test_token_expire(client_factory):
    client, _ = client_factory()
    h = jwt_header(exp=datetime.now(timezone.utc) - timedelta(seconds=2))
    assert client.post(URL, json=PAYLOAD, headers=h).status_code == 401


def test_version_revoquee(client_factory):
    client, _ = client_factory()
    assert client.post(URL, json=PAYLOAD, headers=jwt_header(tv=2)).status_code == 401


def test_compte_inactif(client_factory):
    client, _ = client_factory(FakeDB(active=False))
    assert client.post(URL, json=PAYLOAD, headers=jwt_header()).status_code == 401


def test_role_interdit(client_factory):
    client, _ = client_factory(FakeDB(role="ADMIN"))
    assert client.post(URL, json=PAYLOAD, headers=jwt_header()).status_code == 403


def test_pays_interdit(client_factory):
    client, _ = client_factory(FakeDB(country_code="GA"))
    assert client.post(URL, json=PAYLOAD, headers=jwt_header()).status_code == 403


def test_moyen_interdit(client_factory):
    client, _ = client_factory()
    payload = dict(PAYLOAD, moyen="MTN_MOMO")
    assert client.post(URL, json=payload, headers=jwt_header()).status_code == 403


def test_champ_manquant(client_factory):
    client, _ = client_factory()
    payload = dict(PAYLOAD)
    payload.pop("moyen")
    assert client.post(URL, json=payload, headers=jwt_header()).status_code == 422


def test_sub_invalide(client_factory):
    client, _ = client_factory()
    assert client.post(URL, json=PAYLOAD, headers=jwt_header(sub="abc")).status_code == 401


def test_pas_de_route_paiement_reel(client_factory):
    client, _ = client_factory()
    assert client.post(URL, json=PAYLOAD, headers=jwt_header()).json()["paiement_reel_confirme"] is False
