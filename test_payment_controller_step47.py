from enum import Enum
from types import SimpleNamespace
import pytest
pytest.importorskip("passlib", reason="Dépendance de sécurité non installée")
from fastapi import HTTPException
from app.payment_api_step45 import verifier_operation_authentifiee, OperationAExaminer
from app.models import Country

class Role(str, Enum):
    DRIVER="DRIVER"
    CONTROLLER="CONTROLLER"
    AGENT="AGENT"
    COUNTRY_MANAGER="COUNTRY_MANAGER"
    ADMIN="ADMIN"

class FakeDB:
    def get(self, cls, key):
        return SimpleNamespace(code="CG") if cls is Country and key == 1 else None

def check(role, action="CONFIRMER_ESPECES", canal="BUS", moyen="ESPECES"):
    u = SimpleNamespace(role=role, is_active=True, username="test", country_id=1)
    data = OperationAExaminer(pays="CG", canal=canal, moyen=moyen, action=action)
    return verifier_operation_authentifiee(u, FakeDB(), data)

@pytest.mark.parametrize("role", [Role.DRIVER, Role.CONTROLLER])
@pytest.mark.parametrize("action", ["CREER_INTENTION", "CONFIRMER_ESPECES", "ANNULER_INTENTION"])
def test_encaissement_bus(role, action):
    r = check(role, action)
    assert r["autorise"] and r["operation_executee"] is False

@pytest.mark.parametrize("role", [Role.DRIVER, Role.CONTROLLER])
def test_agence_interdite(role):
    with pytest.raises(HTTPException) as e:
        check(role, canal="AGENCE")
    assert e.value.status_code == 403

@pytest.mark.parametrize("role", [Role.AGENT, Role.COUNTRY_MANAGER, Role.ADMIN])
def test_autres_roles_refuses(role):
    with pytest.raises(HTTPException):
        check(role)

@pytest.mark.parametrize("role", [Role.DRIVER, Role.CONTROLLER])
def test_mobile_money_interdit_dans_bus(role):
    with pytest.raises(HTTPException):
        check(role, moyen="MTN_MOMO")
