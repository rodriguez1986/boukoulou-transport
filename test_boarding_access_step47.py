import pytest
from app.boarding_access_step47 import AffectationVerifiee, autoriser_embarquement


def decision(role="DRIVER", action="VALIDER_EMBARQUEMENT", **changes):
    p = dict(user_id=12, role=role, actif=True, pays_utilisateur="CG",
             voyage_id=91, pays_voyage="CG", action=action,
             affectation=AffectationVerifiee(12, 91, "CG", True, True))
    p.update(changes)
    return autoriser_embarquement(**p)

@pytest.mark.parametrize("role", ["DRIVER", "CONTROLLER"])
@pytest.mark.parametrize("action", ["VALIDER_EMBARQUEMENT", "CONTROLER_BILLET", "CONSULTER_PASSAGERS", "CONSULTER_VOYAGE"])
def test_autorise(role, action):
    r = decision(role, action)
    assert r["autorise"] and not r["embarquement_enregistre"] and not r["billet_valide"]

@pytest.mark.parametrize("role", ["AGENT", "COUNTRY_MANAGER", "ADMIN", "SUPER_ADMIN"])
def test_role_refuse(role):
    assert not decision(role)["autorise"]

@pytest.mark.parametrize("changes", [
    {"actif": False}, {"pays_voyage": "GA"}, {"voyage_id": 92},
    {"user_id": 13}, {"action": "MODIFIER_TARIF"},
    {"affectation": AffectationVerifiee(12, 91, "CG", True, False)},
    {"affectation": AffectationVerifiee(12, 91, "CG", False, True)},
    {"affectation": None},
])
def test_refus(changes):
    assert not decision(**changes)["autorise"]
