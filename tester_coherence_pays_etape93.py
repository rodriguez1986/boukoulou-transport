
# ============================================================
# BOUKOULOU TRANSPORT V5.9 - ETAPE 93.4.8.6
#
# TESTS DE COHERENCE GEOGRAPHIQUE DES COURSES
#
# Objectifs :
# 1. Refuser un vehicule appartenant a un autre pays.
# 2. Refuser un chauffeur appartenant a un autre pays.
# 3. Autoriser une affectation coherente.
# 4. Verifier qu'aucune course n'est creee apres un refus.
#
# Securite :
# - SQLite en memoire uniquement.
# - Aucune connexion a PostgreSQL.
# - Aucun changement des courses reelles.
# - Appel direct de la vraie fonction create_trip().
# ============================================================

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import create_engine, event, select, func
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

# Importer les vrais modeles de Boukoulou Transport.
from app.models import (
    Country,
    User,
    Line,
    Vehicle,
    Driver,
    Trip,
    Audit,
    Role,
)

# Importer la vraie fonction et le schema de creation.
from app.main import create_trip, TripIn


# ============================================================
# 1. CREATION DE LA BASE SQLITE EN MEMOIRE
# ============================================================

engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


# Activer les contraintes de cles etrangeres.
@event.listens_for(engine, "connect")
def activer_cles_etrangeres(connexion, enregistrement):
    connexion.execute("PRAGMA foreign_keys=ON")


# Creer uniquement les tables necessaires aux tests.
Country.metadata.create_all(
    engine,
    tables=[
        Country.__table__,
        User.__table__,
        Line.__table__,
        Vehicle.__table__,
        Driver.__table__,
        Trip.__table__,
        Audit.__table__,
    ],
)


# ============================================================
# 2. FONCTIONS DE VERIFICATION
# ============================================================

def nombre_courses(db):
    """Compter les courses de la base SQLite de test."""
    return db.scalar(select(func.count()).select_from(Trip))


def verifier_refus(db, description, donnees, administrateur):
    """
    Verifier que create_trip refuse une affectation
    avec HTTP 409 et ne cree aucune course.
    """

    avant = nombre_courses(db)

    try:
        create_trip(
            x=TripIn(**donnees),
            u=administrateur,
            db=db,
        )

    except HTTPException as erreur:
        assert erreur.status_code == 409, (
            f"{description} : HTTP {erreur.status_code} "
            "au lieu de HTTP 409"
        )

        apres = nombre_courses(db)

        assert apres == avant, (
            f"{description} : une course a ete creee "
            "malgre le refus"
        )

        print(f"SUCCES : {description} -> HTTP 409")
        print("SUCCES : aucune course ajoutee apres le refus.")

    else:
        raise AssertionError(
            f"{description} : la creation aurait du etre refusee"
        )


# ============================================================
# 3. CREATION DES DONNEES FICTIVES
# ============================================================

with Session(engine) as db:

    # Deux pays fictifs.
    pays_gabon = Country(
        id=9001,
        code="GA",
        name="Gabon Test",
        currency="XAF",
    )

    pays_congo = Country(
        id=9002,
        code="CG",
        name="Congo Test",
        currency="XAF",
    )

    # Administrateur fictif.
    administrateur = User(
        id=9001,
        username="admin.test.pays",
        password_hash="test_sans_connexion",
        role=Role.ADMIN,
        is_active=True,
        token_version=0,
    )

    # Ligne situee au Gabon.
    ligne_gabon = Line(
        id=9001,
        country_id=9001,
        code="LIGNE_GA_TEST",
        name="Ligne Gabon Test",
        fare=500,
    )

    # Vehicule affecte au Gabon.
    vehicule_gabon = Vehicle(
        id=9001,
        country_id=9001,
        code="BUS_GA_TEST",
        plate="GA-TEST-001",
        capacity=30,
        standing_capacity=10,
        status="ACTIVE",
    )

    # Vehicule affecte au Congo.
    vehicule_congo = Vehicle(
        id=9002,
        country_id=9002,
        code="BUS_CG_TEST",
        plate="CG-TEST-001",
        capacity=30,
        standing_capacity=10,
        status="ACTIVE",
    )

    # Chauffeur affecte au Gabon.
    chauffeur_gabon = Driver(
        id=9001,
        country_id=9001,
        employee_code="DRV_GA_TEST",
        first_name="Jean",
        last_name="Gabon",
        license_number="LIC_GA_TEST",
        status="ACTIVE",
    )

    # Chauffeur affecte au Congo.
    chauffeur_congo = Driver(
        id=9002,
        country_id=9002,
        employee_code="DRV_CG_TEST",
        first_name="Paul",
        last_name="Congo",
        license_number="LIC_CG_TEST",
        status="ACTIVE",
    )

    # Enregistrer uniquement dans SQLite.
    db.add_all([
        pays_gabon,
        pays_congo,
        administrateur,
        ligne_gabon,
        vehicule_gabon,
        vehicule_congo,
        chauffeur_gabon,
        chauffeur_congo,
    ])

    db.commit()

    # Date fictive utilisee pour tous les scenarios.
    depart = datetime(2030, 1, 1, 8, 0, tzinfo=timezone.utc)

    # ========================================================
    # TEST 1 : VEHICULE D'UN AUTRE PAYS
    # ========================================================

    verifier_refus(
        db,
        "Vehicule Congo sur ligne Gabon refuse",
        {
            "line_id": 9001,
            "vehicle_id": 9002,
            "driver_id": 9001,
            "departure_at": depart,
            "notes": "TEST REFUS VEHICULE",
        },
        administrateur,
    )

    # ========================================================
    # TEST 2 : CHAUFFEUR D'UN AUTRE PAYS
    # ========================================================

    verifier_refus(
        db,
        "Chauffeur Congo sur ligne Gabon refuse",
        {
            "line_id": 9001,
            "vehicle_id": 9001,
            "driver_id": 9002,
            "departure_at": depart,
            "notes": "TEST REFUS CHAUFFEUR",
        },
        administrateur,
    )

    # ========================================================
    # TEST 3 : AFFECTATION CORRECTE
    # ========================================================

    avant = nombre_courses(db)

    course = create_trip(
        x=TripIn(
            line_id=9001,
            vehicle_id=9001,
            driver_id=9001,
            departure_at=depart,
            notes="TEST AFFECTATION CORRECTE",
        ),
        u=administrateur,
        db=db,
    )

    assert course.id is not None
    assert course.status == "SCHEDULED"
    assert nombre_courses(db) == avant + 1

    print("SUCCES : affectation du meme pays autorisee.")

    # ========================================================
    # TEST 4 : VERIFIER LA TRACE D'AUDIT
    # ========================================================

    trace = db.scalar(
        select(Audit).where(
            Audit.username == administrateur.username,
            Audit.action == "CREATE_TRIP",
            Audit.target == str(course.id),
        )
    )

    assert trace is not None, (
        "La creation autorisee n'a pas produit de trace d'audit"
    )

    print("SUCCES : trace d'audit enregistree dans SQLite.")

print()
print("TOUS LES TESTS DE COHERENCE GEOGRAPHIQUE SONT REUSSIS.")
