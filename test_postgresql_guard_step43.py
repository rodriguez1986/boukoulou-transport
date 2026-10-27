from pathlib import Path

def test_sql_draft_has_constraints():
    sql = (Path(__file__).parent / "migrations" /
           "v59_payment_audit_step41_DRAFT_NOT_APPLIED.sql").read_text()
    assert "UNIQUE" in sql
    assert "PRIMARY KEY (stream_id, sequence)" in sql
    assert "REFERENCES bt_payment_audit_stream_step41" in sql
    assert "CHECK" in sql


def test_integration_opt_in_is_explicit():
    code = (Path(__file__).parent / "test_postgresql_integration_step43.py").read_text()
    assert "I_UNDERSTAND_TEST_DATABASE_ONLY" in code
    assert "bt_test_" in code
    assert "DROP SCHEMA IF EXISTS" in code
    assert "CREATE SCHEMA" in code
