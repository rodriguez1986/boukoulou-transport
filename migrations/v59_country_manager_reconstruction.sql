-- MIGRATION PROPOSÉE, NON EXÉCUTÉE. À vérifier sur une COPIE de la base PostgreSQL.
-- Le type 'role' est supposé être l'enum SQLAlchemy historique.
ALTER TYPE role ADD VALUE IF NOT EXISTS 'COUNTRY_MANAGER';
ALTER TABLE users ADD COLUMN IF NOT EXISTS country_id INTEGER NULL;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_users_country_id_reconstruction') THEN
    ALTER TABLE users ADD CONSTRAINT fk_users_country_id_reconstruction
      FOREIGN KEY (country_id) REFERENCES countries(id);
  END IF;
END $$;
-- Aucun utilisateur n'est modifié ou créé par cette migration.
