-- BROUILLON : NE PAS EXÉCUTER avant revue du schéma et du PSP.
-- Dépend de la migration NON APPLIQUÉE de l’étape 31.
-- L’unicité est durable par prestataire + identifiant d’événement.
CREATE TABLE refund_provider_events (
    id BIGSERIAL PRIMARY KEY,
    refund_request_id BIGINT NOT NULL REFERENCES refund_requests(id),
    provider VARCHAR(80) NOT NULL CHECK (length(trim(provider)) > 0),
    provider_event_id VARCHAR(180) NOT NULL CHECK (length(trim(provider_event_id)) > 0),
    provider_refund_id VARCHAR(180) NOT NULL,
    external_status VARCHAR(24) NOT NULL CHECK (external_status IN ('CONFIRMED', 'FAILED')),
    amount BIGINT NOT NULL CHECK (amount > 0),
    currency CHAR(3) NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
    payload_sha256 CHAR(64) NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_refund_provider_event UNIQUE (provider, provider_event_id)
);
CREATE INDEX ix_refund_provider_events_request ON refund_provider_events(refund_request_id);
-- La transaction future doit authentifier la signature PSP sur les octets bruts,
-- insérer l'événement (ON CONFLICT ne doit jamais écraser un conflit),
-- vérifier les correspondances montant/devise/remboursement,
-- verrouiller le remboursement, appliquer la transition et auditer atomiquement.
-- Ne pas utiliser ce brouillon tel quel pour traiter des webhooks réels.
