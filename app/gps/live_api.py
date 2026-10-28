from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Vehicle
from ..security import roles
from .config import GPSMode, GPSSource
from .phone_api import GPSHybridPosition, assigned_vehicles
from .service import GPSPoint, choose_position

router = APIRouter(
    prefix="/gps/v2/live",
    tags=["GPS hybride - temps reel"]
)


def latest_position(db, vehicle_id, source):
    stmt = (
        select(GPSHybridPosition)
        .where(
            GPSHybridPosition.vehicle_id == vehicle_id,
            GPSHybridPosition.source == source.value,
        )
        .order_by(
            GPSHybridPosition.recorded_at.desc(),
            GPSHybridPosition.id.desc(),
        )
        .limit(1)
    )

    row = db.scalar(stmt)

    if row is None:
        return None

    return GPSPoint(
        vehicle_id=row.vehicle_id,
        latitude=row.latitude,
        longitude=row.longitude,
        speed=row.speed,
        recorded_at=row.recorded_at,
        source=GPSSource(row.source),
    )


@router.get("/{vehicle_id}")
def live_vehicle(
    vehicle_id: int,
    mode: GPSMode = Query(default=GPSMode.AUTO),
    user=Depends(roles("ADMIN", "DRIVER")),
    db: Session = Depends(get_db),
):
    vehicle = db.get(Vehicle, vehicle_id)

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicule introuvable"
        )

    if user.country_id is None:
        raise HTTPException(
            status_code=403,
            detail="Pays utilisateur non defini"
        )

    if vehicle.country_id != user.country_id:
        raise HTTPException(
            status_code=403,
            detail="Vehicule non autorise"
        )

    if user.role.value == "DRIVER":
        allowed_ids = {
            v.id for v in assigned_vehicles(db, user)
        }

        if vehicle_id not in allowed_ids:
            raise HTTPException(
                status_code=403,
                detail="Vehicule non affecte au chauffeur"
            )

    now = datetime.now(timezone.utc)

    phone = latest_position(
        db, vehicle_id, GPSSource.PHONE
    )

    device = latest_position(
        db, vehicle_id, GPSSource.DEVICE
    )

    selected = choose_position(
        phone=phone,
        device=device,
        mode=mode,
        now=now,
    )

    if selected is None:
        return {
            "vehicle_id": vehicle_id,
            "mode": mode.value,
            "status": "OFFLINE",
            "source": None,
            "latitude": None,
            "longitude": None,
            "speed": None,
            "recorded_at": None,
        }

    return {
        "vehicle_id": vehicle_id,
        "mode": mode.value,
        "status": "ONLINE",
        "source": selected.source.value,
        "latitude": selected.latitude,
        "longitude": selected.longitude,
        "speed": selected.speed,
        "recorded_at": selected.recorded_at.isoformat(),
    }
