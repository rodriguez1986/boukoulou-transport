-- V5.9 : tables nouvelles, sans suppression ni modification des billets existants.
-- Exécuter APRÈS sauvegarde et AVANT redémarrage de l'API.
CREATE TABLE IF NOT EXISTS v59_stocks (
 id SERIAL PRIMARY KEY, country_id INTEGER NOT NULL REFERENCES countries(id),
 fare INTEGER NOT NULL CHECK (fare>0), created INTEGER NOT NULL,
 available INTEGER NOT NULL, admin_id INTEGER NOT NULL REFERENCES users(id),
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 CONSTRAINT ck_v59_stock CHECK(created>=0 AND available>=0 AND available<=created));
CREATE TABLE IF NOT EXISTS v59_passes (
 id SERIAL PRIMARY KEY, code VARCHAR(80) UNIQUE NOT NULL,
 stock_id INTEGER NOT NULL REFERENCES v59_stocks(id), country_id INTEGER NOT NULL REFERENCES countries(id),
 fare INTEGER NOT NULL, quantity INTEGER NOT NULL, remaining INTEGER NOT NULL,
 total INTEGER NOT NULL, agent_id INTEGER NOT NULL REFERENCES users(id),
 cash_session_id INTEGER NOT NULL REFERENCES cash_sessions(id),
 reference VARCHAR(100) UNIQUE NOT NULL, provider VARCHAR(40) NOT NULL,
 sold_at TIMESTAMPTZ NOT NULL, valid_until TIMESTAMPTZ NOT NULL,
 CONSTRAINT ck_v59_remaining CHECK(remaining>=0 AND remaining<=quantity));
CREATE TABLE IF NOT EXISTS v59_boardings (
 id SERIAL PRIMARY KEY, pass_id INTEGER NOT NULL REFERENCES v59_passes(id),
 trip_id INTEGER NOT NULL REFERENCES trips(id), controller_id INTEGER NOT NULL REFERENCES users(id),
 boarded_at TIMESTAMPTZ NOT NULL, remaining_after INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS ix_v59_boardings_trip ON v59_boardings(trip_id);
