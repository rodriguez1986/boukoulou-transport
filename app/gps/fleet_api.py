from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Vehicle
from ..security import roles
from .config import GPSMode, GPSSource, GPS_REFRESH_SECONDS
from .live_api import latest_position
from .service import choose_position


router = APIRouter(
    prefix="/gps/v2/live",
    tags=["GPS hybride - flotte"],
)


@router.get("/fleet")
def live_fleet(
    mode: GPSMode = Query(default=GPSMode.AUTO),
    user=Depends(roles("ADMIN", "COUNTRY_MANAGER")),
    db: Session = Depends(get_db),
):
    query = select(Vehicle).order_by(Vehicle.id)

    if user.role.value == "COUNTRY_MANAGER":
        if user.country_id is None:
            raise HTTPException(
                status_code=403,
                detail="Pays utilisateur non defini",
            )

        query = query.where(
            Vehicle.country_id == user.country_id
        )

    vehicles = db.scalars(query).all()
    now = datetime.now(timezone.utc)
    results = []

    for vehicle in vehicles:
        phone = latest_position(
            db, vehicle.id, GPSSource.PHONE
        )

        device = latest_position(
            db, vehicle.id, GPSSource.DEVICE
        )

        selected = choose_position(
            phone=phone,
            device=device,
            mode=mode,
            now=now,
        )

        results.append({
            "vehicle_id": vehicle.id,
            "code": vehicle.code,
            "plate": vehicle.plate,
            "country_id": vehicle.country_id,
            "mode": mode.value,
            "status": "ONLINE" if selected else "OFFLINE",
            "source": (
                selected.source.value if selected else None
            ),
            "latitude": (
                selected.latitude if selected else None
            ),
            "longitude": (
                selected.longitude if selected else None
            ),
            "speed": (
                selected.speed if selected else None
            ),
            "recorded_at": (
                selected.recorded_at.isoformat()
                if selected else None
            ),
        })

    online = sum(
        1 for item in results
        if item["status"] == "ONLINE"
    )

    return {
        "mode": mode.value,
        "refresh_seconds": GPS_REFRESH_SECONDS,
        "total": len(results),
        "online": online,
        "offline": len(results) - online,
        "vehicles": results,
    }