from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import City, Country
from app.security import roles
from app.schemas import CityIn


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
