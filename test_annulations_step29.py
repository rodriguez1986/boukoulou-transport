"""Tests du diagnostic isolé : aucune base de données requise."""
import ast
from pathlib import Path
import importlib.util

spec = importlib.util.spec_from_file_location('annulations_step29', Path(__file__).parent / 'app' / 'annulations_step29.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
diagnostic = mod.diagnostic_annulations


def jeu():
    return ([{'id': 1, 'status': 'CANCELLED'}, {'id': 2, 'status': 'SCHEDULED'}],
            [{'id': 11, 'trip_id': 1}, {'id': 12, 'trip_id': 2}],
            [{'id': 21, 'ticket_id': 11, 'amount': 1500, 'status': 'SUCCESS'},
             {'id': 22, 'ticket_id': 12, 'amount': 2000, 'status': 'SUCCESS'}])


def test_paiement_sur_course_annulee_signale():
    r = diagnostic(*jeu())
    assert r['paiements_valides_sur_courses_annulees'] == 1
    assert r['montant_paiements_a_examiner'] == 1500


def test_course_active_non_signalee():
    r = diagnostic(*jeu())
    assert all(a['payment_id'] != 22 for a in r['alertes'])


def test_paiement_non_valide_exclu():
    c, b, p = jeu()
    p.append({'id': 23, 'ticket_id': 11, 'amount': 999, 'status': 'FAILED'})
    assert diagnostic(c, b, p)['montant_paiements_a_examiner'] == 1500


def test_annulation_nimplique_pas_remboursement():
    r = diagnostic(*jeu())
    assert r['remboursements_confirmes'] is None
    assert r['aucune_deduction_automatique']


def test_remboursement_sans_lien_signale():
    r = diagnostic(*jeu(), remboursements=[{'amount': 100}])
    assert any(a['code'] == 'REMBOURSEMENT_SANS_LIEN_PAIEMENT' for a in r['alertes'])


def test_remboursement_negatif_signale():
    r = diagnostic(*jeu(), remboursements=[{'payment_id': 21, 'amount': -10}])
    assert any(a['code'] == 'MONTANT_REMBOURSEMENT_NEGATIF' for a in r['alertes'])


def test_sources_non_modifiees():
    c, b, p = jeu()
    before = repr((c, b, p))
    diagnostic(c, b, p)
    assert repr((c, b, p)) == before


def test_annulation_existante_sans_remboursement_automatique():
    source = (Path(__file__).parent / 'app' / 'main.py').read_text(encoding='utf-8-sig')
    tree = ast.parse(source)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'cancel_trip')
    fragment = ast.get_source_segment(source, fn)
    assert 'trip.status = "CANCELLED"' in fragment
    assert 'refund' not in fragment.lower() and 'rembours' not in fragment.lower()
