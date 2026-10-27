import pytest

from app.payment_routing_step38 import (
    DemandePaiement, moyens_disponibles, verifier_demande_paiement,
    preparer_intention_paiement, CONGO, GABON, AGENCE, BUS, EN_LIGNE,
    ESPECES, AIRTEL_MONEY, MTN_MOMO, MOOV_MONEY
)


@pytest.mark.parametrize("pays,canal,moyens", [
    (CONGO, AGENCE, (ESPECES,)),
    (CONGO, BUS, (ESPECES,)),
    (CONGO, EN_LIGNE, (AIRTEL_MONEY, MTN_MOMO)),
    (GABON, AGENCE, (ESPECES,)),
    (GABON, BUS, (ESPECES,)),
    (GABON, EN_LIGNE, (AIRTEL_MONEY, MOOV_MONEY)),
])
def test_catalogue(pays, canal, moyens):
    assert moyens_disponibles(pays, canal) == moyens


@pytest.mark.parametrize("pays,canal,moyen", [
    (CONGO, AGENCE, ESPECES),
    (CONGO, BUS, ESPECES),
    (GABON, AGENCE, ESPECES),
    (GABON, BUS, ESPECES),
    (CONGO, EN_LIGNE, AIRTEL_MONEY),
    (CONGO, EN_LIGNE, MTN_MOMO),
    (GABON, EN_LIGNE, AIRTEL_MONEY),
    (GABON, EN_LIGNE, MOOV_MONEY),
])
def test_combinations_valides(pays, canal, moyen):
    result = preparer_intention_paiement(DemandePaiement(pays, canal, moyen, "2500"))
    assert result["intention_preparee"]
    assert result["intention"]["montant_xaf"] == 2500
    assert result["intention"]["statut"] == "NON_EXECUTEE"
    assert not result["validation"]["transaction_executee"]


@pytest.mark.parametrize("pays,canal,moyen", [
    (CONGO, EN_LIGNE, MOOV_MONEY),
    (GABON, EN_LIGNE, MTN_MOMO),
    (CONGO, EN_LIGNE, ESPECES),
    (GABON, EN_LIGNE, ESPECES),
    (CONGO, AGENCE, AIRTEL_MONEY),
    (GABON, BUS, MOOV_MONEY),
    (CONGO, BUS, MTN_MOMO),
    (GABON, AGENCE, MTN_MOMO),
])
def test_combinations_interdites(pays, canal, moyen):
    r = verifier_demande_paiement(DemandePaiement(pays, canal, moyen, 2500))
    assert not r["autorise_par_regles_metier"]
    assert "MOYEN_INTERDIT_POUR_PAYS_ET_CANAL" in r["motifs"]


@pytest.mark.parametrize("montant", [0, -5, "12.5", "NaN", "Infinity", True, 1.5, "", None])
def test_montants_invalides(montant):
    r = verifier_demande_paiement(DemandePaiement(CONGO, AGENCE, ESPECES, montant))
    assert "MONTANT_INVALIDE" in r["motifs"]


def test_montant_entier_strict():
    assert verifier_demande_paiement(
        DemandePaiement(GABON, BUS, ESPECES, "1000")
    )["autorise_par_regles_metier"]


def test_devise():
    assert "DEVISE_NON_AUTORISEE" in verifier_demande_paiement(
        DemandePaiement(GABON, BUS, ESPECES, 1000, "EUR")
    )["motifs"]


def test_pays():
    assert "PAYS_NON_PRIS_EN_CHARGE" in verifier_demande_paiement(
        DemandePaiement("FR", BUS, ESPECES, 1000)
    )["motifs"]


def test_canal():
    assert "CANAL_NON_PRIS_EN_CHARGE" in verifier_demande_paiement(
        DemandePaiement(CONGO, "TELEPHONE", ESPECES, 1000)
    )["motifs"]


def test_moyen_inconnu():
    assert "MOYEN_INCONNU" in verifier_demande_paiement(
        DemandePaiement(CONGO, BUS, "CARTE", 1000)
    )["motifs"]


def test_demande_invalide():
    assert "DEMANDE_INVALIDE" in verifier_demande_paiement(None)["motifs"]


def test_agence_validation_caissier():
    r = preparer_intention_paiement(DemandePaiement(CONGO, AGENCE, ESPECES, 500))
    assert r["intention"]["necessite_validation_caissier"]
    assert not r["intention"]["necessite_confirmation_externe"]


def test_bus_validation_caissier():
    r = preparer_intention_paiement(DemandePaiement(GABON, BUS, ESPECES, 500))
    assert r["intention"]["necessite_validation_caissier"]


def test_en_ligne_confirmation_psp():
    r = preparer_intention_paiement(DemandePaiement(GABON, EN_LIGNE, MOOV_MONEY, 500))
    assert r["intention"]["necessite_confirmation_externe"]
    assert not r["intention"]["necessite_validation_caissier"]


def test_pas_d_intention_sur_refus():
    r = preparer_intention_paiement(DemandePaiement(GABON, EN_LIGNE, MTN_MOMO, 500))
    assert not r["intention_preparee"]
    assert r["intention"] is None


def test_inconnus_aucun_moyen():
    assert moyens_disponibles("FR", EN_LIGNE) == ()
