# ============================================================
# BOUKOULOU TRANSPORT V5.9 - ETAPE 93
# TEST REEL D'ISOLATION ENTRE CHAUFFEURS
#
# Objectifs :
# - Tester les vrais modeles SQLAlchemy.
# - Tester la vraie fonction verifier_acces_course().
# - Verifier les autorisations DRIVER et ADMIN.
#
# Securite :
# - Base SQLite en memoire uniquement.
# - Aucune connexion a PostgreSQL.
# - Aucune modification des courses existantes.
# - Aucun appel aux routes PUT.
# ============================================================

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.models import User, Driver, Trip
# Importer les fonctions reelles de l'application.
from app.main import (
    verifier_acces_course,
    start_trip,
    complete_trip,
    trip_report,          # Rapport de course securise
    trip_availability,
    TripStartIn,
    TripCompleteIn,
)


# ------------------------------------------------------------
# 1. Creer une base SQLite temporaire en memoire
# ------------------------------------------------------------

engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Activer la verification des cles etrangeres dans SQLite.
@event.listens_for(engine, "connect")
def configurer_sqlite(connexion, enregistrement):
    connexion.execute("PRAGMA foreign_keys=ON")


# ------------------------------------------------------------
# 2. Creer les tables strictement necessaires
#
# Les relations avec countries, lines et vehicles imposent
# egalement la creation de leurs tables.
# ------------------------------------------------------------

from app.models import Country, Line, Vehicle

# Recuperer le metadata partage par les modeles.
metadata = User.metadata

metadata.create_all(
    engine,
    tables=[
        Country.__table__,
        User.__table__,
        Driver.__table__,
        Line.__table__,
        Vehicle.__table__,
        Trip.__table__,
    ],
)


# ------------------------------------------------------------
# 3. Construire les donnees fictives
# ------------------------------------------------------------

with Session(engine) as db:

    # Pays fictif.
    # Les colonnes obligatoires seront inspectees avant
    # insertion si le modele impose d'autres informations.
    pays = Country(
        id=9001,
        code="ZZ",
        name="Pays Test",
        currency="XOF",
    )
        # ========================================================

