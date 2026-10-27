
# ============================================================
# BOUKOULOU TRANSPORT V5.9 - ETAPE 93.4.9.5
#
# TEST DES ROTATIONS ALLER / RETOUR
#
# Exemple :
#   Course 1 : Mfilou -> Total
#   Course 2 : Total -> Mfilou
#
# Objectifs :
# - Interdire deux courses simultanees pour un meme bus.
# - Interdire deux courses simultanees pour un chauffeur.
# - Autoriser le retour apres la fin de l'aller.
# - Verifier la transmission du kilometrage.
#
# SECURITE :
# Base SQLite en memoire uniquement.
# Aucune modification de PostgreSQL.
# ============================================================

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

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

from app.schemas import TripStartIn, TripCompleteIn

from app.main import start_trip, complete_trip


# ============================================================
# 1. BASE TEMPORAIRE SQLITE
# ============================================================

engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def activer_cles_etrangeres(connexion, enregistrement):
    connexion.execute("PRAGMA foreign_keys=ON")


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
# 2. DONNEES FICTIVES
# ============================================================

with Session(engine, expire_on_commit=False) as db:

    pays = Country(
        id=9001,
        code="CG",
        name="Congo",
        currency="XAF",
    )

    admin = User(
        id=9001,
        username="admin.test.rotations",
        password_hash="test-non-utilise",
        role=Role.ADMIN,
        is_active=True,
        country_id=9001,
    )

    ligne_aller = Line(
        id=9001,
        country_id=9001,
        code="TEST-MFILOU-TOTAL",
        name="Mfilou - Total",
        fare=200,
    )

    ligne_retour = Line(
        id=9002,
        country_id=9001,
        code="TEST-TOTAL-MFILOU",
        name="Total - Mfilou",
        fare=200,
    )

    bus_a = Vehicle(
        id=9001,
        country_id=9001,
        code="BUS-ROTATION-A",
        plate="TEST-ROT-001",
        capacity=30,
        standing_capacity=10,
        status="ACTIVE",
        mileage=10000,
    )

    bus_b = Vehicle(
        id=9002,
        country_id=9001,
        code="BUS-ROTATION-B",
        plate="TEST-ROT-002",
        capacity=30,
        standing_capacity=10,
        status="ACTIVE",
        mileage=20000,
    )

    chauffeur = Driver(
        id=9001,
        country_id=9001,
        employee_code="CHAUFFEUR-ROT-001",
        first_name="Jean",
        last_name="Test",
        license_number="PERMIS-ROT-001",
        status="ACTIVE",
    )

    # Le depart est prevu dans le passe recent pour eviter
    # le refus lie a un depart trop anticipe.
    depart_prevu = datetime.now(timezone.utc) - timedelta(minutes=5)

    aller = Trip(
        id=9001,
        line_id=9001,
        vehicle_id=9001,
        driver_id=9001,
        departure_at=depart_prevu,
        status="SCHEDULED",
    )

    retour = Trip(
        id=9002,
        line_id=9002,
        vehicle_id=9001,
        driver_id=9001,
        departure_at=depart_prevu,
        status="SCHEDULED",
    )

    autre_course = Trip(
        id=9003,
        line_id=9002,
        vehicle_id=9002,
        driver_id=9001,
        departure_at=depart_prevu,
        status="SCHEDULED",
    )

    db.add_all([
        pays,
        admin,
        ligne_aller,
        ligne_retour,
        bus_a,
        bus_b,
        chauffeur,
        aller,
        retour,
        autre_course,
    ])

    db.commit()

    # ========================================================
    # 3. DEMARRAGE DE L'ALLER
    # ========================================================

    resultat = start_trip(
        trip_id=9001,
        x=TripStartIn(start_mileage=10000),
        u=admin,
        db=db,
    )

    assert resultat["status"] == "IN_PROGRESS"

    print("SUCCES : Mfilou -> Total a demarre.")

    # ========================================================
    # 4. REFUS DU RETOUR : MEME BUS OCCUPE
    # ========================================================

    try:
        start_trip(
            trip_id=9002,
            x=TripStartIn(start_mileage=10000),
            u=admin,
            db=db,
        )

    except HTTPException as erreur:
        assert erreur.status_code == 409
        assert "vehicule" in str(erreur.detail).lower() or \
               "hicule" in str(erreur.detail).lower()

        print(
            "SUCCES : retour refuse car le bus A est occupe."
        )

    else:
        raise AssertionError(
            "ERREUR : le bus A a demarre deux courses."
        )

    assert db.get(Trip, 9002).status == "SCHEDULED"

    # ========================================================
    # 5. REFUS : MEME CHAUFFEUR SUR UN AUTRE BUS
    # ========================================================

    try:
        start_trip(
            trip_id=9003,
            x=TripStartIn(start_mileage=20000),
            u=admin,
            db=db,
        )

    except HTTPException as erreur:
        assert erreur.status_code == 409

        print(
            "SUCCES : chauffeur occupe sur une autre course."
        )

    else:
        raise AssertionError(
            "ERREUR : le chauffeur conduit deux bus."
        )

    assert db.get(Trip, 9003).status == "SCHEDULED"

    # ========================================================
    # 6. TERMINER L'ALLER
    # ========================================================

    resultat = complete_trip(
        trip_id=9001,
        x=TripCompleteIn(end_mileage=10012),
        u=admin,
        db=db,
    )

    assert resultat["status"] == "COMPLETED"
    assert db.get(Vehicle, 9001).mileage == 10012

    print(
        "SUCCES : aller termine, compteur du bus = 10012 km."
    )

    # ========================================================
    # 7. DEMARRER LE RETOUR AVEC LE MEME BUS
    # ========================================================

    resultat = start_trip(
        trip_id=9002,
        x=TripStartIn(start_mileage=10012),
        u=admin,
        db=db,
    )

    assert resultat["status"] == "IN_PROGRESS"

    print(
        "SUCCES : retour Total -> Mfilou autorise."
    )

    # ========================================================
    # 8. VERIFIER LE KILOMETRAGE DU RETOUR
    # ========================================================

    resultat = complete_trip(
        trip_id=9002,
        x=TripCompleteIn(end_mileage=10024),
        u=admin,
        db=db,
    )

    assert resultat["status"] == "COMPLETED"
    assert db.get(Vehicle, 9001).mileage == 10024

    print(
        "SUCCES : retour termine, compteur du bus = 10024 km."
    )

    # ========================================================
    # 9. VERIFIER LES STATUTS ET LES AUDITS
    # ========================================================

    assert db.get(Trip, 9001).status == "COMPLETED"
    assert db.get(Trip, 9002).status == "COMPLETED"

    audits = db.query(Audit).all()

    assert len(audits) >= 4

    print("SUCCES : statuts et audits verifies.")

    print()
    print(
        "TOUS LES TESTS DE ROTATION ALLER-RETOUR SONT REUSSIS."
    )
