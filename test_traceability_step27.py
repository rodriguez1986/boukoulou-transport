"""Tests de rapprochement purement en mémoire, sans PostgreSQL."""
from copy import deepcopy
from pathlib import Path
import ast
from app.traceability_step27 import tracer_ventes_v59


def pass_(id=1, reference='V59-A', total=3000, cash_session_id=7):
    return dict(id=id, reference=reference, total=total, cash_session_id=cash_session_id)


def bord_(id=10, pass_id=1, total_amount=3000, cash_session_id=7):
    return dict(id=id, pass_id=pass_id, total_amount=total_amount, cash_session_id=cash_session_id)


def test_guichet_sans_vente_bord():
    result = tracer_ventes_v59([pass_()], [])
    assert result['lignes'][0]['origine'] == 'GUICHET'
    assert result['anomalies'] == []


def test_bord_avec_lien_pass_id_et_montants_coherents():
    result = tracer_ventes_v59([pass_()], [bord_()])
    assert result['lignes'][0]['origine'] == 'BORD'
    assert result['anomalies'] == []


def test_bord_orphelin_signale():
    result = tracer_ventes_v59([], [bord_()])
    assert result['anomalies'][0]['type'] == 'VENTE_BORD_SANS_PASS'


def test_bord_multiple_signale():
    result = tracer_ventes_v59([pass_()], [bord_(), bord_(id=11)])
    assert 'PLUSIEURS_VENTES_BORD' in {a['type'] for a in result['anomalies']}


def test_ecart_montant_et_caisse_signales():
    result = tracer_ventes_v59([pass_()], [bord_(total_amount=2000, cash_session_id=8)])
    assert {a['type'] for a in result['anomalies']} == {'MONTANTS_DIFFERENTS', 'CAISSES_DIFFERENTES'}


def test_reference_commune_paiement_historique_alerte_seulement():
    payments = [{'reference': 'V59-A', 'status': 'SUCCESS', 'amount': 3000}]
    result = tracer_ventes_v59([pass_()], [], payments)
    assert result['lignes'][0]['paiements_historiques_meme_reference'] == 1
    assert result['anomalies'][0]['type'] == 'REFERENCE_PAIEMENT_COMMUNE'
    assert result['lignes'][0]['montant_pass'] == 3000


def test_paiement_non_valide_ignore():
    result = tracer_ventes_v59([pass_()], [], [{'reference': 'V59-A', 'status': 'FAILED'}])
    assert result['anomalies'] == []


def test_aucune_mutation_des_donnees():
    p, b = [pass_()], [bord_()]
    avant = deepcopy((p, b))
    tracer_ventes_v59(p, b)
    assert (p, b) == avant


def test_modele_contient_lien_pass_id_unique():
    source = (Path(__file__).parent / 'app' / 'v59.py').read_text(encoding='utf-8-sig')
    assert "UniqueConstraint('pass_id', name='uq_v59_onboard_pass')" in source
    assert "ForeignKey('v59_passes.id')" in source


def test_module_diagnostic_sans_sql_ni_ecriture():
    tree = ast.parse((Path(__file__).parent / 'app' / 'traceability_step27.py').read_text())
    assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in {'commit','execute','add','delete','flush','rollback'} for n in ast.walk(tree))
