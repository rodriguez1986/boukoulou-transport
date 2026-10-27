"""Étape 33 — diagnostic PUR de répétition d’événements PSP.

Ne vérifie PAS les signatures ni la réalité d’un remboursement.
Les identifiants et empreintes ne constituent pas une preuve PSP.
"""
import hashlib
import json


def _identifiant(value):
    return value.strip() if isinstance(value, str) and value.strip() else None


def _empreinte(evenement):
    # Empreinte déterministe des seuls champs utiles à la détection des conflits.
    contenu = {k: evenement.get(k) for k in ('provider', 'event_id', 'refund_id', 'status', 'amount', 'currency')}
    return hashlib.sha256(json.dumps(contenu, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def examiner_evenement_remboursement(*, evenement, historique=()):
    """Signale doublons/conflits sans traiter l’événement ni écrire en base.

    L’historique est une collection de dicts représentant des événements déjà vus.
    Une confirmation PSP n’est JAMAIS attestée par ce diagnostic.
    """
    erreurs = []
    if not isinstance(evenement, dict):
        return _decision(['EVENEMENT_INVALIDE'])
    provider = _identifiant(evenement.get('provider'))
    event_id = _identifiant(evenement.get('event_id'))
    refund_id = _identifiant(evenement.get('refund_id'))
    status = _identifiant(evenement.get('status'))
    if not provider or not event_id or not refund_id:
        erreurs.append('IDENTIFIANTS_OBLIGATOIRES')
    if status not in ('CONFIRMED', 'FAILED'):
        erreurs.append('ETAT_EXTERNE_INVALIDE')
    if not isinstance(historique, (tuple, list)):
        erreurs.append('HISTORIQUE_INVALIDE')
        historique = ()
    identite = (provider, event_id)
    for precedent in historique:
        if not isinstance(precedent, dict):
            erreurs.append('HISTORIQUE_INVALIDE')
            continue
        if (_identifiant(precedent.get('provider')), _identifiant(precedent.get('event_id'))) != identite:
            continue
        if not provider or not event_id:
            continue
        if _empreinte(precedent) == _empreinte(evenement):
            erreurs.append('EVENEMENT_DEJA_VU')
        else:
            erreurs.append('EVENEMENT_CONFLICTUEL')
    return _decision(list(dict.fromkeys(erreurs)))


def _decision(erreurs):
    return {
        'nouvel_evenement_possible_en_simulation': not erreurs,
        'motifs': erreurs,
        'evenement_traite': False,
        'etat_modifie': False,
        'remboursement_execute': False,
        'audit_enregistre': False,
        'signature_psp_verifiee': False,
        'preuve_psp_verifiee': False,
    }
