# ============================================================
# BOUKOULOU TRANSPORT V5.9 - ETAPE 93
# INSPECTION DES MODELES POUR LES TESTS D'ISOLATION
#
# Objectif :
# Afficher les champs obligatoires, valeurs par defaut
# et relations des cinq modeles utilises par les courses.
#
# Securite :
# - Aucune connexion a PostgreSQL.
# - Aucune modification des donnees.
# ============================================================

from sqlalchemy import inspect
from app.models import User, Driver, Trip, Line, Vehicle

# Modeles necessaires au test.
modeles = [User, Driver, Line, Vehicle, Trip]

for modele in modeles:

    print("\n" + "=" * 60)
    print("MODELE :", modele.__name__)
    print("=" * 60)

    # Inspecter les colonnes SQLAlchemy.
    for colonne in inspect(modele).columns:

        # Une colonne est obligatoire si elle n'accepte pas NULL,
        # n'est pas une cle primaire et n'a pas de valeur par defaut.
        obligatoire = (
            not colonne.nullable
            and not colonne.primary_key
            and colonne.default is None
            and colonne.server_default is None
        )

        print(
            f"{colonne.name:25} "
            f"type={str(colonne.type):20} "
            f"obligatoire={obligatoire}"
        )

    # Afficher les relations avec les autres tables.
    print("\nCLES ETRANGERES :")

    for cle in inspect(modele).persist_selectable.foreign_keys:
        print(" -", cle)