"""Étape 34 : prévalidation PURE avant stockage durable d’événements PSP.

Aucune connexion PostgreSQL, aucun appel PSP, aucune écriture.
Les signatures PSP ne sont PAS vérifiées par ce module.
"""
from app.refund_events_step33 import examiner_evenement_remboursement


def preparer_evenement_pour_registre(*, evenement, historique=(), remboursements_connus=()):
    """Décide si un événement pourrait être enregistré; ne l’enregistre jamais."""
    base = examiner_evenement_remboursement(evenement=evenement, historique=historique)
    motifs = list(base['motifs'])
    if not isinstance(remboursements_connus, (list, tuple, set, frozenset)):
        motifs.append('REFERENTIEL_REMBOURSEMENTS_INVALIDE')
    elif isinstance(evenement, dict) and evenement.get('refund_id') not in remboursements_connus:
        motifs.append('REMBOURSEMENT_INCONNU')
    if isinstance(evenement, dict):
        amount = evenement.get('amount')
        currency = evenement.get('currency')
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            motifs.append('MONTANT_INVALIDE')
        if not isinstance(currency, str) or not (len(currency) == 3 and currency.isascii() and currency.isalpha() and currency.isupper()):
            motifs.append('DEVISE_INVALIDE')
    return {
        'enregistrement_possible_en_simulation': not motifs,
        'motifs': list(dict.fromkeys(motifs)),
        'enregistrement_effectue': False,
        'evenement_traite': False,
        'signature_psp_verifiee': False,
        'remboursement_execute': False,
    }
