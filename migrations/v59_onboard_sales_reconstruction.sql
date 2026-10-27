-- RECONSTITUTION : exécuter UNIQUEMENT après vérification du schéma réel.
-- Ne supprime ni ne modifie les tables existantes.
-- Ne pas appliquer sur une base existante avant sauvegarde et comparaison.
CREATE TABLE IF NOT EXISTS v59_onboard_sales (
    id SERIAL PRIMARY KEY,
    pass_id INTEGER NOT NULL REFERENCES v59_passes(id),
    trip_id INTEGER NOT NULL REFERENCES trips(id),
    controller_id INTEGER NOT NULL REFERENCES users(id),
    cash_session_id INTEGER NOT NULL REFERENCES cash_sessions(id),
    total_amount INTEGER NOT NULL CHECK (total_amount >= 0),
    sold_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_v59_onboard_pass UNIQUE (pass_id)
);
