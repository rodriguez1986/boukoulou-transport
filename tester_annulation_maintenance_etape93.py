
# ============================================================
# BOUKOULOU TRANSPORT V5.9 - ETAPE 93.4.9.7.50
#
# TESTS ANNULATION ET MAINTENANCE
#
# Base SQLite en memoire uniquement.
# Aucune connexion volontaire a PostgreSQL.
# Executer dans le conteneur Docker isole, sans reseau.
# ============================================================

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.models import (
    Country, User, Line, Vehicle, Driver,
    Trip, Maintenance, Audit, Role
)
from app.schemas import (
    TripCancelIn, MaintenanceIn, MaintenanceUpdate,
    TripStartIn
)
from app.main import (
    cancel_trip, create_maintenance,
    update_maintenance, start_trip
)


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
        Maintenance.__table__,
        Audit.__table__,
    ],
)


def verifier_refus_409(operation, description):
    try:
        operation()
    except HTTPException as erreur:
        assert erreur.status_code == 409, (
            f"{description} : HTTP {erreur.status_code}"
        )
        print(f"SUCCES : {description} -> HTTP 409")
    else:
        raise AssertionError(
            f"{description} : refus HTTP 409 attendu"
        )


with Session(engine, expire_on_commit=False) as db:

    # --------------------------------------------------------
    # 1. Donnees fictives
    # --------------------------------------------------------

    pays = Country(
        id=9301,
        code="CG",
        name="Congo",
        currency="XAF",
    )

    admin = User(
        id=9301,
        username="admin.test.maintenance",
        password_hash="test-non-utilise",
        role=Role.ADMIN,
        is_active=True,
        country_id=9301,
    )

    ligne = Line(
        id=9301,
        country_id=9301,
        code="TEST-MAINTENANCE",
        name="Ligne de test maintenance",
        fare=200,
    )

    bus = Vehicle(
        id=9301,
        country_id=9301,
        code="BUS-MAINT-TEST",
        plate="TEST-MAINT-001",
        capacity=30,
        standing_capacity=10,
        status="ACTIVE",
        mileage=10000,
    )

    chauffeur = Driver(
        id=9301,
        country_id=9301,
        employee_code="CHAUFFEUR-MAINT-001",
        first_name="Jean",
        last_name="Test",
        license_number="PERMIS-MAINT-001",
        status="ACTIVE",
    )

    depart = datetime.now(timezone.utc) - timedelta(minutes=5)

    courses = [
        Trip(
            id=9301 + i,
            line_id=9301,
            vehicle_id=9301,
            driver_id=9301,
            departure_at=depart,
            status="SCHEDULED",
        )
        for i in range(4)
    ]

    db.add_all([pays, admin, ligne, bus, chauffeur, *courses])
    db.commit()

    # --------------------------------------------------------
    # 2. Annulation d'une course planifiee
    # --------------------------------------------------------

    resultat = cancel_trip(
        trip_id=9301,
        x=TripCancelIn(notes="Annulation de test"),
        u=admin,
        db=db,
    )

    assert resultat["status"] == "CANCELLED"
    print("SUCCES : annulation SCHEDULED autorisee.")

    verifier_refus_409(
        lambda: cancel_trip(
            trip_id=9301,
            x=TripCancelIn(),
            u=admin,
            db=db,
        ),
        "Nouvelle annulation CANCELLED refusee",
    )
    db.rollback()

    # --------------------------------------------------------
    # 3. Refus d'annulation d'une course en cours
    # --------------------------------------------------------

    db.get(Trip, 9302).status = "IN_PROGRESS"
    db.commit()

    verifier_refus_409(
        lambda: cancel_trip(
            trip_id=9302,
            x=TripCancelIn(),
            u=admin,
            db=db,
        ),
        "Annulation IN_PROGRESS refusee",
    )
    db.rollback()

    # --------------------------------------------------------
    # 4. Refus d'annulation d'une course terminee
    # --------------------------------------------------------

    db.get(Trip, 9303).status = "COMPLETED"
    db.commit()

    verifier_refus_409(
        lambda: cancel_trip(
            trip_id=9303,
            x=TripCancelIn(),
            u=admin,
            db=db,
        ),
        "Annulation COMPLETED refusee",
    )
    db.rollback()

    # --------------------------------------------------------
    # 5. Maintenance planifiee
    # --------------------------------------------------------

    m1 = create_maintenance(
        x=MaintenanceIn(
            vehicle_id=9301,
            description="Revision planifiee",
            status="PLANNED",
        ),
        u=admin,
        db=db,
    )

    m1_id = m1.id
    assert db.get(Vehicle, 9301).status == "ACTIVE"
    print("SUCCES : maintenance PLANNED sans immobilisation.")

    # --------------------------------------------------------
    # 6. Refus de maintenance pendant une course
    # --------------------------------------------------------

    verifier_refus_409(
        lambda: update_maintenance(
            maintenance_id=m1_id,
            x=MaintenanceUpdate(status="IN_PROGRESS"),
            u=admin,
            db=db,
        ),
        "Maintenance interdite pendant une course",
    )
    db.rollback()

    # Terminer fictivement la course pour liberer le bus.
    db.get(Trip, 9302).status = "COMPLETED"
    db.commit()

    # --------------------------------------------------------
    # 7. Immobilisation du bus
    # --------------------------------------------------------

    update_maintenance(
        maintenance_id=m1_id,
        x=MaintenanceUpdate(status="IN_PROGRESS"),
        u=admin,
        db=db,
    )

    assert db.get(Vehicle, 9301).status == "MAINTENANCE"
    print("SUCCES : maintenance IN_PROGRESS immobilise le bus.")

    # --------------------------------------------------------
    # 8. Refus de depart pendant la maintenance
    # --------------------------------------------------------

    verifier_refus_409(
        lambda: start_trip(
            trip_id=9304,
            x=TripStartIn(start_mileage=10000),
            u=admin,
            db=db,
        ),
        "Depart refuse pendant la maintenance",
    )
    db.rollback()

    # --------------------------------------------------------
    # 9. Deuxieme maintenance active
    # --------------------------------------------------------

    m2 = create_maintenance(
        x=MaintenanceIn(
            vehicle_id=9301,
            description="Reparation complementaire",
            status="IN_PROGRESS",
        ),
        u=admin,
        db=db,
    )

    m2_id = m2.id

    # Terminer la premiere maintenance.
    update_maintenance(
        maintenance_id=m1_id,
        x=MaintenanceUpdate(status="COMPLETED"),
        u=admin,
        db=db,
    )

    assert db.get(Vehicle, 9301).status == "MAINTENANCE"
    print("SUCCES : bus immobilise tant qu'une maintenance reste active.")

    # --------------------------------------------------------
    # 10. Fin de la derniere maintenance
    # --------------------------------------------------------

    update_maintenance(
        maintenance_id=m2_id,
        x=MaintenanceUpdate(status="COMPLETED"),
        u=admin,
        db=db,
    )

    assert db.get(Vehicle, 9301).status == "ACTIVE"
    print("SUCCES : bus disponible apres la derniere maintenance.")

    assert db.get(Maintenance, m1_id).done is True
    assert db.get(Maintenance, m2_id).done is True

    print()
    print("TOUS LES TESTS ANNULATION ET MAINTENANCE SONT REUSSIS.")
