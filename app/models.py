from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import String,Integer,Float,DateTime,ForeignKey,Enum as SAEnum,Boolean
from sqlalchemy.orm import Mapped,mapped_column,relationship
from sqlalchemy import UniqueConstraint, Identity, func
from .db import Base
def now(): return datetime.now(timezone.utc)
class Role(str,Enum): ADMIN="ADMIN"; COUNTRY_MANAGER="COUNTRY_MANAGER"; CONTROLLER="CONTROLLER"; DRIVER="DRIVER"; AGENT="AGENT"
class TicketStatus(str,Enum): PENDING="PENDING"; PAID="PAID"; USED="USED"; EXPIRED="EXPIRED"; CANCELLED="CANCELLED"
class PaymentStatus(str,Enum): PENDING="PENDING"; SUCCESS="SUCCESS"; FAILED="FAILED"
class Country(Base):
 __tablename__="countries"; id:Mapped[int]=mapped_column(primary_key=True); code:Mapped[str]=mapped_column(String(2),unique=True); name:Mapped[str]=mapped_column(String(80)); currency:Mapped[str]=mapped_column(String(3))
# V5.7 : is_active interdit la connexion ; token_version invalide les anciens JWT.
# Les colonnes doivent être ajoutées par la migration SQL AVANT le redémarrage API.
class User(Base):
 __tablename__="users"; id:Mapped[int]=mapped_column(primary_key=True); username:Mapped[str]=mapped_column(String(80),unique=True,index=True); password_hash:Mapped[str]=mapped_column(String(255)); role:Mapped[Role]=mapped_column(SAEnum(Role)); is_active:Mapped[bool]=mapped_column(Boolean,default=True,nullable=False); token_version:Mapped[int]=mapped_column(Integer,default=0,nullable=False); country_id:Mapped[int | None]=mapped_column(ForeignKey("countries.id"),nullable=True); country=relationship("Country")
class Line(Base):
 __tablename__="lines"; id:Mapped[int]=mapped_column(primary_key=True); country_id:Mapped[int]=mapped_column(ForeignKey("countries.id")); code:Mapped[str]=mapped_column(String(30),unique=True); name:Mapped[str]=mapped_column(String(120)); fare:Mapped[int]=mapped_column(Integer); country=relationship("Country")
class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"))

    code: Mapped[str] = mapped_column(String(30), unique=True)
    plate: Mapped[str] = mapped_column(String(40), unique=True)
    capacity: Mapped[int] = mapped_column(Integer)
    standing_capacity: Mapped[int] = mapped_column(
    Integer,
    nullable=False,
    default=0
    )

    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")

    brand: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mileage: Mapped[int] = mapped_column(Integer, default=0)

    country = relationship("Country")

class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(primary_key=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"))
    user_id: Mapped[int | None] = mapped_column(
    ForeignKey("users.id"),
    unique=True,
    nullable=True
    )

    employee_code: Mapped[str] = mapped_column(String(30), unique=True)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))

    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)

    license_number: Mapped[str] = mapped_column(
        String(80),
        unique=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="ACTIVE"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now
    )

    country = relationship("Country")


class DriverAssignment(Base):
    __tablename__ = "driver_assignments"

    id: Mapped[int] = mapped_column(primary_key=True)

    driver_id: Mapped[int] = mapped_column(
        ForeignKey("drivers.id")
    )

    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id")
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    driver = relationship("Driver")
    vehicle = relationship("Vehicle")

class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(primary_key=True)

    line_id: Mapped[int] = mapped_column(
        ForeignKey("lines.id")
    )

    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id")
    )

    driver_id: Mapped[int | None] = mapped_column(
        ForeignKey("drivers.id"),
        nullable=True
    )

    departure_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="SCHEDULED"
    )

    actual_departure_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    actual_arrival_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    start_mileage: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    end_mileage: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    line = relationship("Line")
    vehicle = relationship("Vehicle")
    driver = relationship("Driver")
class Ticket(Base):
 __tablename__="tickets"; id:Mapped[int]=mapped_column(primary_key=True); code:Mapped[str]=mapped_column(String(80),unique=True,index=True); trip_id:Mapped[int]=mapped_column(ForeignKey("trips.id")); amount:Mapped[int]=mapped_column(Integer); status:Mapped[TicketStatus]=mapped_column(SAEnum(TicketStatus),default=TicketStatus.PENDING); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); expires_at:Mapped[datetime]=mapped_column(DateTime(timezone=True)); used_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True); trip=relationship("Trip")
class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"))
    provider: Mapped[str] = mapped_column(String(40))
    reference: Mapped[str] = mapped_column(String(100), unique=True)
    amount: Mapped[int] = mapped_column(Integer)
    status: Mapped[PaymentStatus] = mapped_column(SAEnum(PaymentStatus))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    cash_session_id: Mapped[int | None] = mapped_column(ForeignKey("cash_sessions.id"), nullable=True)
    user = relationship("User")
    cash_session = relationship("CashSession")

class CashSession(Base):
    __tablename__ = "cash_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    opening_amount: Mapped[int] = mapped_column(Integer, default=0)

    expected_amount: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )
    declared_amount: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )
    difference_amount: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="OPEN"
    )

    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    user = relationship("User")

class GPSPosition(Base):
 __tablename__="gps_positions"; id:Mapped[int]=mapped_column(primary_key=True); vehicle_id:Mapped[int]=mapped_column(ForeignKey("vehicles.id")); latitude:Mapped[float]=mapped_column(Float); longitude:Mapped[float]=mapped_column(Float); speed:Mapped[float]=mapped_column(Float,default=0); recorded_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class Maintenance(Base):
    __tablename__ = "maintenance"

    id: Mapped[int] = mapped_column(primary_key=True)

    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id")
    )

    description: Mapped[str] = mapped_column(String(255))
    cost: Mapped[int] = mapped_column(Integer, default=0)
    done: Mapped[bool] = mapped_column(Boolean, default=False)

    maintenance_type: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True
    )

    mileage: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    next_maintenance_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="PLANNED"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now
    )

    vehicle = relationship("Vehicle")


class Fuel(Base):
    __tablename__ = "fuel"

    id: Mapped[int] = mapped_column(primary_key=True)

    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id")
    )

    driver_id: Mapped[int | None] = mapped_column(
        ForeignKey("drivers.id"),
        nullable=True
    )

    liters: Mapped[float] = mapped_column(Float)

    cost: Mapped[int] = mapped_column(Integer)

    mileage: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now
    )

    vehicle = relationship("Vehicle")
    driver = relationship("Driver")
class Audit(Base):
 __tablename__="audit"; id:Mapped[int]=mapped_column(primary_key=True); username:Mapped[str]=mapped_column(String(80)); action:Mapped[str]=mapped_column(String(100)); target:Mapped[str]=mapped_column(String(100)); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)


class CashSessionRectification(Base):
    """Historique immuable des rectifications administratives de caisse."""
    __tablename__ = "cash_session_rectifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    cash_session_id: Mapped[int] = mapped_column(ForeignKey("cash_sessions.id"), nullable=False)
    admin_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    old_declared_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    new_declared_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    old_difference_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    new_difference_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)


class TripController(Base):
    __tablename__ = "trip_controllers"

    __table_args__ = (
        UniqueConstraint(
            "trip_id",
            "controller_id",
            name="uq_trip_controller"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        Identity(),
        primary_key=True
    )

    trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id"),
        nullable=False
    )

    controller_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    trip = relationship("Trip")
    controller = relationship("User")
