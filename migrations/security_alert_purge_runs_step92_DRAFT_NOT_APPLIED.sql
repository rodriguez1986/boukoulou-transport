-- ÉTAPE 92 : migration à appliquer manuellement après sauvegarde.
CREATE TABLE IF NOT EXISTS security_alert_purge_runs (
    id BIGSERIAL PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(32) NOT NULL CHECK (status IN ('completed','skipped_locked','failed')),
    dry_run BOOLEAN NOT NULL,
    deleted INTEGER NOT NULL DEFAULT 0 CHECK (deleted >= 0),
    eligible INTEGER NOT NULL DEFAULT 0 CHECK (eligible >= 0),
    batch_size INTEGER NOT NULL CHECK (batch_size BETWEEN 1 AND 1000),
    error_code VARCHAR(64)
);
CREATE INDEX IF NOT EXISTS ix_security_alert_purge_runs_started_at ON security_alert_purge_runs (started_at DESC);
