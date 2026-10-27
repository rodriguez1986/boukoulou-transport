
"""Tests PostgreSQL opt-in dans une table isolée; jamais dans les tables métier.

Exécution : BOUKOULOU_TEST_DATABASE_URL=postgresql+psycopg://.../boukoulou_test
            BOUKOULOU_ALLOW_TEST_DB_WRITE=YES pytest -q test_cash_concurrency_step12.py
"""
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

@pytest.fixture(scope="module")
def isolated_cash_table():
    url = os.getenv("BOUKOULOU_TEST_DATABASE_URL")
    if not url or os.getenv("BOUKOULOU_ALLOW_TEST_DB_WRITE") != "YES":
        pytest.skip("Test PostgreSQL désactivé : URL et consentement explicite requis")
    sqlalchemy = pytest.importorskip("sqlalchemy")
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url
    parsed = make_url(url)
    if not parsed.drivername.startswith("postgresql") or not (parsed.database or "").endswith("_test"):
        pytest.fail("Refus de modifier une base autre qu'une base PostgreSQL suffixée _test")
    engine = create_engine(url, pool_size=3, max_overflow=2, connect_args={"connect_timeout": 5})
    table = "bt_cash_step12_" + uuid.uuid4().hex[:16]
    # Identifiant généré localement, sans entrée utilisateur.
    try:
        with engine.begin() as conn:
            conn.execute(text(f"CREATE TABLE {table} (id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL, status TEXT NOT NULL)"))
            conn.execute(text(f"CREATE UNIQUE INDEX ux_{table} ON {table} (user_id) WHERE status = 'OPEN'"))
        yield engine, table
    finally:
        try:
            with engine.begin() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
        finally:
            engine.dispose()

def test_deux_ouvertures_concurrentes_meme_utilisateur(isolated_cash_table):
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError
    engine, table = isolated_cash_table
    barrier = Barrier(2, timeout=10)
    def open_cash():
        with engine.connect() as conn:
            # Les deux transactions essaient d'insérer au même moment.
            barrier.wait()
            try:
                conn.execute(text(f"INSERT INTO {table} (user_id,status) VALUES (101,'OPEN')"))
                conn.commit()
                return "success"
            except IntegrityError as exc:
                conn.rollback()
                assert getattr(getattr(exc.orig, "diag", None), "constraint_name", None) == f"ux_{table}"
                return "conflict"
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: open_cash(), range(2)))
    assert sorted(results) == ["conflict", "success"]

def test_deux_utilisateurs_peuvent_ouvrir(isolated_cash_table):
    from sqlalchemy import text
    engine, table = isolated_cash_table
    with engine.begin() as conn:
        conn.execute(text(f"INSERT INTO {table} (user_id,status) VALUES (201,'OPEN'), (202,'OPEN')"))
        n = conn.execute(text(f"SELECT count(*) FROM {table} WHERE user_id IN (201,202) AND status='OPEN'")).scalar_one()
        assert n == 2

def test_reouverture_apres_cloture(isolated_cash_table):
    from sqlalchemy import text
    engine, table = isolated_cash_table
    with engine.begin() as conn:
        conn.execute(text(f"INSERT INTO {table} (user_id,status) VALUES (301,'OPEN')"))
        conn.execute(text(f"UPDATE {table} SET status='CLOSED' WHERE user_id=301"))
        conn.execute(text(f"INSERT INTO {table} (user_id,status) VALUES (301,'OPEN')"))
        assert conn.execute(text(f"SELECT count(*) FROM {table} WHERE user_id=301 AND status='OPEN'")).scalar_one() == 1

def test_une_ouverture_par_utilisateur_reste_possible(isolated_cash_table):
    from sqlalchemy import text
    engine, table = isolated_cash_table
    with engine.begin() as conn:
        conn.execute(text(f"INSERT INTO {table} (user_id,status) VALUES (401,'OPEN'), (402,'OPEN')"))
        assert conn.execute(text(f"SELECT count(*) FROM {table} WHERE status='OPEN' AND user_id IN (401,402)")).scalar_one() == 2
