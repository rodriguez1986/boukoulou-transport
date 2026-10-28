import hashlib
import hmac
import secrets
from datetime import datetime, timezone, timedelta
from math import isfinite

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Vehicle
from ..security import roles
from .phone_api import GPSDevice, GPSHybridPosition
from .service import validate_position


router = APIRouter(
    prefix="/gps/v2/devices",
    tags=["GPS hybride - capteurs"]
)


class DeviceRegisterIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_id: int = Field(gt=0)
    device_uid: str = Field(min_length=3, max_length=120)
    device_name: str | None = Field(default=None, max_length=150)


class DevicePositionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    speed: float = Field(default=0, ge=0)
    recorded_at: datetime


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@router.post("/register", status_code=201)
def register_device(
    data: DeviceRegisterIn,
    admin=Depends(roles("ADMIN")),
    db: Session = Depends(get_db),
):
    vehicle = db.get(Vehicle, data.vehicle_id)

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicule introuvable"
        )


    uid = data.device_uid.strip()

    if len(uid) < 3:
        raise HTTPException(
            status_code=422,
            detail="Identifiant capteur trop court"
        )

    existing = db.scalar(
        select(GPSDevice).where(GPSDevice.device_uid == uid)
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Capteur deja enregistre"
        )

    token = secrets.token_urlsafe(48)

    device = GPSDevice(
        vehicle_id=data.vehicle_id,
        device_uid=uid,
        device_name=data.device_name,
        token_hash=hash_token(token),
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )

    db.add(device)

    try:
        db.commit()
        db.refresh(device)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Impossible d'enregistrer ce capteur"
        )

    return {
        "id": device.id,
        "vehicle_id": device.vehicle_id,
        "device_uid": device.device_uid,
        "device_token": token,
        "warning": "Conserver ce jeton en lieu sur. Il ne sera plus affiche."
    }


@router.post("/positions", status_code=201)
def receive_device_position(
    data: DevicePositionIn,
    x_device_uid: str | None = Header(default=None),
    x_device_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if not x_device_uid or not x_device_token:
        raise HTTPException(
            status_code=401,
            detail="Authentification capteur manquante"
        )

    device = db.scalar(
        select(GPSDevice).where(
            GPSDevice.device_uid == x_device_uid,
            GPSDevice.is_active.is_(True),
        )
    )

    if device is None:
        raise HTTPException(
            status_code=401,
            detail="Capteur non autorise"
        )

    if not hmac.compare_digest(
        device.token_hash,
        hash_token(x_device_token),
    ):
        raise HTTPException(
            status_code=401,
            detail="Capteur non autorise"
        )

    try:
        validate_position(
            device.vehicle_id,
            data.latitude,
            data.longitude,
            data.speed,
        )
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=422,
            detail="Coordonnees GPS invalides"
        )

    now = datetime.now(timezone.utc)

    recorded_at = data.recorded_at

    if recorded_at.tzinfo is None:
        raise HTTPException(
            status_code=422,
            detail="Fuseau horaire obligatoire"
        )

    recorded_at = recorded_at.astimezone(timezone.utc)

    if recorded_at > now + timedelta(seconds=30):
        raise HTTPException(
            status_code=422,
            detail="Date GPS dans le futur"
        )

    if recorded_at < now - timedelta(minutes=5):
        raise HTTPException(
            status_code=422,
            detail="Position GPS trop ancienne"
        )

    position = GPSHybridPosition(
        vehicle_id=device.vehicle_id,
        device_id=device.id,
        source="DEVICE",
        latitude=data.latitude,
        longitude=data.longitude,
        speed=data.speed,
        recorded_at=recorded_at,
        received_at=now,
    )

    db.add(position)
    db.commit()
    db.refresh(position)

    return {
        "id": position.id,
        "vehicle_id": position.vehicle_id,
        "device_id": device.id,
        "source": "DEVICE",
        "recorded_at": recorded_at.isoformat(),
        "status": "RECORDED",
    }
