-- PROJET DE MIGRATION SEULEMENT : NE PAS EXECUTER EN PRODUCTION.
-- Validation préalable : schéma payments, politique des devises, rôles, PSP.
-- Le registre n'implémente aucun remboursement ni aucun déclencheur de débit.
CREATE TABLE IF NOT EXISTS refund_requests (
    id BIGSERIAL PRIMARY KEY,
    payment_id INTEGER NOT NULL REFERENCES payments(id),
    idempotency_key VARCHAR(120) NOT NULL,
    amount BIGINT NOT NULL CHECK (amount > 0),
    status VARCHAR(24) NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'PROCESSING', 'CONFIRMED', 'FAILED', 'CANCELLED')),
    requested_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    provider_ref VARCHAR(180),
    CONSTRAINT uq_refund_payment_idempotency UNIQUE (payment_id, idempotency_key)
);
CREATE INDEX IF NOT EXISTS ix_refund_requests_payment_id ON refund_requests(payment_id);
-- IMPORTANT : une contrainte UNIQUE seule ne garantit PAS le plafond cumulé.
-- La future API devra verrouiller SELECT ... FROM payments WHERE id = ? FOR UPDATE,
-- puis calculer les montants PENDING/PROCESSING/CONFIRMED dans la même transaction.
-- La finalisation PSP et l'audit durable doivent être conçus séparément.
