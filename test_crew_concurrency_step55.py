"""Étape 55 : scénarios de concurrence et limites, sans toucher la production."""
import os
import threading
from pathlib import Path
import pytest
from sqlalchemy import create_engine, text


def test_verrouillage_et_controle_chevauchement_dans_service():
    src = (Path(__file__).parent / "app/crew_assignment_admin_step49.py").read_text()
    assert "select(Trip.id).where(Trip.id == trip_id).with_for_update()" in src
    assert "CrewAssignmentStep48.active.is_(True)" in src
    assert "_refuser('AFFECTATION_CHEVAUCHANTE')" in src
    assert "db.rollback()" in src


def test_routes_non_activees():
    main = (Path(__file__).parent / "app/main.py").read_text()
    assert "crew_assignment_api_step50" not in main


def test_verrouillage_postgresql_deux_sessions_optionnel():
    """Deux transactions indépendantes : la seconde échoue au lock_timeout.

    Utilise un verrou transactionnel consultatif, sans table ni écriture.
    Ce test ne prouve PAS le verrouillage des lignes applicatives.
    """
    url = os.environ.get('BT_STEP55_TEST_DATABASE_URL')
    if not url:
        pytest.skip('PostgreSQL de test non configuré (BT_STEP55_TEST_DATABASE_URL)')
    if not url.startswith(('postgresql://', 'postgresql+psycopg://')):
        pytest.fail('URL PostgreSQL obligatoire')
    if os.environ.get('BT_STEP55_CONFIRM_ISOLATED_DB') != 'YES':
        pytest.skip('Confirmation explicite de base de test isolée absente')
    pytest.importorskip('psycopg')
    engine = create_engine(url, pool_size=2, max_overflow=0, pool_pre_ping=True)
    held = threading.Event()
    release = threading.Event()
    errors = []
    def first():
        try:
            with engine.connect() as c:
                with c.begin():
                    c.execute(text('SELECT pg_advisory_xact_lock(550055)'))
                    held.set()
                    if not release.wait(8):
                        raise AssertionError('Timeout en attente du second thread')
        except Exception as exc:
            errors.append(exc)
            held.set()
    worker = threading.Thread(target=first, daemon=True)
    try:
        worker.start()
        assert held.wait(8), 'Première transaction non démarrée'
        assert not errors, errors
        with engine.connect() as c:
            with c.begin():
                c.execute(text("SET LOCAL lock_timeout = '250ms'"))
                with pytest.raises(Exception) as excinfo:
                    c.execute(text('SELECT pg_advisory_xact_lock(550055)'))
                # SQLSTATE 55P03 : lock_not_available ; pas un problème de connexion.
                assert getattr(getattr(excinfo.value, 'orig', None), 'sqlstate', None) == '55P03'
    finally:
        release.set()
        worker.join(timeout=8)
        engine.dispose()
    assert not worker.is_alive()
    assert not errors, errors
