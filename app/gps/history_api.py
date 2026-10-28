
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Vehicle
from ..security import roles
from .config import GPSSource
from .phone_api import GPSHybridPosition, assigned_vehicles


router = APIRouter(
    prefix="/gps/v2/history",
    tags=["GPS hybride - historique"],
)


@router.get("/{vehicle_id}")
def vehicle_history(
    vehicle_id: int,
    start: Optional[datetime] = Query(default=None),
    end: Optional[datetime] = Query(default=None),
    source: Optional[GPSSource] = Query(default=None),
    limit: int = Query(default=500, ge=1, le=2000),
    user=Depends(roles("ADMIN", "COUNTRY_MANAGER", "DRIVER")),
    db: Session = Depends(get_db),
):
    # 1. Verifier l'existence du vehicule
    vehicle = db.get(Vehicle, vehicle_id)

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicule introuvable",
        )

    # 2. Controler les autorisations par pays
    if user.role.value != "ADMIN":
        if user.country_id is None:
            raise HTTPException(
                status_code=403,
                detail="Pays utilisateur non defini",
            )

        if vehicle.country_id != user.country_id:
            raise HTTPException(
                status_code=403,
                detail="Vehicule non autorise",
            )

    # 3. Controler les affectations chauffeur
    if user.role.value == "DRIVER":
        allowed_ids = {
            v.id for v in assigned_vehicles(db, user)
        }

        if vehicle_id not in allowed_ids:
            raise HTTPException(
                status_code=403,
                detail="Vehicule non affecte au chauffeur",
            )

    # 4. Definir la periode de consultation
    now = datetime.now(timezone.utc)

    if end is None:
        end = now

    if start is None:
        start = end - timedelta(hours=24)

    if start.tzinfo is None or end.tzinfo is None:
        raise HTTPException(
            status_code=422,
            detail="Les dates doivent contenir un fuseau horaire",
        )

    start = start.astimezone(timezone.utc)
    end = end.astimezone(timezone.utc)

    if start > end:
        raise HTTPException(
            status_code=422,
            detail="La date de debut doit preceder la date de fin",
        )

    if end - start > timedelta(days=31):
        raise HTTPException(
            status_code=422,
            detail="Periode maximale : 31 jours",
        )

    # 5. Construire la requete SQL
    filters = [
        GPSHybridPosition.vehicle_id == vehicle_id,
        GPSHybridPosition.recorded_at >= start,
        GPSHybridPosition.recorded_at <= end,
    ]

    if source is not None:
        filters.append(
            GPSHybridPosition.source == source.value
        )

    # 6. Compter les positions disponibles
    total = db.scalar(
        select(func.count(GPSHybridPosition.id))
        .where(*filters)
    ) or 0

    # 7. Recuperer les positions
    # Les plus recentes sont selectionnees en premier.
    stmt = (
        select(GPSHybridPosition)
        .where(*filters)
        .order_by(
            GPSHybridPosition.recorded_at.desc(),
            GPSHybridPosition.id.desc(),
        )
        .limit(limit)
    )

    rows = db.scalars(stmt).all()

    # Ordre chronologique pour tracer le parcours
    rows.reverse()

    positions = [
        {
            "id": row.id,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "speed": row.speed,
            "source": row.source,
            "recorded_at": row.recorded_at.isoformat(),
        }
        for row in rows
    ]

    return {
        "vehicle_id": vehicle_id,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "source": source.value if source else "ALL",
        "total": total,
        "returned": len(positions),
        "truncated": total > len(positions),
        "positions": positions,
    }
