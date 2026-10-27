-- BROUILLON : NE PAS APPLIQUER AUTOMATIQUEMENT.
-- Requiert la migration étape 48 et une revue DBA.
CREATE TABLE IF NOT EXISTS bt_crew_assignment_audit_step49 (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    assignment_id BIGINT NOT NULL REFERENCES bt_crew_assignments_step48(id),
    actor_id INTEGER NOT NULL REFERENCES users(id),
    target_user_id INTEGER NOT NULL REFERENCES users(id),
    trip_id INTEGER NOT NULL REFERENCES trips(id),
    action VARCHAR(16) NOT NULL CHECK (action IN ('ATTRIBUER','RETIRER')),
    role VARCHAR(16) NOT NULL CHECK (role IN ('DRIVER','CONTROLLER')),
    happened_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_crew_audit_assignment_step49
ON bt_crew_assignment_audit_step49 (assignment_id, id);
-- Recommandation : audit append-only via privilèges DB séparés et politique de rétention.
-- Le service verrouille Trip sous PostgreSQL, mais d'autres chemins d'écriture
-- pourraient contourner cette protection : ajouter des contraintes DB après revue.
