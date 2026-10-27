"""Prévalidation métier d'une demande de remboursement, sans effet de bord.

Étape 30 : AUCUN remboursement, accès BD, écriture comptable ou audit n'est exécuté.
La validation est indicative : les droits et soldes doivent être revérifiés sous
verrou transactionnel au moment de la future exécution PostgreSQL.
"""
from decimal import Decimal, InvalidOperation

ALLOWED_ROLES = frozenset({"ADMIN"})  # Règle provisoire à faire approuver.


def _amount(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    if not amount.is_finite() or amount != amount.to_integral_value():
        return None
    return int(amount)


def verifier_demande_remboursement(*, role, payment, montant, cle_idempotence,
                                    remboursements_existants=()):
    """Retourne une décision et ses motifs; aucune mutation des entrées."""
    erreurs = []
    role = getattr(role, "value", role)
    if role not in ALLOWED_ROLES:
        erreurs.append("ROLE_NON_AUTORISE")
    if not isinstance(payment, dict) or not payment.get("id"):
        erreurs.append("PAIEMENT_ABSENT")
        payment = {}
    if str(payment.get("status", "")).upper() != "SUCCESS":
        erreurs.append("PAIEMENT_NON_VALIDE")
    if not isinstance(cle_idempotence, str) or not cle_idempotence.strip():
        erreurs.append("CLE_IDEMPOTENCE_REQUISE")
    total = _amount(payment.get("amount"))
    demande = _amount(montant)
    if total is None or total <= 0:
        erreurs.append("MONTANT_PAIEMENT_INVALIDE")
    if demande is None or demande <= 0:
        erreurs.append("MONTANT_REMBOURSEMENT_INVALIDE")
    deja = 0
    for r in remboursements_existants:
        if not isinstance(r, dict) or r.get("payment_id") != payment.get("id"):
            continue
        if cle_idempotence and r.get("idempotency_key") == cle_idempotence:
            erreurs.append("DEMANDE_DEJA_ENREGISTREE")
        # Seuls les remboursements confirmés consomment le plafond; les
        # demandes en attente doivent être réservées dans le futur registre.
        if str(r.get("status", "")).upper() == "CONFIRMED":
            valeur = _amount(r.get("amount"))
            if valeur is None or valeur <= 0:
                erreurs.append("HISTORIQUE_REMBOURSEMENTS_INVALIDE")
            else:
                deja += valeur
    if total is not None and demande is not None and demande > 0 and deja + demande > total:
        erreurs.append("PLAFOND_REMBOURSEMENT_DEPASSE")
    return {"autorise_en_prevalidation": not erreurs,
            "motifs": list(dict.fromkeys(erreurs)),
            "montant_deja_confirme": deja,
            "plafond_paiement": total,
            "execution_effectuee": False,
            "audit_enregistre": False,
            "aucune_ecriture": True}
