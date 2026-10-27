import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("refund_rules_step30", Path(__file__).parent / "app" / "refund_rules_step30.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def check(**kwargs):
    data = {"role": "ADMIN", "payment": {"id": 10, "status": "SUCCESS", "amount": 1000},
            "montant": 400, "cle_idempotence": "ref-001"}
    data.update(kwargs)
    return module.verifier_demande_remboursement(**data)

def test_valid_prevalidation_is_not_execution():
    r=check(); assert r["autorise_en_prevalidation"] and not r["execution_effectuee"] and r["aucune_ecriture"]

def test_role_denied():
    assert "ROLE_NON_AUTORISE" in check(role="AGENT")["motifs"]

def test_failed_payment_denied():
    assert "PAIEMENT_NON_VALIDE" in check(payment={"id": 10, "status": "FAILED", "amount": 1000})["motifs"]

def test_missing_key_denied():
    assert "CLE_IDEMPOTENCE_REQUISE" in check(cle_idempotence="")["motifs"]

def test_duplicate_request_denied():
    assert "DEMANDE_DEJA_ENREGISTREE" in check(remboursements_existants=[{"payment_id": 10, "idempotency_key": "ref-001", "status": "PENDING", "amount": 400}])["motifs"]

def test_cumulative_limit_denied():
    assert "PLAFOND_REMBOURSEMENT_DEPASSE" in check(montant=401, remboursements_existants=[{"payment_id": 10, "status": "CONFIRMED", "amount": 600}])["motifs"]

def test_exact_remaining_amount_allowed():
    assert check(montant=400, remboursements_existants=[{"payment_id": 10, "status": "CONFIRMED", "amount": 600}])["autorise_en_prevalidation"]

def test_invalid_amounts_denied():
    for v in (0, -1, "NaN", "Infinity", "1.5", True):
        assert "MONTANT_REMBOURSEMENT_INVALIDE" in check(montant=v)["motifs"]

def test_invalid_history_denied():
    assert "HISTORIQUE_REMBOURSEMENTS_INVALIDE" in check(remboursements_existants=[{"payment_id": 10, "status": "CONFIRMED", "amount": -10}])["motifs"]

def test_does_not_mutate_inputs():
    payment={"id": 10, "status": "SUCCESS", "amount": 1000}
    existing=[{"payment_id": 10, "status": "CONFIRMED", "amount": 100}]
    check(payment=payment, remboursements_existants=existing)
    assert payment["amount"] == 1000 and existing[0]["amount"] == 100
