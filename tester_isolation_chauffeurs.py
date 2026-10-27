# ============================================================
# BOUKOULOU TRANSPORT V5.9 - ETAPE 93
# TEST D'ISOLATION ENTRE DEUX CHAUFFEURS
#
# Objectif :
# Verifier qu'un chauffeur ne peut acceder qu'aux courses
# affectees a son compte utilisateur.
#
# Securite :
# - Aucune connexion a PostgreSQL.
# - Aucun utilisateur cree.
# - Aucune course modifiee.
# - Aucun changement de statut ou de kilometrage.
#
# Methode :
# Utilisation d'une session SQLAlchemy simulee.
# ============================================================

from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import HTTPException
from sqlalchemy.dialects import postgresql

from app.main import (
    filtrer_courses_utilisateur,
    verifier_acces_course,
)
from app.models import Driver, Trip


# ------------------------------------------------------------
# 1. Creer deux comptes chauffeurs fictifs
# ------------------------------------------------------------

chauffeur_a = SimpleNamespace(
    id=1001,
    role=SimpleNamespace(value="DRIVER"),
)

chauffeur_b = SimpleNamespace(
    id=1002,
    role=SimpleNamespace(value="DRIVER"),
)


# ------------------------------------------------------------
# 2. Verifier les conditions SQL generees
#
# Cette partie teste le filtre reel de l'application,
# sans executer la requete contre PostgreSQL.
# ------------------------------------------------------------

def verifier_filtre_chauffeur(utilisateur):
    """
    Construit la requete SQL du chauffeur et verifie
    qu'elle contient une restriction sur son user_id.
    """

    # Creer une session fictive.
    db = MagicMock()

    # Utiliser une vraie requete SQLAlchemy sans connexion.
    from sqlalchemy.orm import Session
    from sqlalchemy import create_engine

    # La construction de l'engine ne provoque aucune connexion.
    engine = create_engine(
        "postgresql+psycopg://unused:unused@localhost/unused"
    )

    with Session(engine) as session:

        requete = filtrer_courses_utilisateur(
            session.query(Trip),
            utilisateur,
            session,
        )

        # Compiler uniquement la requete.
        # Aucun SQL n'est execute.
        sql = str(
            requete.statement.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        )

        # Le filtre doit cibler le compte du chauffeur.
        assert "drivers.user_id" in sql, (
            "Le filtre sur drivers.user_id est absent."
        )

        assert str(utilisateur.id) in sql, (
            "L'identifiant du chauffeur est absent du filtre."
        )

        print(
            f"SUCCES : filtre SQL present pour "
            f"l'utilisateur {utilisateur.id}."
        )


# ------------------------------------------------------------
# 3. Executer les tests pour les deux chauffeurs
# ------------------------------------------------------------

verifier_filtre_chauffeur(chauffeur_a)
verifier_filtre_chauffeur(chauffeur_b)


# ============================================================
# 4. TEST DU REFUS HTTP 404
#
# Objectif :
# Tester la vraie fonction verifier_acces_course().
#
# La requete SQLAlchemy est construite normalement.
# Son execution est interceptee avant tout acces a la base.
#
# Aucune connexion PostgreSQL.
# Aucune modification des courses.
# ============================================================

from unittest.mock import patch
from sqlalchemy.orm import Query, Session
from sqlalchemy import create_engine

# Construire un moteur sans ouvrir de connexion.
moteur_test = create_engine(
    "postgresql+psycopg://unused:unused@localhost/unused"
)

# Utiliser une vraie session SQLAlchemy.
with Session(moteur_test) as session:

    # Intercepter directement Query.first().
    # C'est cette methode qu'appelle verifier_acces_course().
    with patch.object(Query, "first", return_value=None) as recherche_simulee:

        try:
            verifier_acces_course(
                session,
                chauffeur_b,
                trip_id=5001,
            )

        except HTTPException as erreur:

            # La course non accessible doit retourner HTTP 404.
            assert erreur.status_code == 404, (
                f"Code HTTP inattendu : {erreur.status_code}"
            )

            # Verifier que la recherche a bien ete effectuee.
            recherche_simulee.assert_called_once()

            print(
                "SUCCES : une recherche sans course autorisee "
                "retourne HTTP 404."
            )

        else:
            raise AssertionError(
                "ECHEC : une recherche sans resultat a ete acceptee."
            )

print("")
print("TESTS D'ISOLATION TERMINES.")