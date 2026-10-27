"""Étape 35 — vérification HMAC-SHA256 générique d'une notification PSP.

Ce format de signature est une démonstration interne, PAS une intégration
Stripe, PayPal, Airtel Money, MTN MoMo ou d'un autre PSP.
Aucune écriture, aucun remboursement, aucun appel réseau.
"""
import hashlib
import hmac
import re
import time

_SIGNATURE = re.compile(r"^[0-9a-fA-F]{64}$")


def signer_notification_test(*, corps_brut, secret, horodatage):
    """Signature du protocole de démonstration: HMAC(secret, timestamp + b'.' + raw_body)."""
    if not isinstance(corps_brut, bytes) or not isinstance(secret, bytes) or not secret:
        raise ValueError("corps_brut et secret doivent être des bytes (secret non vide)")
    if isinstance(horodatage, bool) or not isinstance(horodatage, int) or horodatage < 0:
        raise ValueError("horodatage entier positif requis")
    message = str(horodatage).encode("ascii") + b"." + corps_brut
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def verifier_notification_psp(*, corps_brut, signature, horodatage, secret,
                              maintenant=None, tolerance_secondes=300):
    """Vérification cryptographique isolée du protocole de démonstration.

    `maintenant` injectable pour les tests. Une signature valide ne prouve
    ni un remboursement effectif ni l'identité d'un PSP réel.
    """
    motifs = []
    if not isinstance(corps_brut, bytes):
        motifs.append("CORPS_BRUT_INVALIDE")
    if not isinstance(secret, bytes) or not secret:
        motifs.append("SECRET_INVALIDE")
    if not isinstance(signature, str) or not _SIGNATURE.fullmatch(signature):
        motifs.append("SIGNATURE_FORMAT_INVALIDE")
    if isinstance(horodatage, bool) or not isinstance(horodatage, int) or horodatage < 0:
        motifs.append("HORODATAGE_INVALIDE")
    if isinstance(tolerance_secondes, bool) or not isinstance(tolerance_secondes, int) or tolerance_secondes < 0:
        motifs.append("TOLERANCE_INVALIDE")
    if maintenant is None:
        maintenant = int(time.time())
    if isinstance(maintenant, bool) or not isinstance(maintenant, int) or maintenant < 0:
        motifs.append("HEURE_REFERENCE_INVALIDE")
    if not motifs:
        if abs(maintenant - horodatage) > tolerance_secondes:
            motifs.append("HORODATAGE_HORS_FENETRE")
        attendu = signer_notification_test(
            corps_brut=corps_brut, secret=secret, horodatage=horodatage
        )
        if not hmac.compare_digest(attendu, signature.lower()):
            motifs.append("SIGNATURE_INVALIDE")
    return {
        "signature_valide_en_protocole_test": not motifs,
        "motifs": motifs,
        "protocole_psp_reel_verifie": False,
        "anti_rejeu_persistant_actif": False,
        "evenement_enregistre": False,
        "remboursement_execute": False,
    }
