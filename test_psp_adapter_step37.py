from app.psp_adapter_step37 import (
    ConfigurationPSP, evaluer_activation_psp, decrire_plan_transactionnel
)


def test_configuration_non_valide():
    r = evaluer_activation_psp(None)
    assert not r["activation_autorisee"]
    assert "CONFIGURATION_INVALIDE" in r["motifs"]


def test_prestataire_absent():
    r = evaluer_activation_psp(ConfigurationPSP("", "sandbox", False, False, False))
    assert "FOURNISSEUR_NON_CHOISI" in r["motifs"]


def test_environnement_invalide():
    r = evaluer_activation_psp(ConfigurationPSP("PSP", "demo", False, False, False))
    assert "ENVIRONNEMENT_INVALIDE" in r["motifs"]


def test_signature_non_implementee():
    r = evaluer_activation_psp(ConfigurationPSP("PSP", "sandbox", False, False, False))
    assert "VERIFICATION_SIGNATURE_REELLE_MANQUANTE" in r["motifs"]


def test_secret_absent():
    r = evaluer_activation_psp(ConfigurationPSP("PSP", "sandbox", True, False, False))
    assert "SECRET_PSP_MANQUANT" in r["motifs"]


def test_deduplication_non_active():
    r = evaluer_activation_psp(ConfigurationPSP("PSP", "sandbox", True, False, True))
    assert "DEDUPLICATION_ATOMIQUE_MANQUANTE" in r["motifs"]


def test_endpoint_premature():
    r = evaluer_activation_psp(ConfigurationPSP("PSP", "sandbox", True, True, True, True))
    assert "ENDPOINT_ACTIF_PREMATUREMENT" in r["motifs"]


def test_configuration_complete_ne_suffit_pas():
    r = evaluer_activation_psp(ConfigurationPSP("PSP", "production", True, True, True))
    assert not r["activation_autorisee"]
    assert "INTEGRATION_REELLE_NON_IMPLEMENTEE" in r["motifs"]
    assert not r["webhook_actif"]
    assert not r["remboursement_actif"]


def test_plan_transactionnel():
    p = decrire_plan_transactionnel()
    assert len(p) == 9
    assert any("UNIQUE" in s for s in p)
    assert any("FOR UPDATE" in s for s in p)
    assert any("audit" in s for s in p)


def test_config_immutable():
    c = ConfigurationPSP("PSP", "sandbox", True, True, True)
    try:
        c.fournisseur = "AUTRE"
    except (AttributeError, TypeError):
        pass
    else:
        raise AssertionError("La configuration doit être immuable")
