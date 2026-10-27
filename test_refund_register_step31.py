import ast
from pathlib import Path
from app.refund_register_step31 import examiner_reservation

PAYMENT = {"id": 10, "status": "SUCCESS", "amount": 1000}

def check(registre=(), montant=400, cle="refund-1", role="ADMIN"):
    return examiner_reservation(role=role, payment=PAYMENT, montant=montant,
        cle_idempotence=cle, registre=registre)

def test_valid_is_only_simulation():
    r = check()
    assert r["reservation_possible_en_simulation"]
    assert not r["reservation_effectuee"] and not r["remboursement_execute"]

def test_pending_reserves_limit():
    r = check(registre=[{"payment_id":10,"status":"PENDING","amount":700}], montant=400)
    assert "PLAFOND_AVEC_RESERVATIONS_DEPASSE" in r["motifs"]

def test_processing_reserves_limit():
    r = check(registre=[{"payment_id":10,"status":"PROCESSING","amount":700}], montant=400)
    assert "PLAFOND_AVEC_RESERVATIONS_DEPASSE" in r["motifs"]

def test_confirmed_consumes_limit():
    r = check(registre=[{"payment_id":10,"status":"CONFIRMED","amount":700}], montant=400)
    assert not r["reservation_possible_en_simulation"]

def test_failed_does_not_reserve():
    assert check(registre=[{"payment_id":10,"status":"FAILED","amount":700}])["reservation_possible_en_simulation"]

def test_other_payment_does_not_reserve():
    assert check(registre=[{"payment_id":11,"status":"PENDING","amount":700}])["reservation_possible_en_simulation"]

def test_duplicate_key_rejected():
    r = check(registre=[{"payment_id":10,"status":"PENDING","amount":100,"idempotency_key":"refund-1"}])
    assert "DEMANDE_DEJA_ENREGISTREE" in r["motifs"]

def test_exact_remaining_allowed():
    assert check(registre=[{"payment_id":10,"status":"PENDING","amount":600}])["reservation_possible_en_simulation"]

def test_invalid_reserved_history_rejected():
    r = check(registre=[{"payment_id":10,"status":"PENDING","amount":-3}])
    assert "HISTORIQUE_RESERVATIONS_INVALIDE" in r["motifs"]

def test_role_restriction_preserved():
    assert "ROLE_NON_AUTORISE" in check(role="AGENT")["motifs"]

def test_sql_is_draft_and_has_unique_key():
    sql = (Path(__file__).parent/'migrations/v59_refund_register_step31_DRAFT_NOT_APPLIED.sql').read_text()
    assert 'UNIQUE (payment_id, idempotency_key)' in sql
    assert 'FOR UPDATE' in sql
    assert 'NE PAS EXECUTER EN PRODUCTION' in sql
