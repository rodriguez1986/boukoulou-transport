from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import City, Country, Stop
from app.security import roles
from app.schemas import CityIn, StopIn


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
