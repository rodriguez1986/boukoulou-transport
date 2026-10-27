-- ETAPE 41 : BROUILLON, NE PAS APPLIQUER SANS REVUE ET TESTS POSTGRESQL
-- Tables autonomes de préparation : aucun lien FK avec schéma V5.9 existant.
-- Adapter noms, identité authentifiée, autorisations et modèle de transaction.
BEGIN;

CREATE TABLE IF NOT EXISTS bt_payment_audit_stream_step41 (
    stream_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reference_billet TEXT NOT NULL UNIQUE CHECK (length(btrim(reference_billet)) > 0),
    pays VARCHAR(2) NOT NULL CHECK (pays IN ('CG','GA')),
    canal VARCHAR(8) NOT NULL CHECK (canal IN ('AGENCE','BUS','EN_LIGNE')),
    moyen VARCHAR(16) NOT NULL CHECK (moyen IN ('ESPECES','AIRTEL_MONEY','MTN_MOMO','MOOV_MONEY')),
    montant_xaf BIGINT NOT NULL CHECK (montant_xaf > 0),
    statut VARCHAR(16) NOT NULL CHECK (statut IN ('EN_ATTENTE','CONFIRME','ECHOUE','ANNULE')),
    derniere_sequence INTEGER NOT NULL DEFAULT 0 CHECK (derniere_sequence >= 0),
    derniere_empreinte CHAR(64) NOT NULL DEFAULT '',
    cree_le TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (
      (canal IN ('AGENCE','BUS') AND moyen = 'ESPECES')
      OR (pays = 'CG' AND canal = 'EN_LIGNE' AND moyen IN ('AIRTEL_MONEY','MTN_MOMO'))
      OR (pays = 'GA' AND canal = 'EN_LIGNE' AND moyen IN ('AIRTEL_MONEY','MOOV_MONEY'))
    )
);

CREATE TABLE IF NOT EXISTS bt_payment_audit_entry_step41 (
    stream_id BIGINT NOT NULL REFERENCES bt_payment_audit_stream_step41(stream_id),
    sequence INTEGER NOT NULL CHECK (sequence > 0),
    action TEXT NOT NULL,
    acteur TEXT NOT NULL,
    statut VARCHAR(16) NOT NULL CHECK (statut IN ('EN_ATTENTE','CONFIRME','ECHOUE','ANNULE')),
    reference_confirmation TEXT NOT NULL DEFAULT '',
    empreinte_precedente TEXT NOT NULL,
    empreinte CHAR(64) NOT NULL,
    cree_le TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (stream_id, sequence)
);

-- Plan d'écriture : BEGIN; SELECT stream FOR UPDATE; vérifier sequence + empreinte;
-- INSERT entry; UPDATE stream; COMMIT. Pas de déclencheur/route API à cette étape.
-- La transaction applicative et les permissions SQL doivent encore être implémentées.
COMMIT;
