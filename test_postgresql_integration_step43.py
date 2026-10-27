"""Tests PostgreSQL réels, strictement opt-in et isolés dans un schéma éphémère.

Exécuter uniquement sur une base DE TEST avec droits CREATE SCHEMA.
N'exécute jamais la migration dans le schéma public.
"""
import os
import re
import threading
import uuid
from pathlib import Path

import pytest

from app.payment_routing_step38 import DemandePaiement
from app.payment_lifecycle_step39 import demarrer_simulation
from app.payment_audit_step40 import initialiser_journal, journaliser_transition
from app.payment_audit_transaction_step42 import (
    enregistrer_journal_initial, enregistrer_transition, EcritureAuditRefusee,
)

OPT_IN = os.environ.get("BT_STEP43_PG_TEST_ENABLE") == "I_UNDERSTAND_TEST_DATABASE_ONLY"
DSN = os.environ.get("BT_STEP43_PG_TEST_DSN", "")

pytestmark = pytest.mark.skipif(
    not (OPT_IN and DSN),
    reason="PostgreSQL réel désactivé : opt-in + DSN de base de test requis",
)


@pytest.fixture(scope="module")
def environnement():
    psycopg = pytest.importorskip("psycopg2")
    if not DSN or not OPT_IN:
        pytest.skip("Opt-in manquant")
    # Précondition : l'opérateur fournit explicitement une base dédiée.
    # Le nom de la base est contrôlé pour réduire le risque d'erreur humaine.
    with psycopg.connect(DSN) as verifier:
        with verifier.cursor() as cur:
            cur.execute("SELECT current_database()")
            nom = cur.fetchone()[0]
    if not (nom.startswith("bt_test_") or nom.endswith("_test")):
        pytest.fail("Nom de base non dédié aux tests (bt_test_* ou *_test requis)")
    schema = "bt_step43_" + uuid.uuid4().hex[:16]
    ddl = (Path(__file__).parent / "migrations" /
           "v59_payment_audit_step41_DRAFT_NOT_APPLIED.sql").read_text(encoding="utf-8")
    # Ne pas rejouer BEGIN/COMMIT à l'intérieur de la transaction de fixture.
    ddl = re.sub(r"(?im)^\s*(BEGIN|COMMIT)\s*;\s*$", "", ddl)
    admin = psycopg.connect(DSN)
    admin.autocommit = True
    try:
        with admin.cursor() as cur:
            cur.execute('CREATE SCHEMA "' + schema + '"')
        def connecter():
            conn = psycopg.connect(DSN, options="-c search_path=" + schema)
            conn.autocommit = False
            return conn
        with connecter() as conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
            conn.commit()
        yield connecter
    finally:
        # Nettoyage UNIQUEMENT du schéma aléatoire créé dans la base de test.
        try:
            with admin.cursor() as cur:
                cur.execute('DROP SCHEMA IF EXISTS "' + schema + '" CASCADE')
        finally:
            admin.close()


def journaux(reference):
    p = demarrer_simulation(
        DemandePaiement("CG", "EN_LIGNE", "MTN_MOMO", 2500), reference
    )["paiement"]
    initial = initialiser_journal(p)["journal"]
    final = journaliser_transition(
        p, initial, "CONFIRME", acteur="PSP_SIMULE",
        reference_confirmation="SIM-" + reference
    )["journal"]
    return initial, final


def test_insert_and_transition_real_pg(environnement):
    initial, final = journaux("BIL-PG-43-1")
    with environnement() as conn:
        assert enregistrer_journal_initial(conn, initial)["enregistre"]
        assert enregistrer_transition(conn, final)["enregistre"]
        with conn.cursor() as cur:
            cur.execute("""SELECT s.statut, s.derniere_sequence, count(e.sequence)
                FROM bt_payment_audit_stream_step41 s
                JOIN bt_payment_audit_entry_step41 e ON e.stream_id=s.stream_id
                WHERE s.reference_billet=%s GROUP BY s.stream_id""",
                ("BIL-PG-43-1",))
            assert cur.fetchone() == ("CONFIRME", 2, 2)


def test_duplicate_reference_rollback_real_pg(environnement):
    initial, _ = journaux("BIL-PG-43-2")
    with environnement() as conn:
        enregistrer_journal_initial(conn, initial)
        with pytest.raises(Exception):
            enregistrer_journal_initial(conn, initial)
        with conn.cursor() as cur:
            cur.execute("""SELECT count(*) FROM bt_payment_audit_stream_step41
                           WHERE reference_billet=%s""", ("BIL-PG-43-2",))
            assert cur.fetchone()[0] == 1


def test_competing_transitions_real_pg(environnement):
    initial, final = journaux("BIL-PG-43-3")
    with environnement() as conn:
        enregistrer_journal_initial(conn, initial)
    barrier = threading.Barrier(2)
    outcomes = []
    lock = threading.Lock()

    def worker():
        with environnement() as conn:
            barrier.wait(timeout=10)
            try:
                enregistrer_transition(conn, final)
                result = "ok"
            except EcritureAuditRefusee:
                result = "refuse"
            with lock:
                outcomes.append(result)

    a = threading.Thread(target=worker)
    b = threading.Thread(target=worker)
    a.start(); b.start()
    a.join(timeout=15); b.join(timeout=15)
    assert not a.is_alive() and not b.is_alive()
    assert sorted(outcomes) == ["ok", "refuse"]
    with environnement() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT count(*) FROM bt_payment_audit_entry_step41 e
                JOIN bt_payment_audit_stream_step41 s ON s.stream_id=e.stream_id
                WHERE s.reference_billet=%s""", ("BIL-PG-43-3",))
            assert cur.fetchone()[0] == 2
