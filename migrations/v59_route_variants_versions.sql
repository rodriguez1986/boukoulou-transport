-- Boukoulou Transport V5.9
-- Etape 56.30.75
-- Migration additive : parcours versionnes
-- NE PAS EXECUTER AVANT VALIDATION

BEGIN;

-- Necessaire pour l'exclusion des plages temporelles
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- 1. Variantes de parcours
CREATE TABLE route_variants (
    id SERIAL PRIMARY KEY,
    line_id INTEGER NOT NULL REFERENCES lines(id),
    city_id INTEGER NOT NULL,
    direction VARCHAR(10) NOT NULL,
    name VARCHAR(160),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_route_variants_direction
        CHECK (direction IN ('ALLER', 'RETOUR')),

    CONSTRAINT fk_route_variants_line_city
        FOREIGN KEY (line_id, city_id)
        REFERENCES lines(id, city_id),

    CONSTRAINT uq_route_variants_line_direction
        UNIQUE (line_id, direction),

    CONSTRAINT uq_route_variants_id_line
        UNIQUE (id, line_id),

    CONSTRAINT uq_route_variants_id_city
        UNIQUE (id, city_id)
);

-- 2. Versions de parcours
CREATE TABLE route_versions (
    id SERIAL PRIMARY KEY,

    route_variant_id INTEGER NOT NULL
        REFERENCES route_variants(id),

    line_id INTEGER NOT NULL,
    city_id INTEGER NOT NULL,

    version_number INTEGER NOT NULL,

    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',

    valid_from TIMESTAMPTZ,
    valid_to TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_route_versions_variant_line
        FOREIGN KEY (route_variant_id, line_id)
        REFERENCES route_variants(id, line_id),

    CONSTRAINT fk_route_versions_variant_city
        FOREIGN KEY (route_variant_id, city_id)
        REFERENCES route_variants(id, city_id),

    CONSTRAINT ck_route_versions_number
        CHECK (version_number > 0),

    CONSTRAINT ck_route_versions_status
        CHECK (status IN ('DRAFT', 'ACTIVE', 'ARCHIVED')),

    CONSTRAINT ck_route_versions_dates
        CHECK (
            valid_to IS NULL
            OR (
                valid_from IS NOT NULL
                AND valid_to > valid_from
            )
        ),

    CONSTRAINT ck_route_versions_active_start
        CHECK (
            status <> 'ACTIVE'
            OR valid_from IS NOT NULL
        ),

    CONSTRAINT uq_route_versions_number
        UNIQUE (route_variant_id, version_number),

    CONSTRAINT uq_route_versions_id_line
        UNIQUE (id, line_id),

    CONSTRAINT uq_route_versions_id_city
        UNIQUE (id, city_id)
);

-- Interdire le chevauchement des versions actives
ALTER TABLE route_versions
ADD CONSTRAINT ex_route_versions_active_period
EXCLUDE USING gist (
    route_variant_id WITH =,
    tstzrange(valid_from, valid_to, '[)') WITH &&
)
WHERE (status = 'ACTIVE');

-- 3. Arrets de chaque version
CREATE TABLE route_version_stops (
    id SERIAL PRIMARY KEY,

    route_version_id INTEGER NOT NULL,
    city_id INTEGER NOT NULL,
    stop_id INTEGER NOT NULL,
    stop_order INTEGER NOT NULL,

    CONSTRAINT fk_route_version_stops_version_city
        FOREIGN KEY (route_version_id, city_id)
        REFERENCES route_versions(id, city_id),

    CONSTRAINT fk_route_version_stops_stop_city
        FOREIGN KEY (stop_id, city_id)
        REFERENCES stops(id, city_id),

    CONSTRAINT ck_route_version_stops_order
        CHECK (stop_order > 0),

    CONSTRAINT uq_route_version_stops_order
        UNIQUE (route_version_id, stop_order),

    CONSTRAINT uq_route_version_stops_stop
        UNIQUE (route_version_id, stop_id)
);

-- 4. Voyages : reference facultative a la version
ALTER TABLE trips
    ADD COLUMN route_version_id INTEGER;

ALTER TABLE trips
    ADD CONSTRAINT fk_trips_route_version_line
    FOREIGN KEY (route_version_id, line_id)
    REFERENCES route_versions(id, line_id);

-- 5. Index
CREATE INDEX idx_route_variants_line
    ON route_variants(line_id);

CREATE INDEX idx_route_versions_variant_status
    ON route_versions(route_variant_id, status);

CREATE INDEX idx_route_version_stops_version_order
    ON route_version_stops(route_version_id, stop_order);

CREATE INDEX idx_trips_route_version
    ON trips(route_version_id);

COMMIT;