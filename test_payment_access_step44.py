import pytest
from app.payment_access_step44 import (
    IdentiteHabilitee, OperationPaiement, verifier_autorisation,
    preparer_trace_decision, CAISSIER, AGENT_BUS, SUPERVISEUR,
    SERVICE_PSP, AUDITEUR, CREER_INTENTION, CONFIRMER_ESPECES,
    RECEVOIR_RESULTAT_PSP, CONSULTER_AUDIT, ANNULER_INTENTION,
)


def identite(role, pays="CG", canal="AGENCE", **kwargs):
    return IdentiteHabilitee("agent-1", role, frozenset({pays}),
                            frozenset({canal}), authentifiee=True, **kwargs)


def operation(pays="CG", canal="AGENCE", moyen="ESPECES", action=CREER_INTENTION):
    return OperationPaiement(pays, canal, moyen, action)


@pytest.mark.parametrize("role,canal,moyen,action", [
    (CAISSIER, "AGENCE", "ESPECES", CREER_INTENTION),
    (CAISSIER, "AGENCE", "ESPECES", CONFIRMER_ESPECES),
    (CAISSIER, "AGENCE", "ESPECES", ANNULER_INTENTION),
    (AGENT_BUS, "BUS", "ESPECES", CREER_INTENTION),
    (AGENT_BUS, "BUS", "ESPECES", CONFIRMER_ESPECES),
    (SUPERVISEUR, "AGENCE", "ESPECES", CONSULTER_AUDIT),
    (AUDITEUR, "BUS", "ESPECES", CONSULTER_AUDIT),
    (SERVICE_PSP, "EN_LIGNE", "MTN_MOMO", RECEVOIR_RESULTAT_PSP),
])
def test_permissions(role, canal, moyen, action):
    assert verifier_autorisation(
        identite(role, canal=canal), operation(canal=canal, moyen=moyen, action=action)
    )["autorise"]


@pytest.mark.parametrize("role,canal,moyen,action", [
    (CAISSIER, "AGENCE", "ESPECES", CONSULTER_AUDIT),
    (CAISSIER, "BUS", "ESPECES", CONFIRMER_ESPECES),
    (AGENT_BUS, "AGENCE", "ESPECES", CONFIRMER_ESPECES),
    (SUPERVISEUR, "AGENCE", "ESPECES", CONFIRMER_ESPECES),
    (AUDITEUR, "BUS", "ESPECES", ANNULER_INTENTION),
    (SERVICE_PSP, "EN_LIGNE", "MTN_MOMO", CONFIRMER_ESPECES),
    (SERVICE_PSP, "AGENCE", "ESPECES", RECEVOIR_RESULTAT_PSP),
])
def test_refus_role(role, canal, moyen, action):
    assert not verifier_autorisation(
        identite(role, canal=canal), operation(canal=canal, moyen=moyen, action=action)
    )["autorise"]


def test_pas_authentifie():
    i = IdentiteHabilitee("agent-1", CAISSIER, frozenset({"CG"}),
                         frozenset({"AGENCE"}))
    assert "IDENTITE_NON_AUTHENTIFIEE" in verifier_autorisation(
        i, operation())["motifs"]


def test_pays_non_autorise():
    assert "PAYS_HORS_PERIMETRE" in verifier_autorisation(
        identite(CAISSIER), operation("GA"))["motifs"]


def test_moyen_interdit():
    assert "MOYEN_NON_AUTORISE" in verifier_autorisation(
        identite(CAISSIER), operation(moyen="MTN_MOMO"))["motifs"]


def test_inactif():
    i = IdentiteHabilitee("agent-1", CAISSIER, frozenset({"CG"}),
                         frozenset({"AGENCE"}), active=False, authentifiee=True)
    assert "COMPTE_INACTIF" in verifier_autorisation(i, operation())["motifs"]


def test_identite_invalide():
    assert not verifier_autorisation(None, operation())["autorise"]


def test_role_inconnu():
    assert "ROLE_INCONNU" in verifier_autorisation(
        identite("ADMIN_TOUT_PUISSANT"), operation())["motifs"]


def test_gabon_moov():
    assert verifier_autorisation(
        identite(SERVICE_PSP, pays="GA", canal="EN_LIGNE"),
        operation("GA", "EN_LIGNE", "MOOV_MONEY", RECEVOIR_RESULTAT_PSP)
    )["autorise"]


def test_trace_non_persistante():
    trace = preparer_trace_decision(identite(CAISSIER), operation())
    assert trace["autorise"] and not trace["trace_persistee"]
    assert not trace["horodatage_fiable"]


def test_pas_execution():
    d = verifier_autorisation(identite(CAISSIER), operation())
    assert not d["action_executee"] and not d["paiement_reel_confirme"]
