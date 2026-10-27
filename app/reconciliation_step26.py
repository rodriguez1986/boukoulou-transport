"""Diagnostic conservateur des références de recettes (aucune écriture SQL)."""
from collections import defaultdict


def detecter_references_communes(paiements, passes):
    """Retourne les références communes entre paiements SUCCESS et passes V5.9.

    Les entrées sont des dictionnaires contenant reference, montant, provider,
    cash_session_id et status pour les paiements; reference, total, provider,
    cash_session_id pour les passes. Ce diagnostic ne déduit pas que deux
    opérations de références différentes correspondent à une même vente.
    """
    historiques = defaultdict(list)
    ventes = defaultdict(list)
    for p in paiements:
        if str(p.get('status', '')).upper() == 'SUCCESS' and p.get('reference'):
            historiques[str(p['reference'])].append(p)
    for v in passes:
        if v.get('reference'):
            ventes[str(v['reference'])].append(v)
    alertes = []
    for reference in sorted(historiques.keys() & ventes.keys()):
        for paiement in historiques[reference]:
            for vente in ventes[reference]:
                alertes.append({
                    'reference': reference,
                    'montant_paiement': paiement.get('amount'),
                    'montant_passe': vente.get('total'),
                    'session_paiement': paiement.get('cash_session_id'),
                    'session_passe': vente.get('cash_session_id'),
                    'meme_session': paiement.get('cash_session_id') == vente.get('cash_session_id'),
                    'meme_montant': paiement.get('amount') == vente.get('total'),
                })
    return alertes
