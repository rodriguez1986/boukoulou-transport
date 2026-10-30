from datetime import datetime, timedelta, timezone
from math import isfinite

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Float,
    ForeignKey, Integer, String, select
)
from sqlalchemy.orm import Session

from ..db import Base, get_db
from ..models import Driver, DriverAssignment, Vehicle
from ..security import roles
from .service import validate_position


router = APIRouter(
    prefix="/gps/v2/phone",
    tags=["GPS hybride - téléphone"]
)


class GPSHybridPosition(Base):
    __tablename__ = "gps_hybrid_positions"

    id = Column(BigInteger, primary_key=True)
    vehicle_id = Column(
        Integer, ForeignKey("vehicles.id"), nullable=False
    )
    device_id = Column(
        BigInteger, ForeignKey("gps_devices.id"), nullable=True
    )
    source = Column(String(10), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed = Column(Float, nullable=False, default=0)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False)


class GPSDevice(Base):
    __tablename__ = "gps_devices"

    id = Column(BigInteger, primary_key=True)
    vehicle_id = Column(
        Integer, ForeignKey("vehicles.id"), nullable=False
    )
    device_uid = Column(String(120), nullable=False, unique=True)
    device_name = Column(String(150))
    token_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False)


class PhonePositionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    speed: float = Field(default=0, ge=0)
    recorded_at: datetime


def assigned_vehicles(db: Session, user):
    """Véhicules réellement affectés au chauffeur connecté."""

    if user.country_id is None:
        return []

    stmt = (
        select(Vehicle)
        .join(
            DriverAssignment,
            DriverAssignment.vehicle_id == Vehicle.id
        )
        .join(
            Driver,
            Driver.id == DriverAssignment.driver_id
        )
        .where(
            Driver.user_id == user.id,
            Driver.country_id == user.country_id,
            Vehicle.country_id == user.country_id,
            DriverAssignment.active.is_(True),
            DriverAssignment.ended_at.is_(None),
            Driver.status == "ACTIVE",
        )
        .distinct()
        .order_by(Vehicle.id)
    )

    return db.scalars(stmt).all()


@router.get("/vehicles")
def phone_vehicles(
    user=Depends(roles("DRIVER")),
    db: Session = Depends(get_db),
):
    vehicles = assigned_vehicles(db, user)

    return [
        {
            "id": vehicle.id,
            "code": vehicle.code,
            "plate": vehicle.plate,
        }
        for vehicle in vehicles
    ]


@router.post("/{vehicle_id}/positions", status_code=201)
def phone_position(
    vehicle_id: int,
    payload: PhonePositionIn,
    user=Depends(roles("DRIVER")),
    db: Session = Depends(get_db),
):
    if vehicle_id <= 0:
        raise HTTPException(422, "Véhicule invalide")

    vehicles = assigned_vehicles(db, user)

    if not any(vehicle.id == vehicle_id for vehicle in vehicles):
        raise HTTPException(
            status_code=403,
            detail="Véhicule non affecté à ce chauffeur"
        )

    try:
        validate_position(
            vehicle_id,
            payload.latitude,
            payload.longitude,
            payload.speed,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

    if payload.recorded_at.tzinfo is None:
        raise HTTPException(
            422, "Horodatage avec fuseau horaire obligatoire"
        )

    recorded_at = payload.recorded_at.astimezone(timezone.utc)
    now = datetime.now(timezone.utc)

    if recorded_at > now + timedelta(seconds=30):
        raise HTTPException(422, "Position GPS datée dans le futur")

    if recorded_at < now - timedelta(minutes=5):
        raise HTTPException(422, "Position GPS trop ancienne")

    point = GPSHybridPosition(
        vehicle_id=vehicle_id,
        device_id=None,
        source="PHONE",
        latitude=payload.latitude,
        longitude=payload.longitude,
        speed=payload.speed,
        recorded_at=recorded_at,
        received_at=now,
    )

    db.add(point)

    try:
        db.commit()
        db.refresh(point)
    except Exception:
        db.rollback()
        raise

    return {
        "id": point.id,
        "vehicle_id": point.vehicle_id,
        "source": point.source,
        "recorded_at": point.recorded_at,
        "status": "RECORDED",
    }
