from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import City, Country, Stop, Line, LineStop
from app.security import roles
from app.schemas import CityIn, StopIn, LineStopIn


router = APIRouter(tags=["Urban Routes"])


# ============================================================
# V5.9 - CONSULTATION DES VILLES
# ============================================================

@router.get("/cities")
def list_cities(
    u=Depends(
        roles(
            "ADMIN",
            "COUNTRY_MANAGER",
            "AGENT",
            "CONTROLLER",
            "DRIVER"
        )
    ),
    db: Session = Depends(get_db)
):
    query = db.query(City)

    if u.role.value == "COUNTRY_MANAGER":

        if u.country_id is None:
            raise HTTPException(
                status_code=403,
                detail="Pays d'affectation manquant"
            )

        query = query.filter(
            City.country_id == u.country_id
        )

    return query.order_by(City.name, City.id).all()


# ============================================================
# V5.9 - CREATION DES VILLES
# ============================================================

@router.post("/cities", status_code=201)
def create_city(
    data: CityIn,
    u=Depends(roles("ADMIN")),
    db: Session = Depends(get_db)
):
    name = data.name.strip()

    if not name:
        raise HTTPException(
            status_code=422,
            detail="Le nom de la ville est obligatoire"
        )

    country = db.get(Country, data.country_id)

    if country is None:
        raise HTTPException(
            status_code=404,
            detail="Pays introuvable"
        )

    existing = (
        db.query(City)
        .filter(
            City.country_id == data.country_id,
            func.lower(City.name) == name.lower()
        )
        .first()
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Cette ville existe deja dans ce pays"
        )

    city = City(
        country_id=data.country_id,
        name=name
    )

    try:
        db.add(city)
        db.commit()
        db.refresh(city)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ville existante ou donnees incoherentes"
        )

    return city

# ============================================================
# V5.9 - CONSULTATION DES ARRETS URBAINS
# ============================================================

@router.get("/stops")
def list_stops(
    city_id: int | None = None,
    u=Depends(
        roles(
            "ADMIN",
            "COUNTRY_MANAGER",
            "AGENT",
            "CONTROLLER",
            "DRIVER"
        )
    ),
    db: Session = Depends(get_db)
):
    if city_id is not None and city_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="Identifiant de ville invalide"
        )

    query = db.query(Stop).join(
        City, Stop.city_id == City.id
    )

    if u.role.value == "COUNTRY_MANAGER":
        if u.country_id is None:
            raise HTTPException(
                status_code=403,
                detail="Pays d'affectation manquant"
            )

        query = query.filter(
            City.country_id == u.country_id
        )

    if city_id is not None:
        query = query.filter(
            Stop.city_id == city_id
        )

    return query.order_by(
        Stop.city_id,
        Stop.name,
        Stop.id
    ).all()

# ============================================================
# V5.9 - CREATION DES ARRETS URBAINS
# ============================================================

@router.post("/stops", status_code=201)
def create_stop(
    data: StopIn,
    u=Depends(roles("ADMIN")),
    db: Session = Depends(get_db)
):
    name = data.name.strip()

    if not name:
        raise HTTPException(
            status_code=422,
            detail="Le nom de l'arret est obligatoire"
        )

    city = db.get(City, data.city_id)

    if city is None:
        raise HTTPException(
            status_code=404,
            detail="Ville introuvable"
        )

    existing = (
        db.query(Stop)
        .filter(
            Stop.city_id == data.city_id,
            func.lower(Stop.name) == name.lower()
        )
        .first()
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Cet arret existe deja dans cette ville"
        )

    stop = Stop(
        city_id=data.city_id,
        name=name,
        latitude=data.latitude,
        longitude=data.longitude
    )

    try:
        db.add(stop)
        db.commit()
        db.refresh(stop)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Arret existant ou donnees incoherentes"
        )

    return stop

# ============================================================
# V5.9 - CONSULTATION DES ARRETS D'UNE LIGNE
# ============================================================

@router.get("/lines/{line_id}/stops")
def list_line_stops(
    line_id: int,
    u=Depends(
        roles(
            "ADMIN",
            "COUNTRY_MANAGER",
            "AGENT",
            "CONTROLLER",
            "DRIVER"
        )
    ),
    db: Session = Depends(get_db)
):
    if line_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="Identifiant de ligne invalide"
        )

    line = db.get(Line, line_id)

    if line is None:
        raise HTTPException(
            status_code=404,
            detail="Ligne introuvable"
        )

    if u.role.value == "COUNTRY_MANAGER":
        if u.country_id is None:
            raise HTTPException(
                status_code=403,
                detail="Pays d'affectation manquant"
            )

        if line.country_id != u.country_id:
            raise HTTPException(
                status_code=403,
                detail="Acces interdit a cette ligne"
            )

    results = (
        db.query(LineStop, Stop)
        .join(Stop, LineStop.stop_id == Stop.id)
        .filter(
            LineStop.line_id == line_id,
            LineStop.city_id == Stop.city_id
        )
        .order_by(
            LineStop.stop_order,
            LineStop.id
        )
        .all()
    )

    return [
        {
            "id": line_stop.id,
            "line_id": line_stop.line_id,
            "city_id": line_stop.city_id,
            "stop_id": stop.id,
            "stop_order": line_stop.stop_order,
            "name": stop.name,
            "latitude": stop.latitude,
            "longitude": stop.longitude
        }
        for line_stop, stop in results
    ]

# ============================================================
# V5.9 - ASSOCIATION D'UN ARRET A UNE LIGNE
# ============================================================

@router.post("/lines/{line_id}/stops", status_code=201)
def create_line_stop(
    line_id: int,
    data: LineStopIn,
    u=Depends(roles("ADMIN")),
    db: Session = Depends(get_db)
):
    if line_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="Identifiant de ligne invalide"
        )

    line = db.get(Line, line_id)

    if line is None:
        raise HTTPException(
            status_code=404,
            detail="Ligne introuvable"
        )

    if line.city_id is None:
        raise HTTPException(
            status_code=422,
            detail="La ligne n'est associee a aucune ville"
        )

    stop = db.get(Stop, data.stop_id)

    if stop is None:
        raise HTTPException(
            status_code=404,
            detail="Arret introuvable"
        )

    if stop.city_id != line.city_id:
        raise HTTPException(
            status_code=422,
            detail="L'arret et la ligne doivent appartenir a la meme ville"
        )

    existing_stop = (
        db.query(LineStop)
        .filter(
            LineStop.line_id == line_id,
            LineStop.stop_id == data.stop_id
        )
        .first()
    )

    if existing_stop is not None:
        raise HTTPException(
            status_code=409,
            detail="Cet arret est deja associe a cette ligne"
        )

    existing_order = (
        db.query(LineStop)
        .filter(
            LineStop.line_id == line_id,
            LineStop.stop_order == data.stop_order
        )
        .first()
    )

    if existing_order is not None:
        raise HTTPException(
            status_code=409,
            detail="Cet ordre de passage est deja utilise"
        )

    association = LineStop(
        line_id=line_id,
        city_id=line.city_id,
        stop_id=data.stop_id,
        stop_order=data.stop_order
    )

    try:
        db.add(association)
        db.commit()
        db.refresh(association)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Association existante ou donnees incoherentes"
        )

    return {
        "id": association.id,
        "line_id": association.line_id,
        "city_id": association.city_id,
        "stop_id": association.stop_id,
        "stop_order": association.stop_order
    }
