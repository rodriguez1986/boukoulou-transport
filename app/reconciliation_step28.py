"""Rapprochement explicatif, en mémoire et sans écriture.

Les références communes restent des suspicions : aucune déduction automatique.
Les ventes à bord sont déjà représentées par les passes V5.9.
"""
from collections import defaultdict
from .traceability_step27 import tracer_ventes_v59


def rapport_rapprochement(paiements, passes, ventes_bord):
    """Synthèse conservatrice des sources, sans supprimer ni fusionner les ventes.

    Les montants sont des unités entières (ex. FCFA). Les entrées sont des dicts.
    Une absence de référence n'autorise jamais un rapprochement implicite.
    """
    paiements = list(paiements)
    passes = list(passes)
    ventes_bord = list(ventes_bord)
    trace = tracer_ventes_v59(passes, ventes_bord, paiements)
    historiques_valides = [p for p in paiements if str(p.get('status', '')).upper() == 'SUCCESS']
    historiques = sum(int(p.get('amount') or 0) for p in historiques_valides)
    v59 = sum(int(p.get('total') or 0) for p in passes)
    refs_hist = defaultdict(list)
    for p in historiques_valides:
        if p.get('reference'):
            refs_hist[str(p['reference'])].append(p)
    rapprochements = []
    for p in passes:
        ref = p.get('reference')
        if not ref:
            continue
        for historique in refs_hist.get(str(ref), []):
            rapprochements.append({
                'reference': str(ref), 'pass_id': p.get('id'),
                'meme_montant': historique.get('amount') == p.get('total'),
                'meme_caisse': historique.get('cash_session_id') == p.get('cash_session_id'),
                'statut': 'A_VERIFIER',
            })
    return {
        'recettes_historiques_validees': historiques,
        'recettes_passes_v59': v59,
        'total_brut_non_dedoublonne': historiques + v59,
        'nombre_ventes_bord': len(ventes_bord),
        'ventes_bord_deja_dans_passes': True,
        'rapprochements_a_verifier': rapprochements,
        'anomalies': trace['anomalies'],
        'aucune_correction_automatique': True,
    }
