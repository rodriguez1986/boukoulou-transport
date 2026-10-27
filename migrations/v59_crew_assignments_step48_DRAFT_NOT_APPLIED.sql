-- BROUILLON NON APPLIQUÉ. Revue DBA, sauvegarde et migration contrôlée requises.
-- L'affectation est créée par une opération administrative serveur autorisée.
CREATE TABLE IF NOT EXISTS bt_crew_assignments_step48 (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    trip_id INTEGER NOT NULL REFERENCES trips(id),
    role VARCHAR(16) NOT NULL CHECK (role IN ('DRIVER','CONTROLLER')),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ,
    assigned_by_user_id INTEGER NOT NULL REFERENCES users(id),
    CHECK (ends_at IS NULL OR ends_at > starts_at)
);
CREATE INDEX IF NOT EXISTS idx_bt_crew_assignment_lookup_step48
ON bt_crew_assignments_step48 (user_id, trip_id, role, active);
-- Les chevauchements et l'unicité des affectations actives doivent être
-- arbitrés avant production (contrainte d'exclusion / verrouillage).
