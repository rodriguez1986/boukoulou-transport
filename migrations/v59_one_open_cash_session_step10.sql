-- Boukoulou Transport V5.9 - Étape 10
-- À EXAMINER ET SAUVEGARDER AVANT EXÉCUTION ; NON APPLIQUÉE.
-- PostgreSQL uniquement. Ne supprime aucune donnée.
--
-- Précontrôle indispensable : cette requête ne doit retourner AUCUNE ligne :
-- SELECT user_id, count(*) AS caisses_ouvertes
-- FROM cash_sessions WHERE status = 'OPEN'
-- GROUP BY user_id HAVING count(*) > 1;
--
-- Si des doublons existent, les examiner et les résoudre manuellement
-- selon la comptabilité avant toute migration.
--
-- Exécuter hors d'une transaction explicite si CREATE INDEX CONCURRENTLY
-- est utilisé. Cette commande échoue sans modifier les lignes si des doublons
-- existent, et peut laisser un index INVALID à nettoyer manuellement.
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS
    ux_cash_sessions_one_open_per_user
ON cash_sessions (user_id)
WHERE status = 'OPEN';
--
-- Vérification après création :
-- SELECT indexname, indexdef FROM pg_indexes
-- WHERE tablename = 'cash_sessions'
-- AND indexname = 'ux_cash_sessions_one_open_per_user';
--
-- Vérifier également pg_index.indisvalid (un index peut exister sans être valide).
