import time

from app.psp_signature_step35 import signer_notification_test, verifier_notification_psp


SECRET = b"cle-de-test-sans-valeur-en-production"
BODY = b'{"refund_id":"r-1","amount":1000}'


def check(body=BODY, secret=SECRET, ts=1700000000, now=1700000000, signature=None, **kw):
    if signature is None:
        signature = signer_notification_test(corps_brut=BODY, secret=SECRET, horodatage=1700000000)
    return verifier_notification_psp(corps_brut=body, secret=secret, signature=signature,
                                    horodatage=ts, maintenant=now, **kw)


def test_signature_valide():
    result = check()
    assert result["signature_valide_en_protocole_test"]
    assert not result["protocole_psp_reel_verifie"]
    assert not result["evenement_enregistre"]


def test_corps_modifie_refuse():
    assert "SIGNATURE_INVALIDE" in check(body=BODY + b" ")["motifs"]


def test_secret_incorrect_refuse():
    assert "SIGNATURE_INVALIDE" in check(secret=b"mauvaise-cle")["motifs"]


def test_horodatage_modifie_refuse():
    assert "SIGNATURE_INVALIDE" in check(ts=1700000001)["motifs"]


def test_signature_modifiee_refusee():
    assert "SIGNATURE_INVALIDE" in check(signature="0"*64)["motifs"]


def test_signature_mal_formee():
    assert "SIGNATURE_FORMAT_INVALIDE" in check(signature="not-hex")["motifs"]


def test_signature_majuscule_acceptee():
    sig = signer_notification_test(corps_brut=BODY, secret=SECRET, horodatage=1700000000)
    assert check(signature=sig.upper())["signature_valide_en_protocole_test"]


def test_horodatage_expire():
    assert "HORODATAGE_HORS_FENETRE" in check(now=1700000301)["motifs"]


def test_horodatage_futur_lointain():
    assert "HORODATAGE_HORS_FENETRE" in check(now=1699999699)["motifs"]


def test_fenetre_inclusive():
    assert check(now=1700000300)["signature_valide_en_protocole_test"]


def test_corps_non_bytes():
    assert "CORPS_BRUT_INVALIDE" in check(body="texte")["motifs"]


def test_secret_vide():
    assert "SECRET_INVALIDE" in check(secret=b"")["motifs"]


def test_timestamp_bool():
    assert "HORODATAGE_INVALIDE" in check(ts=True)["motifs"]


def test_tolerance_negative():
    assert "TOLERANCE_INVALIDE" in check(tolerance_secondes=-1)["motifs"]


def test_heure_reference_invalide():
    assert "HEURE_REFERENCE_INVALIDE" in check(now=-1)["motifs"]


def test_signature_refuse_corps_meme_json_reformate():
    assert "SIGNATURE_INVALIDE" in check(body=b'{"amount":1000,"refund_id":"r-1"}')["motifs"]