# ------------------------------------------------------------
# Enregistrer le pays dans la transaction SQLite.
#
# flush() rend le pays disponible pour les cles etrangeres
# sans valider definitivement la transaction.
# ------------------------------------------------------------

    db.add(pays)
    db.flush()

    # Deux utilisateurs chauffeurs et un administrateur.
    # Aucun mot de passe reel n'est utilise.
    chauffeur_a = User(
        id=9001,
        username="test.driver.a",
        password_hash="TEST_ONLY",
        role="DRIVER",
        is_active=True,
    )

    chauffeur_b = User(
        id=9002,
        username="test.driver.b",
        password_hash="TEST_ONLY",
        role="DRIVER",
        is_active=True,
    )

    administrateur = User(
        id=9003,
        username="test.admin",
        password_hash="TEST_ONLY",
        role="ADMIN",
        is_active=True,
    )

    db.add_all([
        chauffeur_a,
        chauffeur_b,
        administrateur,
    ])
    db.flush()

    # Creer les deux chauffeurs associes aux utilisateurs.
    conducteur_a = Driver(
        id=9001,
        country_id=9001,
        user_id=9001,
        employee_code="TEST-A",
        first_name="Chauffeur",
        last_name="A",
        license_number="TEST-LIC-A",
        status="ACTIVE",
    )

    conducteur_b = Driver(
        id=9002,
        country_id=9001,
        user_id=9002,
        employee_code="TEST-B",
        first_name="Chauffeur",
        last_name="B",
        license_number="TEST-LIC-B",
        status="ACTIVE",
    )

    db.add_all([conducteur_a, conducteur_b])
    db.flush()
    # Ligne et vehicule fictifs.
    ligne = Line(
        id=9001,
        country_id=9001,
        code="TEST-LINE",
        name="Ligne fictive",
        fare=100,
    )

    vehicule = Vehicle(
        id=9001,
        country_id=9001,
        code="TEST-BUS",
        plate="TEST-9001",
        capacity=30,
        standing_capacity=10,
        status="ACTIVE",
    )

    db.add_all([ligne, vehicule])
    db.flush()

    # Course affectee uniquement au chauffeur A.
    course = Trip(
        id=9001,
        line_id=9001,
        vehicle_id=9001,
        driver_id=9001,
        departure_at=datetime.now(timezone.utc),
        status="SCHEDULED",
    )

    db.add(course)

    # Enregistrer uniquement dans SQLite en memoire.
    db.commit()

    print("Donnees fictives creees dans SQLite.")

    # --------------------------------------------------------
    # 4. Chauffeur A : acces autorise
    # --------------------------------------------------------

    resultat = verifier_acces_course(
        db,
        chauffeur_a,
        9001,
    )

    assert resultat.id == 9001

    print("SUCCES : chauffeur A accede a sa course.")

    # --------------------------------------------------------
    # 5. Chauffeur B : acces refuse
    # --------------------------------------------------------

    try:
        verifier_acces_course(
            db,
            chauffeur_b,
            9001,
        )

    except HTTPException as erreur:
        assert erreur.status_code == 404
        print("SUCCES : chauffeur B refuse (HTTP 404).")

    else:
        raise AssertionError(
            "FAILLE : chauffeur B accede a la course de A."
        )

    # --------------------------------------------------------
    # 6. Administrateur : acces autorise
    # --------------------------------------------------------

    resultat = verifier_acces_course(
        db,
        administrateur,
        9001,
    )

    assert resultat.id == 9001

    print("SUCCES : administrateur autorise.")

    # --------------------------------------------------------
    # 7. Course inexistante : HTTP 404
    # --------------------------------------------------------

    try:
        verifier_acces_course(
            db,
            chauffeur_a,
            999999,
        )

    except HTTPException as erreur:
        assert erreur.status_code == 404
        print("SUCCES : course inexistante refusee.")

    else:
        raise AssertionError(
            "ECHEC : course inexistante acceptee."
        )

        # ========================================================
    # ETAPE 93.2 : TEST DES OPERATIONS NON AUTORISEES
    #
    # Ces tests utilisent uniquement SQLite en memoire.
    # Aucun demarrage ni aucune cloture ne doit etre accepte.
    # ========================================================

    # Memoriser l'etat initial de la course et du vehicule.
    etat_initial = course.status
    kilometrage_initial = vehicule.mileage

    # --------------------------------------------------------
    # TEST 1 : Le chauffeur B tente de demarrer la course A.
    # --------------------------------------------------------

    try:
        start_trip(
            trip_id=9001,
            x=TripStartIn(start_mileage=1000),
            u=chauffeur_b,
            db=db,
        )

    except HTTPException as erreur:
        assert erreur.status_code == 404
        print(
            "SUCCES : demarrage refuse au chauffeur B (HTTP 404)."
        )

    else:
        raise AssertionError(
            "FAILLE : le chauffeur B a demarre la course de A."
        )

    # --------------------------------------------------------
    # TEST 2 : Le chauffeur B tente de terminer la course A.
    # --------------------------------------------------------

    try:
        complete_trip(
            trip_id=9001,
            x=TripCompleteIn(end_mileage=1050),
            u=chauffeur_b,
            db=db,
        )

    except HTTPException as erreur:
        assert erreur.status_code == 404
        print(
            "SUCCES : cloture refusee au chauffeur B (HTTP 404)."
        )

    else:
        raise AssertionError(
            "FAILLE : le chauffeur B a termine la course de A."
        )

    # --------------------------------------------------------
    # TEST 3 : Verifier qu'aucune donnee n'a change.
    # --------------------------------------------------------

    db.expire_all()

    course_verifiee = db.get(Trip, 9001)
    vehicule_verifie = db.get(Vehicle, 9001)

    assert course_verifiee.status == etat_initial
    assert vehicule_verifie.mileage == kilometrage_initial

    print("SUCCES : etat de la course inchange.")
    print("SUCCES : kilometrage du vehicule inchange.")
        # ========================================================
    # ETAPE 93.3 : DEMARRAGE ET CLOTURE AUTORISES
    #
    # Base SQLite en memoire uniquement.
    # Aucun changement dans PostgreSQL.
    # ========================================================

    from datetime import timedelta
    from unittest.mock import patch

    # --------------------------------------------------------
    # 1. Preparer la course pour un depart autorise.
    #
    # Le depart est prevu 5 minutes avant l'heure actuelle.
    # Cela respecte la limite de depart anticipe de 30 min.
    # --------------------------------------------------------

    course.departure_at = (
        datetime.now(timezone.utc) - timedelta(minutes=5)
    )

    # Le vehicule doit etre actif et posseder un compteur
    # inferieur ou egal au kilometrage de depart.
    vehicule.status = "ACTIVE"
    vehicule.mileage = 900

    conducteur_a.status = "ACTIVE"

    db.commit()

    # --------------------------------------------------------
    # 2. Demarrer la course avec le chauffeur A.
    #
    # L'audit est neutralise uniquement dans ce test pour
    # eviter de dependre des tables de journalisation.
    # --------------------------------------------------------

    with patch("app.main.audit"):

        resultat_depart = start_trip(
            trip_id=9001,
            x=TripStartIn(start_mileage=1000),
            u=chauffeur_a,
            db=db,
        )

    assert resultat_depart["status"] == "IN_PROGRESS"
    assert resultat_depart["start_mileage"] == 1000

    db.expire_all()

    course_verifiee = db.get(Trip, 9001)
    vehicule_verifie = db.get(Vehicle, 9001)

    assert course_verifiee.status == "IN_PROGRESS"
    assert course_verifiee.start_mileage == 1000
    assert vehicule_verifie.mileage == 1000

    print("SUCCES : chauffeur A demarre sa course.")
    print("SUCCES : course passee a IN_PROGRESS.")

    # --------------------------------------------------------
    # 3. Terminer la course avec le chauffeur A.
    # --------------------------------------------------------

    with patch("app.main.audit"):

        resultat_fin = complete_trip(
            trip_id=9001,
            x=TripCompleteIn(end_mileage=1050),
            u=chauffeur_a,
            db=db,
        )

    assert resultat_fin["status"] == "COMPLETED"
    assert resultat_fin["end_mileage"] == 1050
    assert resultat_fin["distance_km"] == 50

    db.expire_all()

    course_verifiee = db.get(Trip, 9001)
    vehicule_verifie = db.get(Vehicle, 9001)

    assert course_verifiee.status == "COMPLETED"
    assert course_verifiee.end_mileage == 1050
    assert vehicule_verifie.mileage == 1050

    print("SUCCES : chauffeur A termine sa course.")
    print("SUCCES : course passee a COMPLETED.")
    print("SUCCES : distance parcourue = 50 km.")
    print("SUCCES : compteur du vehicule = 1050 km.")

        # ========================================================
    # BOUKOULOU TRANSPORT V5.9 - ETAPE 93.4.4
    #
    # TEST DE SECURITE DES DISPONIBILITES
    #
    # Ces tests s'executent dans la session SQLite existante.
    # Aucune modification de PostgreSQL.
    # ========================================================

    from unittest.mock import patch

    # --------------------------------------------------------
    # TEST 1 : Chauffeur A autorise
    # --------------------------------------------------------

    with patch("app.main._places_occupees", return_value=5):

        disponibilites_a = trip_availability(
            trip_id=9001,
            u=chauffeur_a,
            db=db,
        )

    assert disponibilites_a["trip_id"] == 9001
    assert disponibilites_a["occupied"] == 5

    print("SUCCES : chauffeur A consulte les disponibilites.")

    # --------------------------------------------------------
    # TEST 2 : Chauffeur B non autorise
    # --------------------------------------------------------

    try:
        trip_availability(
            trip_id=9001,
            u=chauffeur_b,
            db=db,
        )

    except HTTPException as erreur:
        assert erreur.status_code == 404

        print(
            "SUCCES : disponibilites refusees au chauffeur B."
        )

    else:
        raise AssertionError(
            "FAILLE : chauffeur B consulte les disponibilites."
        )

    # --------------------------------------------------------
    # TEST 3 : Administrateur autorise
    # --------------------------------------------------------

    with patch("app.main._places_occupees", return_value=5):

        disponibilites_admin = trip_availability(
            trip_id=9001,
            u=administrateur,
            db=db,
        )

    assert disponibilites_admin["trip_id"] == 9001

    print("SUCCES : administrateur consulte les disponibilites.")

    # --------------------------------------------------------
    # TEST 4 : Verifier les calculs de capacite
    # --------------------------------------------------------

    assert (
        disponibilites_a["capacity"]
        == disponibilites_a["seated_capacity"]
        + disponibilites_a["standing_capacity"]
    )

    assert (
        disponibilites_a["available"]
        == max(0, disponibilites_a["capacity"] - 5)
    )

    print("SUCCES : calcul des disponibilites correct.")


# ============================================================
# FIN DE TOUS LES TESTS
#
# Cette instruction est volontairement hors de la session.
# ============================================================

print("")
print("TOUS LES TESTS D'ISOLATION SONT REUSSIS.")
