from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, StrictInt, field_validator
from sqlalchemy.orm import Session
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from app.db import get_db
from app.models import (
    Line,
    Stop,
    RouteVariant,
    RouteVersion,
    RouteVersionStop,
)
from app.security import roles


router = APIRouter(
    prefix="/urban",
    tags=["Urban Route Versions"],
)


READ_ROLES = (
    "ADMIN",
    "COUNTRY_MANAGER",
    "AGENT",
    "CONTROLLER",
    "DRIVER",
)


def check_country_access(user, country_id: int):
    if user.role.value == "COUNTRY_MANAGER":
        if user.country_id is None:
            raise HTTPException(
                status_code=403,
                detail="Pays d'affectation manquant",
            )

        if user.country_id != country_id:
            raise HTTPException(
                status_code=403,
                detail="Acces interdit a ce pays",
            )


def get_line_or_404(db: Session, line_id: int):
    line = db.get(Line, line_id)

    if line is None:
        raise HTTPException(
            status_code=404,
            detail="Ligne introuvable",
        )

    return line


@router.get("/lines/{line_id}/route-variants")
def list_route_variants(
    line_id: int,
    user=Depends(roles(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    if line_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="Identifiant de ligne invalide",
        )

    line = get_line_or_404(db, line_id)
    check_country_access(user, line.country_id)

    variants = (
        db.query(RouteVariant)
        .filter(RouteVariant.line_id == line_id)
        .order_by(RouteVariant.direction, RouteVariant.id)
        .all()
    )

    return [
        {
            "id": variant.id,
            "line_id": variant.line_id,
            "city_id": variant.city_id,
            "direction": variant.direction,
            "name": variant.name,
        }
        for variant in variants
    ]


@router.get("/route-variants/{variant_id}/versions")
def list_route_versions(
    variant_id: int,
    user=Depends(roles(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    if variant_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="Identifiant de variante invalide",
        )

    variant = db.get(RouteVariant, variant_id)

    if variant is None:
        raise HTTPException(
            status_code=404,
            detail="Variante introuvable",
        )

    line = get_line_or_404(db, variant.line_id)
    check_country_access(user, line.country_id)

    versions = (
        db.query(RouteVersion)
        .filter(RouteVersion.route_variant_id == variant_id)
        .order_by(
            RouteVersion.version_number.desc(),
            RouteVersion.id.desc(),
        )
        .all()
    )

    return [
        {
            "id": version.id,
            "route_variant_id": version.route_variant_id,
            "line_id": version.line_id,
            "city_id": version.city_id,
            "version_number": version.version_number,
            "status": version.status,
            "valid_from": version.valid_from,
            "valid_to": version.valid_to,
        }
        for version in versions
    ]


@router.get("/route-versions/{version_id}/stops")
def list_route_version_stops(
    version_id: int,
    user=Depends(roles(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    if version_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="Identifiant de version invalide",
        )

    version = db.get(RouteVersion, version_id)

    if version is None:
        raise HTTPException(
            status_code=404,
            detail="Version introuvable",
        )

    line = get_line_or_404(db, version.line_id)
    check_country_access(user, line.country_id)

    rows = (
        db.query(RouteVersionStop, Stop)
        .join(
            Stop,
            Stop.id == RouteVersionStop.stop_id,
        )
        .filter(
            RouteVersionStop.route_version_id == version_id,
            RouteVersionStop.city_id == version.city_id,
            Stop.city_id == version.city_id,
        )
        .order_by(
            RouteVersionStop.stop_order,
            RouteVersionStop.id,
        )
        .all()
    )

    return [
        {
            "id": association.id,
            "route_version_id": association.route_version_id,
            "city_id": association.city_id,
            "stop_id": stop.id,
            "stop_order": association.stop_order,
            "name": stop.name,
            "latitude": stop.latitude,
            "longitude": stop.longitude,
        }
        for association, stop in rows
    ]


class DraftRouteStopsIn(BaseModel):
    stop_ids: list[StrictInt] = Field(min_length=2)

    @field_validator("stop_ids")
    @classmethod
    def validate_stop_ids(cls, values):
        if any(type(stop_id) is not int or stop_id <= 0 for stop_id in values):
            raise ValueError("Les identifiants doivent etre des entiers positifs")

        if len(values) != len(set(values)):
            raise ValueError("Un arret ne peut pas etre repete")

        return values


@router.put("/route-versions/{version_id}/stops")
def replace_draft_route_stops(
    version_id: int,
    payload: DraftRouteStopsIn,
    user=Depends(roles("ADMIN")),
    db: Session = Depends(get_db),
):
    if version_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="Identifiant de version invalide",
        )

    try:
        version = (
            db.query(RouteVersion)
            .filter(RouteVersion.id == version_id)
            .with_for_update()
            .one_or_none()
        )

        if version is None:
            raise HTTPException(
                status_code=404,
                detail="Version introuvable",
            )

        if version.status != "DRAFT":
            raise HTTPException(
                status_code=409,
                detail="Seules les versions DRAFT sont modifiables",
            )

        stops = (
            db.query(Stop)
            .filter(Stop.id.in_(payload.stop_ids))
            .all()
        )

        stops_by_id = {stop.id: stop for stop in stops}

        if len(stops_by_id) != len(payload.stop_ids):
            raise HTTPException(
                status_code=422,
                detail="Un ou plusieurs arrets sont introuvables",
            )

        if any(
            stop.city_id != version.city_id
            for stop in stops
        ):
            raise HTTPException(
                status_code=422,
                detail="Tous les arrets doivent appartenir a la ville du parcours",
            )

        db.execute(
            delete(RouteVersionStop).where(
                RouteVersionStop.route_version_id == version_id
            )
        )

        new_rows = [
            RouteVersionStop(
                route_version_id=version_id,
                city_id=version.city_id,
                stop_id=stop_id,
                stop_order=position,
            )
            for position, stop_id in enumerate(
                payload.stop_ids,
                start=1,
            )
        ]

        db.add_all(new_rows)
        db.commit()

        return {
            "route_version_id": version_id,
            "status": version.status,
            "stop_count": len(payload.stop_ids),
            "stops": [
                {
                    "stop_id": stop_id,
                    "stop_order": position,
                    "name": stops_by_id[stop_id].name,
                }
                for position, stop_id in enumerate(
                    payload.stop_ids,
                    start=1,
                )
            ],
        }

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflit de contraintes sur les arrets du parcours",
        )

    except Exception:
        db.rollback()
        raise