from datetime import datetime
from pydantic import BaseModel,Field
from .models import Role
class Login(BaseModel): username:str; password:str
class UserIn(BaseModel): username:str; password:str=Field(min_length=8); role:Role
class CountryIn(BaseModel): code:str=Field(min_length=2,max_length=2); name:str; currency:str=Field(min_length=3,max_length=3)
class LineIn(BaseModel): country_id:int; code:str; name:str; fare:int=Field(gt=0)
class VehicleIn(BaseModel):
    country_id: int
    code: str
    plate: str
    capacity: int = Field(gt=0)

    status: str = "ACTIVE"

    brand: str | None = None
    model: str | None = None
    year: int | None = Field(default=None, ge=1980, le=2100)
    mileage: int = Field(default=0, ge=0)


class VehicleUpdate(BaseModel):
    country_id: int | None = None
    code: str | None = None
    plate: str | None = None
    capacity: int | None = Field(default=None, gt=0)

    status: str | None = None

    brand: str | None = None
    model: str | None = None
    year: int | None = Field(default=None, ge=1980, le=2100)
    mileage: int | None = Field(default=None, ge=0)


class DriverIn(BaseModel):
    country_id: int
    employee_code: str
    first_name: str
    last_name: str
    phone: str | None = None
    license_number: str
    status: str = "ACTIVE"


class DriverUpdate(BaseModel):
    country_id: int | None = None
    employee_code: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    license_number: str | None = None
    status: str | None = None


class DriverAssignmentIn(BaseModel):
    driver_id: int
    vehicle_id: int
class TripIn(BaseModel):
    line_id: int
    vehicle_id: int
    departure_at: datetime

    driver_id: int | None = None
    notes: str | None = Field(default=None, max_length=500)

class TripStartIn(BaseModel):
    start_mileage: int = Field(ge=0)


class TripCompleteIn(BaseModel):
    end_mileage: int = Field(ge=0)


class TripCancelIn(BaseModel):
    notes: str | None = Field(default=None, max_length=500)

class TicketIn(BaseModel): trip_id:int
class PaymentIn(BaseModel): provider:str="SIMULATOR"; simulate_success:bool=True
class ValidateIn(BaseModel): code:str; signature:str
class GPSIn(BaseModel): vehicle_id:int; latitude:float=Field(ge=-90,le=90); longitude:float=Field(ge=-180,le=180); speed:float=0
class MaintenanceIn(BaseModel):
    vehicle_id: int
    description: str
    maintenance_type: str | None = None

    cost: int = Field(default=0, ge=0)
    mileage: int | None = Field(default=None, ge=0)

    scheduled_at: datetime | None = None
    next_maintenance_at: datetime | None = None

    status: str = "PLANNED"


class MaintenanceUpdate(BaseModel):
    description: str | None = None
    maintenance_type: str | None = None

    cost: int | None = Field(default=None, ge=0)
    mileage: int | None = Field(default=None, ge=0)

    scheduled_at: datetime | None = None
    completed_at: datetime | None = None
    next_maintenance_at: datetime | None = None

    status: str | None = None
    done: bool | None = None


class FuelIn(BaseModel):
    vehicle_id: int
    driver_id: int | None = None

    liters: float = Field(gt=0)
    cost: int = Field(ge=0)

    mileage: int | None = Field(default=None, ge=0)

class FuelUpdate(BaseModel):
    driver_id: int | None = None
    liters: float | None = Field(default=None, gt=0)
    cost: int | None = Field(default=None, ge=0)
    mileage: int | None = Field(default=None, ge=0)

class CashSessionOpenIn(BaseModel):
    opening_amount: int = Field(default=0, ge=0)
    notes: str | None = Field(default=None, max_length=500)


class CashSessionCloseIn(BaseModel):
    declared_amount: int = Field(ge=0)
    notes: str | None = Field(default=None, max_length=500)
