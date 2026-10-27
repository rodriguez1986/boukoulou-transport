"""Étape 42 : écriture SQL transactionnelle *préparatoire* du journal.

Nécessite une connexion DB-API PostgreSQL fournie par l'appelant, avec
transactions manuelles (autocommit=False). Le SQL de l'étape 41 est requis.
Aucune connexion créée, aucune migration exécutée et aucun PSP appelé.
"""
from app.payment_audit_storage_step41 import preparer_lignes_audit


class EcritureAuditRefusee(ValueError):
    pass


class ConfigurationTransactionInvalide(RuntimeError):
    pass


def _connexion_verifiee(conn):
    if conn is None or not callable(getattr(conn, 'cursor', None)):
        raise ConfigurationTransactionInvalide('Connexion DB-API requise')
    if getattr(conn, 'autocommit', None) is not False:
        raise ConfigurationTransactionInvalide('autocommit=False obligatoire')
    if not callable(getattr(conn, 'commit', None)) or not callable(getattr(conn, 'rollback', None)):
        raise ConfigurationTransactionInvalide('commit et rollback obligatoires')


def enregistrer_journal_initial(conn, journal):
    """Écrit un journal initial en une transaction, si migration déjà approuvée.

    L'unicité de reference_billet et (stream_id, sequence) est garantie
    par PostgreSQL, pas par un contrôle préalable sujet aux courses.
    Toute erreur SQL est remontée après rollback ; aucune exception masquée.
    """
    _connexion_verifiee(conn)
    donnees = preparer_lignes_audit(journal)
    if not donnees['pret_pour_revue'] or len(donnees['lignes']) != 1:
        raise EcritureAuditRefusee('Journal initial invalide ou déjà transitionné')
    f = donnees['flux']; l = donnees['lignes'][0]
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO bt_payment_audit_stream_step41
            (reference_billet, pays, canal, moyen, montant_xaf, statut,
             derniere_sequence, derniere_empreinte)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING stream_id''',
            (f['reference_billet'], f['pays'], f['canal'], f['moyen'],
             f['montant_xaf'], f['statut'], f['derniere_sequence'],
             f['derniere_empreinte']))
        stream_id = cursor.fetchone()[0]
        cursor.execute('''INSERT INTO bt_payment_audit_entry_step41
            (stream_id, sequence, action, acteur, statut,
             reference_confirmation, empreinte_precedente, empreinte)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
            (stream_id, l['sequence'], l['action'], l['acteur'], l['statut'],
             l['reference_confirmation'], l['empreinte_precedente'], l['empreinte']))
        conn.commit()
        return {'enregistre': True, 'stream_id': stream_id, 'sequence': 1,
                'paiement_reel_confirme': False, 'billet_emis': False}
    except Exception:
        conn.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()


def enregistrer_transition(conn, journal):
    """Verrouille le flux, vérifie l'état précédent et écrit une transition.

    Requiert un journal complet de 2 entrées. Les erreurs de concurrence
    entraînent un rollback. Le code appelant doit gérer l'authentification.
    """
    _connexion_verifiee(conn)
    donnees = preparer_lignes_audit(journal)
    if not donnees['pret_pour_revue'] or len(donnees['lignes']) != 2:
        raise EcritureAuditRefusee('Journal de transition invalide')
    f = donnees['flux']; initiale, suivante = donnees['lignes']
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute('''SELECT stream_id, pays, canal, moyen, montant_xaf,
               statut, derniere_sequence, derniere_empreinte
            FROM bt_payment_audit_stream_step41
            WHERE reference_billet = %s FOR UPDATE''', (f['reference_billet'],))
        existant = cursor.fetchone()
        if existant is None:
            raise EcritureAuditRefusee('Flux inexistant')
        sid, pays, canal, moyen, montant, statut, sequence, empreinte = existant
        if (pays, canal, moyen, montant, statut, sequence, empreinte) != (
                f['pays'], f['canal'], f['moyen'], f['montant_xaf'],
                initiale['statut'], initiale['sequence'], initiale['empreinte']):
            raise EcritureAuditRefusee('Conflit de concurrence ou flux divergent')
        cursor.execute('''INSERT INTO bt_payment_audit_entry_step41
            (stream_id, sequence, action, acteur, statut,
             reference_confirmation, empreinte_precedente, empreinte)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
            (sid, suivante['sequence'], suivante['action'], suivante['acteur'],
             suivante['statut'], suivante['reference_confirmation'],
             suivante['empreinte_precedente'], suivante['empreinte']))
        cursor.execute('''UPDATE bt_payment_audit_stream_step41
            SET statut = %s, derniere_sequence = %s, derniere_empreinte = %s
            WHERE stream_id = %s''',
            (suivante['statut'], suivante['sequence'], suivante['empreinte'], sid))
        conn.commit()
        return {'enregistre': True, 'stream_id': sid, 'sequence': 2,
                'paiement_reel_confirme': False, 'billet_emis': False}
    except Exception:
        conn.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
