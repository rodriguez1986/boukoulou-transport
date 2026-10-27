"""Tests sans import de main.py, sans DB ou JWT réels."""
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
import importlib.util
import sys
import pytest
from fastapi import HTTPException

# Importer la véritable dépendance JWT FastAPI. Si passlib est absent,
# le shim minimal reste exclusivement dans l'environnement de tests.
# Ne jamais remplacer app.security dans sys.modules : les dépendances
# FastAPI conserveraient alors une référence au faux utilisateur.
if importlib.util.find_spec("passlib") is None:
    sys.path.insert(0, str(Path(__file__).parent / "test_support_step53"))

from app.payment_api_step45 import (
    OperationAExaminer, construire_identite_depuis_utilisateur,
    verifier_operation_authentifiee, router,
)


class Role(str, Enum):
    AGENT = "AGENT"
    DRIVER = "DRIVER"
    COUNTRY_MANAGER = "COUNTRY_MANAGER"
    CONTROLLER = "CONTROLLER"
    ADMIN = "ADMIN"


def compte(role=Role.AGENT, country_id=1, active=True):
    return SimpleNamespace(role=role, country_id=country_id,
                           username="agent-fiable", is_active=active)


class DB:
    def __init__(self, code="CG"):
        self.code = code
    def get(self, cls, key):
        return SimpleNamespace(code=self.code) if key == 1 else None


def operation(pays="CG", canal="AGENCE", moyen="ESPECES", action="CONFIRMER_ESPECES"):
    return OperationAExaminer(pays=pays, canal=canal, moyen=moyen, action=action)


def test_agence_ok_sans_encaissement():
    r = verifier_operation_authentifiee(compte(), DB(), operation())
    assert r["autorise"] and not r["operation_executee"] and not r["paiement_reel_confirme"]


def test_bus_driver_ok():
    r = verifier_operation_authentifiee(
        compte(Role.DRIVER), DB(), operation(canal="BUS"))
    assert r["autorise"]


def test_pays_etranger_refuse():
    with pytest.raises(HTTPException) as err:
        verifier_operation_authentifiee(compte(), DB(), operation(pays="GA"))
    assert err.value.status_code == 403


def test_role_admin_pas_implicite():
    with pytest.raises(HTTPException):
        verifier_operation_authentifiee(compte(Role.ADMIN), DB(), operation())


def test_role_controleur_ne_confirme_pas():
    with pytest.raises(HTTPException):
        verifier_operation_authentifiee(compte(Role.CONTROLLER), DB(), operation())


def test_compte_inactif_refuse():
    with pytest.raises(HTTPException):
        verifier_operation_authentifiee(compte(active=False), DB(), operation())


def test_pays_absent_refuse():
    with pytest.raises(HTTPException):
        verifier_operation_authentifiee(compte(country_id=None), DB(), operation())


def test_moyen_mtn_en_agence_refuse():
    with pytest.raises(HTTPException):
        verifier_operation_authentifiee(compte(), DB(), operation(moyen="MTN_MOMO"))


def test_pays_gabon_autorise():
    r = verifier_operation_authentifiee(compte(), DB("GA"), operation(pays="GA"))
    assert r["autorise"]


def test_route_non_montee_automatiquement():
    from pathlib import Path
    main = (Path(__file__).parent / "app" / "main.py").read_text(encoding="utf-8")
    assert "payment_api_step45" not in main
    assert any(route.path.endswith("/verifier") for route in router.routes)


def test_identity_sans_username_refuse():
    u = compte()
    u.username = ""
    with pytest.raises(HTTPException):
        construire_identite_depuis_utilisateur(u, "CG", "CG")
