"""Tests sans PostgreSQL de la répartition financière et des invariants de caisse."""
import ast
from pathlib import Path
from unittest.mock import MagicMock, patch
from types import ModuleType
import sys

ROOT = Path(__file__).parent
MAIN = (ROOT / 'app/main.py').read_text(encoding='utf-8-sig')
TREE = ast.parse(MAIN)
CLOSE = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == 'close_cash_session')
CURRENT = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == 'current_cash_session')
CLOSE_CODE = ast.get_source_segment(MAIN, CLOSE)
CURRENT_CODE = ast.get_source_segment(MAIN, CURRENT)


def test_cloture_et_consultation_meme_source_especes():
    for code in (CLOSE_CODE, CURRENT_CODE):
        assert 'calculer_recettes_par_provider(' in code
        assert 'recettes_par_provider.get("CASH", 0)' in code
        assert 'session.opening_amount + cash_revenue' in code


def test_ecart_de_cloture_coherent():
    assert 'session.difference_amount = data.declared_amount - expected' in CLOSE_CODE
    assert 'session.expected_amount = expected' in CLOSE_CODE
    assert 'session.declared_amount = data.declared_amount' in CLOSE_CODE


def test_total_commercial_issu_du_detail_provider():
    assert 'total_revenue = sum(recettes_par_provider.values())' in CLOSE_CODE


def test_repartition_provider_exclut_paiements_non_valides():
    code = (ROOT / 'app/payment_breakdown.py').read_text(encoding='utf-8')
    assert 'Payment.status == PaymentStatus.SUCCESS' in code
    assert 'Payment.cash_session_id == cash_session_id' in code
    assert 'Pass59.cash_session_id == cash_session_id' in code


def test_repartition_reelle_avec_donnees_simulees():
    # Exécute la vraie fonction de répartition avec des résultats SQL simulés.
    # Remplacer uniquement le module V5.9 lourd par un substitut de modèle.
    # Cela évite d’importer les dépendances JWT non installées localement.
    stub = ModuleType("app.v59")
    stub.Pass59 = type("Pass59", (), {"provider": "provider", "total": "total", "cash_session_id": "cash_session_id"})
    with patch.dict(sys.modules, {"app.v59": stub}):
        from app.payment_breakdown import calculer_recettes_par_provider
    db = MagicMock()
    payments = MagicMock()
    passes = MagicMock()
    payments.filter.return_value = payments
    passes.filter.return_value = passes
    payments.group_by.return_value.all.return_value = [('CASH', 1500), ('MOBILE_MONEY', 900)]
    passes.group_by.return_value.all.return_value = [('cash', 2500), ('CARD', 1200)]
    db.query.side_effect = [payments, passes]
    result = calculer_recettes_par_provider(db, cash_session_id=17)
    assert result == {'CASH': 4000, 'MOBILE_MONEY': 900, 'CARD': 1200}
    assert sum(result.values()) == 6100
    assert 1000 + result['CASH'] == 5000  # fonds initial + espèces
    assert 4800 - (1000 + result['CASH']) == -200  # écart déclaré
    assert payments.filter.called and passes.filter.called


def test_audit_transaction_et_verrouillage_conserves():
    assert '.with_for_update().first()' in CLOSE_CODE
    assert CLOSE_CODE.count('db.commit()') == 1
    assert 'db.rollback()' in CLOSE_CODE
