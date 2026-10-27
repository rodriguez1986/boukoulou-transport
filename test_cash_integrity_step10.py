"""Étape 10 : tests statiques et tests PostgreSQL optionnels, sans modification."""
import ast
from pathlib import Path
import os
import pytest

ROOT = Path(__file__).parent

def test_index_unique_partiel():
    sql = (ROOT/"migrations"/"v59_one_open_cash_session_step10.sql").read_text()
    assert "CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS" in sql
    assert "ON cash_sessions (user_id)" in sql
    assert "WHERE status = 'OPEN'" in sql
    assert "HAVING count(*) > 1" in sql

def test_modele_sessions_etat():
    tree = ast.parse((ROOT/"app"/"models.py").read_text())
    cash = next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=="CashSession")
    names = {t.id for n in cash.body if isinstance(n,ast.AnnAssign) for t in [n.target] if isinstance(t,ast.Name)}
    assert {"user_id","status","closed_at"}.issubset(names)

@pytest.mark.skipif(not os.getenv("BOUKOULOU_TEST_DATABASE_URL"), reason="URL PostgreSQL de test absente")
def test_postgres_index_et_doublons_lecture_seule():
    """N'exécute aucun DDL ni INSERT; utiliser une base de test uniquement."""
    from sqlalchemy import create_engine, text
    engine = create_engine(os.environ["BOUKOULOU_TEST_DATABASE_URL"])
    try:
        with engine.connect() as conn:
            dup = conn.execute(text(
                "SELECT user_id, count(*) FROM cash_sessions WHERE status = 'OPEN' "
                "GROUP BY user_id HAVING count(*) > 1"
            )).all()
            assert not dup, f"Plusieurs caisses ouvertes : {dup}"
            index = conn.execute(text(
                "SELECT i.indisunique, i.indisvalid FROM pg_index i "
                "JOIN pg_class c ON c.oid = i.indexrelid "
                "WHERE c.relname = 'ux_cash_sessions_one_open_per_user'"
            )).first()
            assert index is not None and index.indisunique and index.indisvalid
    finally:
        engine.dispose()
