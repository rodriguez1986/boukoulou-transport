from copy import deepcopy
from app.reconciliation_step28 import rapport_rapprochement


def test_ventes_bord_non_additionnees_aux_passes():
    r = rapport_rapprochement([], [{'id': 1, 'total': 500, 'cash_session_id': 1}], [{'id': 2, 'pass_id': 1, 'total_amount': 500, 'cash_session_id': 1}])
    assert r['total_brut_non_dedoublonne'] == 500
    assert r['nombre_ventes_bord'] == 1


def test_seuls_paiements_valides():
    r = rapport_rapprochement([{'amount': 100, 'status': 'SUCCESS'}, {'amount': 900, 'status': 'FAILED'}], [], [])
    assert r['recettes_historiques_validees'] == 100


def test_reference_commune_reste_a_verifier():
    p = {'reference': 'A', 'amount': 100, 'status': 'SUCCESS', 'cash_session_id': 1}
    v = {'id': 1, 'reference': 'A', 'total': 100, 'cash_session_id': 1}
    r = rapport_rapprochement([p], [v], [])
    assert r['total_brut_non_dedoublonne'] == 200
    assert r['rapprochements_a_verifier'] == [{'reference': 'A', 'pass_id': 1, 'meme_montant': True, 'meme_caisse': True, 'statut': 'A_VERIFIER'}]


def test_reference_differente_pas_de_fusion():
    r = rapport_rapprochement([{'reference': 'A', 'amount': 100, 'status': 'SUCCESS'}], [{'id': 1, 'reference': 'B', 'total': 100}], [])
    assert not r['rapprochements_a_verifier']


def test_ecarts_signalises():
    r = rapport_rapprochement([], [{'id': 1, 'total': 100, 'cash_session_id': 1}], [{'id': 3, 'pass_id': 1, 'total_amount': 90, 'cash_session_id': 2}])
    assert {'MONTANTS_DIFFERENTS', 'CAISSES_DIFFERENTES'} <= {a['type'] for a in r['anomalies']}


def test_entrees_non_modifiees():
    h = [{'reference': 'X', 'amount': 1, 'status': 'SUCCESS'}]
    p = [{'id': 1, 'reference': 'X', 'total': 1}]
    b = []
    before = deepcopy((h, p, b))
    rapport_rapprochement(h, p, b)
    assert (h, p, b) == before
