-- Migration de RECONSTRUCTION : ne pas exécuter sans sauvegarde et validation du schéma.
-- Création additive : aucune table existante supprimée.
CREATE TABLE IF NOT EXISTS cash_session_rectifications (
    id SERIAL PRIMARY KEY,
    cash_session_id INTEGER NOT NULL REFERENCES cash_sessions(id),
    admin_user_id INTEGER NOT NULL REFERENCES users(id),
    old_declared_amount INTEGER NOT NULL,
    new_declared_amount INTEGER NOT NULL,
    old_difference_amount INTEGER NOT NULL,
    new_difference_amount INTEGER NOT NULL,
    reason VARCHAR(500) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
