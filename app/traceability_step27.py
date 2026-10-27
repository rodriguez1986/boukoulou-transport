"""Rapprochement diagnostique en lecture seule des ventes V5.9.

Les liens fiables entre vente à bord et pass reposent sur pass_id.
Les rapprochements avec les paiements historiques ne sont que des alertes.
"""
from collections import defaultdict


def tracer_ventes_v59(passes, ventes_bord, paiements=()):
    """Retourne des lignes par pass et des anomalies, sans mutation des entrées.

    Chaque entrée est un dict. Pass: id, reference, total, cash_session_id,
    provider; bord: id, pass_id, total_amount, cash_session_id; paiement:
    reference, amount, status, cash_session_id.
    """
    passes_par_id = defaultdict(list)
    for p in passes:
        passes_par_id[p.get('id')].append(p)
    bord_par_pass = defaultdict(list)
    for vente in ventes_bord:
        bord_par_pass[vente.get('pass_id')].append(vente)
    paiements_par_ref = defaultdict(list)
    for paiement in paiements:
        if str(paiement.get('status', '')).upper() == 'SUCCESS' and paiement.get('reference'):
            paiements_par_ref[str(paiement['reference'])].append(paiement)

    lignes, anomalies = [], []
    for p in passes:
        pid = p.get('id')
        ventes = bord_par_pass.get(pid, [])
        if len(passes_par_id[pid]) > 1:
            anomalies.append({'type': 'PASS_ID_REPETE', 'pass_id': pid})
        if len(ventes) > 1:
            anomalies.append({'type': 'PLUSIEURS_VENTES_BORD', 'pass_id': pid, 'nombre': len(ventes)})
        for v in ventes:
            if v.get('cash_session_id') != p.get('cash_session_id'):
                anomalies.append({'type': 'CAISSES_DIFFERENTES', 'pass_id': pid, 'vente_bord_id': v.get('id')})
            if v.get('total_amount') != p.get('total'):
                anomalies.append({'type': 'MONTANTS_DIFFERENTS', 'pass_id': pid, 'vente_bord_id': v.get('id')})
        ref = p.get('reference')
        liens_paiements = paiements_par_ref.get(str(ref), []) if ref else []
        if liens_paiements:
            anomalies.append({'type': 'REFERENCE_PAIEMENT_COMMUNE', 'pass_id': pid, 'reference': ref, 'nombre': len(liens_paiements)})
        lignes.append({
            'pass_id': pid,
            'reference': ref,
            'origine': 'BORD' if ventes else 'GUICHET',
            'nombre_ventes_bord': len(ventes),
            'montant_pass': p.get('total'),
            'caisse_pass': p.get('cash_session_id'),
            'paiements_historiques_meme_reference': len(liens_paiements),
        })
    for vente in ventes_bord:
        if vente.get('pass_id') not in passes_par_id:
            anomalies.append({'type': 'VENTE_BORD_SANS_PASS', 'pass_id': vente.get('pass_id'), 'vente_bord_id': vente.get('id')})
    return {'lignes': lignes, 'anomalies': anomalies}
