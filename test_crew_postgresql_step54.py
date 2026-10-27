"""Contrôles PostgreSQL non destructifs ; connexion facultative sur base de TEST.

Activer uniquement avec BT_STEP54_TEST_DATABASE_URL pointant vers une base dédiée.
Aucune table applicative n'est créée ou modifiée par ces tests.
"""
import os
import pytest
from sqlalchemy import create_engine, text, select
from sqlalchemy.dialects import postgresql
from app.models import Trip


def test_verrouillage_trip_compile_postgresql():
    statement = select(Trip.id).where(Trip.id == 42).with_for_update()
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert 'FOR UPDATE' in sql
    assert 'trips.id' in sql


def test_migrations_crew_sont_des_brouillons_non_appliques():
    from pathlib import Path
    root = Path(__file__).parent
    p48 = (root / 'migrations/v59_crew_assignments_step48_DRAFT_NOT_APPLIED.sql').read_text()
    p49 = (root / 'migrations/v59_crew_assignment_admin_step49_DRAFT_NOT_APPLIED.sql').read_text()
    assert 'NON APPLIQUÉ' in p48 and 'NE PAS APPLIQUER' in p49
    assert 'REFERENCES users(id)' in p48
    assert 'REFERENCES bt_crew_assignments_step48(id)' in p49
    assert 'TIMESTAMPTZ' in p48 and 'TIMESTAMPTZ' in p49


def test_verrou_postgresql_sur_table_temporaire_optionnel():
    url = os.environ.get('BT_STEP54_TEST_DATABASE_URL')
    if not url:
        pytest.skip('PostgreSQL de test non configuré (BT_STEP54_TEST_DATABASE_URL)')
    if not url.startswith(('postgresql://', 'postgresql+psycopg://')):
        pytest.fail('La variable doit cibler PostgreSQL, jamais SQLite ou une autre base')
    if os.environ.get('BT_STEP54_CONFIRM_ISOLATED_DB') != 'YES':
        pytest.skip('Confirmation explicite de base isolée manquante')
    # Seule une table temporaire est créée, dans une transaction annulée.
    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            tx = conn.begin()
            try:
                conn.execute(text('CREATE TEMP TABLE bt_step54_lock_test (id integer PRIMARY KEY) ON COMMIT DROP'))
                conn.execute(text('INSERT INTO bt_step54_lock_test(id) VALUES (1)'))
                row = conn.execute(text('SELECT id FROM bt_step54_lock_test WHERE id=1 FOR UPDATE')).scalar_one()
                assert row == 1
            finally:
                tx.rollback()
    finally:
        engine.dispose()
