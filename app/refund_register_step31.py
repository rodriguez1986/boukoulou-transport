"""Étape 31 : simulation du registre des remboursements, sans écriture.

Les états PENDING et PROCESSING réservent le plafond; CONFIRMED le consomme.
La réservation doit être atomique sous verrou PostgreSQL lors d'une future API.
"""
from app.refund_rules_step30 import _amount, verifier_demande_remboursement

RESERVED = frozenset({"PENDING", "PROCESSING", "CONFIRMED"})


def examiner_reservation(*, role, payment, montant, cle_idempotence, registre=()):
    """Diagnostic pur; retourne une décision et un état fictif, sans réservation réelle."""
    base = verifier_demande_remboursement(
        role=role, payment=payment, montant=montant,
        cle_idempotence=cle_idempotence, remboursements_existants=registre)
    erreurs = list(base["motifs"])
    payment_id = payment.get("id") if isinstance(payment, dict) else None
    reserve = 0
    for entry in registre:
        if not isinstance(entry, dict) or entry.get("payment_id") != payment_id:
            continue
        status = str(entry.get("status", "")).upper()
        if status not in RESERVED:
            continue
        value = _amount(entry.get("amount"))
        if value is None or value <= 0:
            erreurs.append("HISTORIQUE_RESERVATIONS_INVALIDE")
        else:
            reserve += value
    amount = _amount(montant)
    ceiling = _amount(payment.get("amount")) if isinstance(payment, dict) else None
    if amount is not None and amount > 0 and ceiling is not None and reserve + amount > ceiling:
        erreurs.append("PLAFOND_AVEC_RESERVATIONS_DEPASSE")
    return {
        "reservation_possible_en_simulation": not erreurs,
        "motifs": list(dict.fromkeys(erreurs)),
        "montant_deja_reserve_ou_confirme": reserve,
        "plafond_paiement": ceiling,
        "reservation_effectuee": False,
        "remboursement_execute": False,
        "audit_enregistre": False,
    }
