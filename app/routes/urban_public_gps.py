from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Line, Trip, Vehicle
from app.gps.config import GPSMode, GPS_REFRESH_SECONDS
from app.gps.live_api import latest_position
from app.gps.service import choose_position
from app.gps.config import GPSSource


router = APIRouter(tags=["Urban Public GPS"])


@router.get("/urban/public/lines/{line_id}/vehicles")
def public_line_vehicles(
    line_id: int,
    db: Session = Depends(get_db),
):
    """
    Positions GPS publiques des bus en circulation
    sur une ligne urbaine.

    Aucune authentification requise.
    Consultation uniquement.
    """

    if line_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="Identifiant de ligne invalide."
        )

    line = db.get(Line, line_id)

    if line is None or line.city_id is None:
        raise HTTPException(
            status_code=404,
            detail="Ligne urbaine introuvable."
        )

    stmt = (
        select(Trip, Vehicle)
        .join(Vehicle, Vehicle.id == Trip.vehicle_id)
        .where(
            Trip.line_id == line.id,
            Trip.status == "IN_PROGRESS",
            Vehicle.country_id == line.country_id,
            Vehicle.status == "ACTIVE",
        )
        .order_by(Trip.id)
    )

    rows = db.execute(stmt).all()

    now = datetime.now(timezone.utc)
    vehicles = []
    seen_vehicle_ids = set()

    for trip, vehicle in rows:
        if vehicle.id in seen_vehicle_ids:
            continue

        seen_vehicle_ids.add(vehicle.id)

        phone = latest_position(
            db, vehicle.id, GPSSource.PHONE
        )

        device = latest_position(
            db, vehicle.id, GPSSource.DEVICE
        )

        position = choose_position(
            phone=phone,
            device=device,
            mode=GPSMode.AUTO,
            now=now,
        )

        if position is None:
            continue

        vehicles.append({
            "vehicle_id": vehicle.id,
            "code": vehicle.code,
            "latitude": position.latitude,
            "longitude": position.longitude,
            "recorded_at": position.recorded_at.isoformat(),
        })

    return {
        "line_id": line.id,
        "line_code": line.code,
        "line_name": line.name,
        "refresh_seconds": GPS_REFRESH_SECONDS,
        "vehicles": vehicles,
    }
