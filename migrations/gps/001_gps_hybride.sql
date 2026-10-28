-- Boukoulou Transport V5.9
-- Migration GPS hybride V1
-- Création uniquement : aucune suppression de données

BEGIN;

CREATE TABLE IF NOT EXISTS gps_devices (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
    device_uid VARCHAR(120) NOT NULL UNIQUE,
    device_name VARCHAR(150),
    token_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gps_devices_vehicle
ON gps_devices(vehicle_id);

CREATE TABLE IF NOT EXISTS gps_hybrid_positions (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
    device_id BIGINT REFERENCES gps_devices(id),
    source VARCHAR(10) NOT NULL
        CHECK (source IN ('PHONE', 'DEVICE')),
    latitude DOUBLE PRECISION NOT NULL
        CHECK (latitude BETWEEN -90 AND 90),
    longitude DOUBLE PRECISION NOT NULL
        CHECK (longitude BETWEEN -180 AND 180),
    speed DOUBLE PRECISION NOT NULL DEFAULT 0
        CHECK (speed >= 0),
    recorded_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT gps_device_source_check CHECK (
        (source = 'PHONE' AND device_id IS NULL)
        OR
        (source = 'DEVICE' AND device_id IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_gps_hybrid_vehicle_source_time
ON gps_hybrid_positions(vehicle_id, source, recorded_at DESC);

COMMIT;
