import json

from app.psp_signature_step35 import signer_notification_test
from app.psp_reception_step36 import simuler_reception_notification

SECRET = b"secret-de-test"
TS = 1700000000
EVENT = {"provider": "DEMO", "event_id": "evt-1", "refund_id": "ref-1",
         "status": "CONFIRMED", "amount": 1000, "currency": "XAF"}


def evaluate(event=EVENT, *, body=None, signature=None, history=(), known=("ref-1",),
             secret=SECRET, ts=TS, now=TS):
    if body is None:
        body = json.dumps(event, separators=(",", ":")).encode("utf-8")
    if signature is None:
        signature = signer_notification_test(
            corps_brut=body, secret=SECRET, horodatage=TS
        )
    return simuler_reception_notification(
        corps_brut=body, signature=signature, horodatage=ts,
        secret=secret, historique=history,
        remboursements_connus=known, maintenant=now
    )


def test_valid_demo_notification():
    result = evaluate()
    assert result["acceptable_en_simulation"]
    assert result["controle_registre_effectue"]
    assert not result["protocole_psp_reel_verifie"]
    assert not result["evenement_enregistre"]
    assert not result["remboursement_execute"]


def test_invalid_signature_short_circuits():
    result = evaluate(signature="0"*64)
    assert "SIGNATURE_INVALIDE" in result["motifs"]
    assert not result["controle_registre_effectue"]


def test_body_tampering():
    body = json.dumps({**EVENT, "amount": 2000}).encode()
    original = json.dumps(EVENT, separators=(",", ":")).encode()
    signature = signer_notification_test(corps_brut=original, secret=SECRET, horodatage=TS)
    assert "SIGNATURE_INVALIDE" in evaluate(body=body, signature=signature)["motifs"]


def test_duplicate_event():
    assert "EVENEMENT_DEJA_VU" in evaluate(history=[EVENT])["motifs"]


def test_conflicting_event():
    assert "EVENEMENT_CONFLICTUEL" in evaluate(
        history=[{**EVENT, "amount": 900}])["motifs"]


def test_unknown_refund():
    assert "REMBOURSEMENT_INCONNU" in evaluate(known=())["motifs"]


def test_bad_amount():
    assert "MONTANT_INVALIDE" in evaluate(event={**EVENT, "amount": -1})["motifs"]


def test_bad_currency():
    assert "DEVISE_INVALIDE" in evaluate(event={**EVENT, "currency": "xaf"})["motifs"]


def test_unknown_status():
    assert "ETAT_EXTERNE_INVALIDE" in evaluate(event={**EVENT, "status": "PENDING"})["motifs"]


def test_invalid_json():
    assert "CORPS_JSON_INVALIDE" in evaluate(body=b"{")["motifs"]


def test_json_array():
    assert "EVENEMENT_JSON_NON_OBJET" in evaluate(body=b"[]")["motifs"]


def test_expired_signature():
    result = evaluate(now=TS+301)
    assert "HORODATAGE_HORS_FENETRE" in result["motifs"]
    assert not result["controle_registre_effectue"]


def test_wrong_secret():
    assert "SIGNATURE_INVALIDE" in evaluate(secret=b"wrong")["motifs"]


def test_missing_identifiers():
    assert "IDENTIFIANTS_OBLIGATOIRES" in evaluate(event={**EVENT, "event_id": ""})["motifs"]


def test_invalid_history():
    assert "HISTORIQUE_INVALIDE" in evaluate(history="invalid")["motifs"]
