from .gps.fleet_api import router as gps_fleet_router
from .gps.live_api import router as gps_live_router
from .gps.device_api import router as gps_device_router
from .gps.phone_api import router as gps_phone_router

from .payment_breakdown import calculer_recettes_par_provider
import os,uuid
from contextlib import asynccontextmanager
from .startup_config_step68 import validate_startup_config, validate_loaded_jwt_secret
from .jwt_runtime_config_step79 import validate_loaded_jwt_runtime_config
from .jwt_startup_diagnostics_step80 import validate_jwt_startup_safely
from datetime import datetime,timedelta,timezone,date
from zoneinfo import ZoneInfo
from io import BytesIO
# BibliothÃƒÆ’Ã‚Â¨ques pour gÃƒÆ’Ã‚Â©nÃƒÆ’Ã‚Â©rer les rapports Excel.
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
# Fin BibliothÃƒÆ’Ã‚Â¨ques pour gÃƒÆ’Ã‚Â©nÃƒÆ’Ã‚Â©rer les rapports Excel.
import qrcode
from fastapi import FastAPI,Depends,HTTPException,Query
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from .db import Base,engine,get_db,SessionLocal
from .models import *
from .schemas import *
from .security import pwd,token,roles,sign_qr,check_qr,utilisateur_optionnel,verifier_acces_pays
from .login_throttle_step82 import is_blocked, record_failure, clear_failures
from . import login_throttle_shared_step83 as shared_throttle
from . import login_ip_step84 as ip_throttle
from . import login_audit_step85 as login_audit
from fastapi import Request
from .v59 import router as v59_router, Boarding59, OnboardSale59, Pass59
# GÃƒÆ’Ã‚Â©nÃƒÆ’Ã‚Â©rateur des rapports financiers PDF.
from .pdf_reports import generer_rapport_caisse
from .finance_dashboard import router as finance_router
from .finance_audit import router as finance_audit_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Valider les paramÃƒÆ’Ã‚Â¨tres avant toute session ou ÃƒÆ’Ã‚Â©criture.
    validate_jwt_startup_safely(validate_startup_config, validate_loaded_jwt_runtime_config)
    app.state.login_redis = shared_throttle.validate_redis_config()
    # Conserver le seed explicitement opt-in ; aucune migration implicite.
    seed()
    yield

app=FastAPI(title="Boukoulou Transport",version="1.0.0",lifespan=lifespan)
app.include_router(v59_router)

# Activer le tableau de bord financier rÃƒÆ’Ã‚Â©servÃƒÆ’Ã‚Â© aux administrateurs.
app.include_router(finance_router)
# Activer le contrÃƒÆ’Ã‚Â´le des anomalies financiÃƒÆ’Ã‚Â¨res.
app.include_router(finance_audit_router)
app.mount("/static", StaticFiles(directory="ui"), name="static")
@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse("ui/index.html")
# Ne jamais crÃƒÆ’Ã‚Â©er/modifier les tables pendant l'import de l'API.
# Les migrations sont gÃƒÆ’Ã‚Â©rÃƒÆ’Ã‚Â©es sÃƒÆ’Ã‚Â©parÃƒÆ’Ã‚Â©ment, aprÃƒÆ’Ã‚Â¨s vÃƒÆ’Ã‚Â©rification et sauvegarde.

def save(db,obj):
 try: db.add(obj); db.commit(); db.refresh(obj); return obj
 except IntegrityError: db.rollback(); raise HTTPException(409,"DonnÃƒÆ’Ã‚Â©e dÃƒÆ’Ã‚Â©jÃƒÆ’Ã‚Â  existante ou incohÃƒÆ’Ã‚Â©rente")
def audit(db,u,a,t): db.add(Audit(username=u.username,action=a,target=t)); db.commit()
def seed():
 # AmorÃƒÆ’Ã‚Â§age EXPLICITE rÃƒÆ’Ã‚Â©servÃƒÆ’Ã‚Â© aux environnements de dÃƒÆ’Ã‚Â©veloppement.
 # DÃƒÆ’Ã‚Â©sactivÃƒÆ’Ã‚Â© par dÃƒÆ’Ã‚Â©faut pour ÃƒÆ’Ã‚Â©viter des ÃƒÆ’Ã‚Â©critures au dÃƒÆ’Ã‚Â©marrage.
 if os.getenv("BOUKOULOU_ENABLE_DEV_SEED") != "1":
  return
 # ÃƒÆ’Ã¢â‚¬Â°tape 67 : double consentement explicite, jamais de seed en test/production.
 environment = os.getenv("BOUKOULOU_ENV", "").strip().lower()
 if environment != "development":
  raise RuntimeError("Seed interdit : BOUKOULOU_ENV=development est obligatoire")
 db=SessionLocal()
 try:
  admin_username = os.environ["ADMIN_USERNAME"]
  admin_password = os.environ["ADMIN_PASSWORD"]

  if not admin_username.strip() or not admin_password.strip():
    raise RuntimeError("ADMIN_USERNAME et ADMIN_PASSWORD doivent etre renseignes")

  if not db.query(User).filter_by(username=admin_username).first():
    db.add(User(
     username=admin_username,
     password_hash=pwd.hash(admin_password),
     role=Role.ADMIN
    ))
  if not db.query(Country).filter_by(code="CG").first(): db.add(Country(code="CG",name="Congo-Brazzaville",currency="XAF"))
  if not db.query(Country).filter_by(code="GA").first(): db.add(Country(code="GA",name="Gabon",currency="XAF"))
  db.commit()
 except Exception:
  # ÃƒÆ’Ã¢â‚¬Â°chec dÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢amorÃƒÆ’Ã‚Â§age : annuler la transaction avant de libÃƒÆ’Ã‚Â©rer la session.
  db.rollback()
  raise
 finally:
  db.close()
@app.get("/health")
def health(): return {"status":"ok"}
@app.post("/auth/login")
def login(x:Login,db:Session=Depends(get_db),request:Request=None):
 # RÃƒÆ’Ã‚Â©ponse gÃƒÆ’Ã‚Â©nÃƒÆ’Ã‚Â©rique pour ne pas rÃƒÆ’Ã‚Â©vÃƒÆ’Ã‚Â©ler l'existence d'un compte.
 try:
  if request is not None and shared_throttle.redis_url():
   blocked = shared_throttle.is_blocked(request.app.state.login_redis,x.username,request) or ip_throttle.redis_is_blocked(request.app.state.login_redis,request)
  else:
   blocked = is_blocked(x.username) or (request is not None and ip_throttle.is_blocked(request))
 except RuntimeError:
  login_audit.emit("login_backend_unavailable",x.username,request, "backend_error")
  raise HTTPException(503,"Service de connexion temporairement indisponible")
 if blocked:
  login_audit.emit("login_blocked",x.username,request)
  raise HTTPException(429,"Trop de tentatives. RÃƒÆ’Ã‚Â©essayez plus tard.",headers={"Retry-After":"900"})
 u=db.query(User).filter_by(username=x.username).first()
 password_ok = pwd.verify(x.password,u.password_hash) if u and u.is_active else False
 if not u or not u.is_active or not password_ok:
  try:
   if request is not None and shared_throttle.redis_url():
    shared_throttle.record_failure(request.app.state.login_redis,x.username,request)
    ip_throttle.redis_record_failure(request.app.state.login_redis,request)
   else:
    record_failure(x.username)
    if request is not None: ip_throttle.record_failure(request)
  except RuntimeError:
   login_audit.emit("login_backend_unavailable",x.username,request, "backend_error")
   raise HTTPException(503,"Service de connexion temporairement indisponible")
  login_audit.emit("login_failed",x.username,request,"invalid_credentials")
  raise HTTPException(401,"Identifiants invalides",headers={"WWW-Authenticate":"Bearer"})
 try:
  if request is not None and shared_throttle.redis_url():
   shared_throttle.clear_failures(request.app.state.login_redis,x.username,request)
  else:
   clear_failures(x.username)
 except RuntimeError:
  login_audit.emit("login_backend_unavailable",x.username,request, "backend_error")
  raise HTTPException(503,"Service de connexion temporairement indisponible")
 login_audit.emit("login_succeeded",x.username,request)
 audit(db,u,"LOGIN",u.username)
 return {"access_token":token(u),"token_type":"bearer","role":u.role.value}
@app.get("/auth/me")
def auth_me(u=Depends(roles("ADMIN", "AGENT", "CONTROLLER", "DRIVER", "COUNTRY_MANAGER"))):
    return {"id": u.id, "username": u.username, "role": u.role.value, "is_active": u.is_active, "country_id": u.country_id}

@app.get("/admin/security/login-alerts")
def admin_login_alerts(
    limit: int = Query(50, ge=1, le=200),
    scope: str | None = Query(None, pattern="^(user_ref|client_ref)$"),
    since: datetime | None = None,
    until: datetime | None = None,
    before_id: int | None = Query(None, ge=1),
    admin=Depends(roles("ADMIN")),
):
    """Filtrer les alertes locales, sans exposer les identifiants bruts."""
    from . import security_alert_storage_step89 as storage
    from .security_alert_registry_step87 import recent as local_recent
    try:
        alerts = (storage.recent if storage.enabled() else local_recent)(limit, scope=scope, since=since, until=until, before_id=before_id)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"alerts": alerts, "scope": "database" if storage.enabled() else "local_process", "persistent": storage.enabled()}

@app.get("/admin/security/purge-runs")
def admin_security_purge_runs(
    limit: int = Query(50, ge=1, le=200),
    before_id: int | None = Query(None, ge=1),
    admin=Depends(roles("ADMIN")),
):
    """Historique SQL des exÃƒÆ’Ã‚Â©cutions planifiÃƒÆ’Ã‚Â©es, administrateurs uniquement."""
    from .security_alert_purge_history_step92 import recent
    try:
        records = recent(limit=limit, before_id=before_id)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"runs": records, "persistent": True}

@app.get("/users")
def list_users(u=Depends(roles("ADMIN")), db: Session=Depends(get_db)):
    return [{"id": x.id, "username": x.username, "role": x.role.value, "is_active": x.is_active}
            for x in db.query(User).order_by(User.id).all()]

@app.post("/users", status_code=201)
def users(x:UserIn,u=Depends(roles("ADMIN")),db:Session=Depends(get_db)):
    created=save(db,User(username=x.username,password_hash=pwd.hash(x.password),role=x.role))
    audit(db,u,"CREATE_USER",created.username)
    return {"id":created.id,"username":created.username,"role":created.role.value}
# ============================================================
# V5.7 - ADMINISTRATION DES COMPTES
# ============================================================
# Les endpoints sont rÃƒÆ’Ã‚Â©servÃƒÆ’Ã‚Â©s ÃƒÆ’Ã‚Â  ADMIN, mÃƒÆ’Ã‚Âªme si l'interface masque le menu.
# Chaque changement de droits incrÃƒÆ’Ã‚Â©mente token_version : les anciens JWT
# deviennent immÃƒÆ’Ã‚Â©diatement inutilisables sur toutes les routes protÃƒÆ’Ã‚Â©gÃƒÆ’Ã‚Â©es.

from pydantic import BaseModel, Field

class UserRoleChange(BaseModel):
    role: Role

class UserPasswordReset(BaseModel):
    password: str = Field(min_length=12, max_length=128)


def _managed_user(db: Session, user_id: int):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "Utilisateur introuvable")
    return target


@app.patch("/users/{user_id}/role")
def change_user_role(user_id: int, data: UserRoleChange,
                     admin=Depends(roles("ADMIN")), db: Session=Depends(get_db)):
    target = _managed_user(db, user_id)
    # EmpÃƒÆ’Ã‚Âªche la perte accidentelle du dernier accÃƒÆ’Ã‚Â¨s admin via son propre compte.
    if target.id == admin.id and data.role != Role.ADMIN:
        raise HTTPException(409, "Vous ne pouvez pas retirer votre propre rÃƒÆ’Ã‚Â´le administrateur")
    previous = target.role.value
    if target.role != data.role:
        target.role = data.role
        target.token_version += 1
        db.commit()
        audit(db, admin, "USER_ROLE_CHANGED", f"{target.username}:{previous}->{data.role.value}")
    return {"id": target.id, "username": target.username, "role": target.role.value,
            "is_active": target.is_active}


@app.patch("/users/{user_id}/status")
def change_user_status(user_id: int, active: bool,
                       admin=Depends(roles("ADMIN")), db: Session=Depends(get_db)):
    target = _managed_user(db, user_id)
    if target.id == admin.id and not active:
        raise HTTPException(409, "Vous ne pouvez pas dÃƒÆ’Ã‚Â©sactiver votre propre compte")
    if target.is_active != active:
        target.is_active = active
        target.token_version += 1
        db.commit()
        audit(db, admin, "USER_ACTIVATED" if active else "USER_DEACTIVATED", target.username)
    return {"id": target.id, "username": target.username, "role": target.role.value,
            "is_active": target.is_active}


@app.post("/users/{user_id}/reset-password")
def reset_user_password(user_id: int, data: UserPasswordReset,
                        admin=Depends(roles("ADMIN")), db: Session=Depends(get_db)):
    target = _managed_user(db, user_id)
    # Ne jamais enregistrer le mot de passe en clair dans l'audit ni la rÃƒÆ’Ã‚Â©ponse.
    target.password_hash = pwd.hash(data.password)
    target.token_version += 1
    db.commit()
    audit(db, admin, "USER_PASSWORD_RESET", target.username)
    return {"message": "Mot de passe mis ÃƒÆ’Ã‚Â  jour ; sessions prÃƒÆ’Ã‚Â©cÃƒÆ’Ã‚Â©dentes invalidÃƒÆ’Ã‚Â©es",
            "id": target.id}


@app.get("/users/audit")
def users_audit(limit: int = 100, admin=Depends(roles("ADMIN")),
                db: Session=Depends(get_db)):
    # Limite bornÃƒÆ’Ã‚Â©e pour ÃƒÆ’Ã‚Â©viter de charger tout l'historique en mÃƒÆ’Ã‚Â©moire.
    limit = max(1, min(limit, 500))
    records = db.query(Audit).order_by(Audit.id.desc()).limit(limit).all()
    return [{"id": a.id, "username": a.username, "action": a.action,
             "target": a.target, "created_at": a.created_at} for a in records]


@app.get("/countries")
def countries(u=Depends(roles("ADMIN", "COUNTRY_MANAGER", "AGENT", "CONTROLLER", "DRIVER")), db:Session=Depends(get_db)):
    # Un responsable national ne voit que son pays.
    query = db.query(Country)
    if u.role.value == "COUNTRY_MANAGER":
        if u.country_id is None:
            raise HTTPException(status_code=403, detail="Pays d'affectation manquant")
        query = query.filter(Country.id == u.country_id)
    return query.all()
@app.post("/countries")
def country(x:CountryIn,u=Depends(roles("ADMIN")),db:Session=Depends(get_db)): return save(db,Country(**x.model_dump()))
@app.post("/lines")
def line(x:LineIn,u=Depends(roles("ADMIN")),db:Session=Depends(get_db)):
 if not db.get(Country,x.country_id): raise HTTPException(404,"Pays introuvable")
 return save(db,Line(**x.model_dump()))
@app.get("/lines")
def lines(u=Depends(roles("ADMIN", "COUNTRY_MANAGER", "AGENT", "CONTROLLER", "DRIVER")), db: Session = Depends(get_db)):
    # Restreindre les lignes aux responsables nationaux authentifiÃƒÆ’Ã‚Â©s.
    query = db.query(Line)
    if u is not None and u.role.value == "COUNTRY_MANAGER":
        if u.country_id is None:
            raise HTTPException(status_code=403, detail="Responsable national sans pays d'affectation")
        query = query.filter(Line.country_id == u.country_id)
    return query.all()
@app.post("/vehicles")
def vehicle(x:VehicleIn,u=Depends(roles("ADMIN")),db:Session=Depends(get_db)):
 if not db.get(Country,x.country_id): raise HTTPException(404,"Pays introuvable")
 return save(db,Vehicle(**x.model_dump()))
@app.get("/vehicles")
def vehicles(u=Depends(roles("ADMIN", "COUNTRY_MANAGER", "AGENT", "CONTROLLER", "DRIVER")), db: Session = Depends(get_db)):
    # Restreindre les vÃƒÆ’Ã‚Â©hicules aux responsables nationaux authentifiÃƒÆ’Ã‚Â©s.
    query = db.query(Vehicle)
    if u is not None and u.role.value == "COUNTRY_MANAGER":
        if u.country_id is None:
            raise HTTPException(status_code=403, detail="Responsable national sans pays d'affectation")
        query = query.filter(Vehicle.country_id == u.country_id)
    return query.all()

# ============================================================
# V4 - GESTION DU PARC ET DES CHAUFFEURS
# ============================================================

@app.get("/vehicles/{vehicle_id}")
def get_vehicle(
    vehicle_id: int,
    u=Depends(roles("ADMIN", "CONTROLLER", "DRIVER")),
    db: Session = Depends(get_db)
):
    v = db.get(Vehicle, vehicle_id)

    if not v:
        raise HTTPException(404, "VÃƒÆ’Ã‚Â©hicule introuvable")

    return v


@app.put("/vehicles/{vehicle_id}")
def update_vehicle(
    vehicle_id: int,
    x: VehicleUpdate,
    u=Depends(roles("ADMIN")),
    db: Session = Depends(get_db)
):
    v = db.get(Vehicle, vehicle_id)

    if not v:
        raise HTTPException(404, "VÃƒÆ’Ã‚Â©hicule introuvable")

    data = x.model_dump(exclude_unset=True)

    if "country_id" in data:
        if not db.get(Country, data["country_id"]):
            raise HTTPException(404, "Pays introuvable")

    for field, value in data.items():
        setattr(v, field, value)

    try:
        db.commit()
        db.refresh(v)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409,
            "Code vÃƒÆ’Ã‚Â©hicule ou plaque dÃƒÆ’Ã‚Â©jÃƒÆ’Ã‚Â  utilisÃƒÆ’Ã‚Â©"
        )

    audit(db, u, "UPDATE_VEHICLE", v.code)

    return v


# ============================================================
# CHAUFFEURS
# ============================================================

@app.get("/drivers")
def list_drivers(
    u=Depends(roles("ADMIN", "CONTROLLER")),
    db: Session = Depends(get_db)
):
    return db.query(Driver).order_by(Driver.id.desc()).all()


@app.post("/drivers")
def create_driver(
    x: DriverIn,
    u=Depends(roles("ADMIN")),
    db: Session = Depends(get_db)
):
    if not db.get(Country, x.country_id):
        raise HTTPException(404, "Pays introuvable")

    driver = Driver(**x.model_dump())

    try:
        db.add(driver)
        db.commit()
        db.refresh(driver)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409,
            "Matricule ou numÃƒÆ’Ã‚Â©ro de permis dÃƒÆ’Ã‚Â©jÃƒÆ’Ã‚Â  utilisÃƒÆ’Ã‚Â©"
        )

    audit(db, u, "CREATE_DRIVER", driver.employee_code)

    return driver


@app.get("/drivers/{driver_id}")
def get_driver(
    driver_id: int,
    u=Depends(roles("ADMIN", "CONTROLLER")),
    db: Session = Depends(get_db)
):
    driver = db.get(Driver, driver_id)

    if not driver:
        raise HTTPException(404, "Chauffeur introuvable")

    return driver


@app.put("/drivers/{driver_id}")
def update_driver(
    driver_id: int,
    x: DriverUpdate,
    u=Depends(roles("ADMIN")),
    db: Session = Depends(get_db)
):
    driver = db.get(Driver, driver_id)

    if not driver:
        raise HTTPException(404, "Chauffeur introuvable")

    data = x.model_dump(exclude_unset=True)

    if "country_id" in data:
        if not db.get(Country, data["country_id"]):
            raise HTTPException(404, "Pays introuvable")

    for field, value in data.items():
        setattr(driver, field, value)

    try:
        db.commit()
        db.refresh(driver)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409,
            "Matricule ou numÃƒÆ’Ã‚Â©ro de permis dÃƒÆ’Ã‚Â©jÃƒÆ’Ã‚Â  utilisÃƒÆ’Ã‚Â©"
        )

    audit(db, u, "UPDATE_DRIVER", driver.employee_code)

    return driver


# ============================================================
# AFFECTATIONS CHAUFFEUR -> VEHICULE
# ============================================================

@app.get("/driver-assignments")
def list_driver_assignments(
    u=Depends(roles("ADMIN", "CONTROLLER")),
    db: Session = Depends(get_db)
):
    rows = (
        db.query(DriverAssignment)
        .order_by(DriverAssignment.id.desc())
        .all()
    )

    return [{
        "id": a.id,
        "driver_id": a.driver_id,
        "driver": (
            f"{a.driver.first_name} {a.driver.last_name}"
            if a.driver else None
        ),
        "vehicle_id": a.vehicle_id,
        "vehicle": (
            f"{a.vehicle.code} - {a.vehicle.plate}"
            if a.vehicle else None
        ),
        "started_at": a.started_at,
        "ended_at": a.ended_at,
        "active": a.active
    } for a in rows]


@app.post("/driver-assignments")
def create_driver_assignment(
    x: DriverAssignmentIn,
    u=Depends(roles("ADMIN")),
    db: Session = Depends(get_db)
):
    driver = db.get(Driver, x.driver_id)

    if not driver:
        raise HTTPException(404, "Chauffeur introuvable")

    vehicle = db.get(Vehicle, x.vehicle_id)

    if not vehicle:
        raise HTTPException(404, "VÃƒÆ’Ã‚Â©hicule introuvable")

    if driver.status != "ACTIVE":
        raise HTTPException(
            409,
            "Le chauffeur n'est pas actif"
        )

    if vehicle.status != "ACTIVE":
        raise HTTPException(
            409,
            "Le vÃƒÆ’Ã‚Â©hicule n'est pas actif"
        )

    # Un chauffeur ne peut avoir qu'une affectation active.
    existing_driver = (
        db.query(DriverAssignment)
        .filter(
            DriverAssignment.driver_id == driver.id,
            DriverAssignment.active == True
        )
        .first()
    )

    if existing_driver:
        raise HTTPException(
            409,
            "Ce chauffeur possÃƒÆ’Ã‚Â¨de dÃƒÆ’Ã‚Â©jÃƒÆ’Ã‚Â  une affectation active"
        )

    # Un vÃƒÆ’Ã‚Â©hicule ne peut avoir qu'un chauffeur actif.
    existing_vehicle = (
        db.query(DriverAssignment)
        .filter(
            DriverAssignment.vehicle_id == vehicle.id,
            DriverAssignment.active == True
        )
        .first()
    )

    if existing_vehicle:
        raise HTTPException(
            409,
            "Ce vÃƒÆ’Ã‚Â©hicule possÃƒÆ’Ã‚Â¨de dÃƒÆ’Ã‚Â©jÃƒÆ’Ã‚Â  un chauffeur actif"
        )

    assignment = DriverAssignment(
        driver_id=driver.id,
        vehicle_id=vehicle.id
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    audit(
        db,
        u,
        "ASSIGN_DRIVER",
        f"{driver.employee_code}->{vehicle.code}"
    )

    return {
        "id": assignment.id,
        "driver_id": driver.id,
        "driver": f"{driver.first_name} {driver.last_name}",
        "vehicle_id": vehicle.id,
        "vehicle": f"{vehicle.code} - {vehicle.plate}",
        "started_at": assignment.started_at,
        "active": assignment.active
    }


@app.put("/driver-assignments/{assignment_id}/end")
def end_driver_assignment(
    assignment_id: int,
    u=Depends(roles("ADMIN")),
    db: Session = Depends(get_db)
):
    assignment = db.get(DriverAssignment, assignment_id)

    if not assignment:
        raise HTTPException(404, "Affectation introuvable")

    if not assignment.active:
        raise HTTPException(
            409,
            "Cette affectation est dÃƒÆ’Ã‚Â©jÃƒÆ’Ã‚Â  terminÃƒÆ’Ã‚Â©e"
        )

    assignment.active = False
    assignment.ended_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(assignment)

    audit(
        db,
        u,
        "END_DRIVER_ASSIGNMENT",
        str(assignment.id)
    )

    return {
        "id": assignment.id,
        "driver_id": assignment.driver_id,
        "vehicle_id": assignment.vehicle_id,
        "started_at": assignment.started_at,
        "ended_at": assignment.ended_at,
        "active": assignment.active
    }
# ============================================================
# V5 - EXPLOITATION DES COURSES
# ============================================================

@app.post("/trips")
def create_trip(
    x: TripIn,
    u=Depends(roles("ADMIN")),
    db: Session = Depends(get_db)
):
    line = db.get(Line, x.line_id)

    if not line:
        raise HTTPException(404, "Ligne introuvable")

    vehicle = db.get(Vehicle, x.vehicle_id)

    if not vehicle:
        raise HTTPException(404, "VÃƒÆ’Ã‚Â©hicule introuvable")

    if vehicle.status != "ACTIVE":
        raise HTTPException(
            409,
            f"Le vÃƒÆ’Ã‚Â©hicule n'est pas disponible : {vehicle.status}"
        )
    # ========================================================
    # SECURITE : COHERENCE GEOGRAPHIQUE DU VEHICULE
    # Le vehicule doit appartenir au pays de la ligne.
    # ========================================================

    if vehicle.country_id != line.country_id:
        raise HTTPException(
            status_code=409,
            detail="Le vehicule et la ligne appartiennent a des pays differents"
        )

    driver = None

    if x.driver_id is not None:
        driver = db.get(Driver, x.driver_id)

        if not driver:
            raise HTTPException(404, "Chauffeur introuvable")

        if driver.status != "ACTIVE":
            raise HTTPException(
                409,
                "Le chauffeur n'est pas actif"
            )
           # ====================================================
        # SECURITE : COHERENCE GEOGRAPHIQUE DU CHAUFFEUR
        # Le chauffeur doit appartenir au pays de la ligne.
        # ====================================================

        if driver.country_id != line.country_id:
            raise HTTPException(
                status_code=409,
                detail="Le chauffeur et la ligne appartiennent a des pays differents"
            )

    trip = Trip(
        line_id=x.line_id,
        vehicle_id=x.vehicle_id,
        driver_id=x.driver_id,
        departure_at=x.departure_at,
        status="SCHEDULED",
        notes=x.notes
    )

    db.add(trip)
    db.commit()
    db.refresh(trip)

    audit(db, u, "CREATE_TRIP", str(trip.id))

    return trip


# ============================================================
# SECURITE : AFFECTATIONS DES COURSES
# ============================================================

def filtrer_courses_utilisateur(query, u, db: Session):
    role = u.role.value

    if role == "COUNTRY_MANAGER":
        if u.country_id is None:
            raise HTTPException(
                status_code=403,
                detail="Responsable national sans pays d'affectation"
            )

        return query.join(
            Line, Trip.line_id == Line.id
        ).filter(Line.country_id == u.country_id)

    if role == "DRIVER":
        return query.filter(
            Trip.driver_id.in_(
                db.query(Driver.id).filter(
                    Driver.user_id == u.id
                )
            )
        )

    if role == "CONTROLLER":
        return query.filter(
            Trip.id.in_(
                db.query(TripController.trip_id).filter(
                    TripController.controller_id == u.id
                )
            )
        )

    return query


def verifier_acces_course(db: Session, u, trip_id: int):
    trip = filtrer_courses_utilisateur(
        db.query(Trip).filter(Trip.id == trip_id),
        u,
        db
    ).first()

    if trip is None:
        raise HTTPException(
            status_code=404,
            detail="Course introuvable"
        )

    return trip

@app.get("/trips")
def list_trips(
    u=Depends(roles("ADMIN", "COUNTRY_MANAGER", "AGENT", "CONTROLLER", "DRIVER")),
    db: Session = Depends(get_db)
):
    # Filtrer par pays sans changer les accÃƒÆ’Ã‚Â¨s des autres rÃƒÆ’Ã‚Â´les.
        # ============================================================
    # SECURITE : FILTRAGE DES COURSES SELON LE ROLE
    # ============================================================
    # ADMIN :
    #   Acces a toutes les courses.
    #
    # COUNTRY_MANAGER :
    #   Acces uniquement aux courses de son pays.
    #
    # DRIVER :
    #   Acces uniquement aux courses affectees a son compte.
    #
    # CONTROLLER :
    #   Acces uniquement aux courses affectees via trip_controllers.
    #
    # AGENT :
    #   Conservation des regles actuelles pour la vente au guichet.
    #
    # IMPORTANT :
    #   Le filtrage est applique dans PostgreSQL, pas seulement
    #   dans l'interface JavaScript.
    # ============================================================

    query = filtrer_courses_utilisateur(
        db.query(Trip),
        u,
        db
    )

    # Conserver le tri existant par date de depart decroissante.
    rows = query.order_by(
        Trip.departure_at.desc()
    ).all()

    return [{
        "id": t.id,
        "line_id": t.line_id,
        "country_id": t.line.country_id if t.line else None,
        "fare": t.line.fare if t.line else None,
        "line": (
            f"{t.line.code} - {t.line.name}"
            if t.line else None
        ),
        "vehicle_id": t.vehicle_id,
        "vehicle": (
            f"{t.vehicle.code} - {t.vehicle.plate}"
            if t.vehicle else None
        ),
        "driver_id": t.driver_id,
        "driver": (
            f"{t.driver.first_name} {t.driver.last_name}"
            if t.driver else None
        ),
        "departure_at": t.departure_at,
        "actual_departure_at": t.actual_departure_at,
        "actual_arrival_at": t.actual_arrival_at,
        "start_mileage": t.start_mileage,
        "end_mileage": t.end_mileage,
        "status": t.status,
        "notes": t.notes
    } for t in rows]


@app.get("/trips/{trip_id}")
def get_trip(
    trip_id: int,
    u=Depends(roles("ADMIN", "COUNTRY_MANAGER", "CONTROLLER", "DRIVER")),
    db: Session = Depends(get_db)
):
    #trip = db.get(Trip, trip_id)
    # ============================================================
    # SECURITE : VERIFICATION D'ACCES A UNE COURSE
    # ============================================================
    # Avant de retourner les informations de la course :
    #
    # - Verifier que la course existe.
    # - Verifier les restrictions territoriales du responsable.
    # - Verifier l'affectation du chauffeur.
    # - Verifier l'affectation du controleur.
    #
    # Une course non autorisee retourne HTTP 404.
    # Cela evite de reveler son existence.
    #
    # IMPORTANT :
    #   Les donnees retournees restent identiques pour ne pas
    #   perturber les interfaces existantes.
    # ============================================================

    trip = verifier_acces_course(db, u, trip_id)


    if not trip:
        raise HTTPException(404, "Course introuvable")

    # ContrÃƒÆ’Ã‚Â´le territorial avant de rÃƒÆ’Ã‚Â©vÃƒÆ’Ã‚Â©ler les donnÃƒÆ’Ã‚Â©es de la course.
    if u.role.value == "COUNTRY_MANAGER":
        if u.country_id is None:
            raise HTTPException(status_code=403, detail="Responsable national sans pays d'affectation")
        if trip.line is None or trip.line.country_id != u.country_id:
            raise HTTPException(status_code=404, detail="Course introuvable")

    return {
        "id": trip.id,
        "line_id": trip.line_id,
        "line": (
            f"{trip.line.code} - {trip.line.name}"
            if trip.line else None
        ),
        "vehicle_id": trip.vehicle_id,
        "vehicle": (
            f"{trip.vehicle.code} - {trip.vehicle.plate}"
            if trip.vehicle else None
        ),
        "driver_id": trip.driver_id,
        "driver": (
            f"{trip.driver.first_name} {trip.driver.last_name}"
            if trip.driver else None
        ),
        "departure_at": trip.departure_at,
        "actual_departure_at": trip.actual_departure_at,
        "actual_arrival_at": trip.actual_arrival_at,
        "start_mileage": trip.start_mileage,
        "end_mileage": trip.end_mileage,
        "status": trip.status,
        "notes": trip.notes
    }


# ============================================================
# DEMARRAGE D'UNE COURSE
# ============================================================

@app.put("/trips/{trip_id}/start")
def start_trip(
    trip_id: int,
    x: TripStartIn,
    u=Depends(roles("ADMIN", "DRIVER")),
    db: Session = Depends(get_db)
):
    # --------------------------------------------------------
    # V5.9 - ETAPE 93 : CONTROLE D'ACCES A LA COURSE
    #
    # Le chauffeur ne peut modifier que ses propres courses.
    # Une course non autorisee retourne HTTP 404.
    # --------------------------------------------------------
    trip = verifier_acces_course(db, u, trip_id)

    if trip.status != "SCHEDULED":
        raise HTTPException(
            409,
            f"Impossible de dÃƒÆ’Ã‚Â©marrer une course {trip.status}"
        )
        # --------------------------------------------------------
    # V5.1 - Protection contre un dÃƒÆ’Ã‚Â©part trop anticipÃƒÆ’Ã‚Â©
    # --------------------------------------------------------

    now_utc = datetime.now(timezone.utc)

    scheduled_departure = trip.departure_at

    # SÃƒÆ’Ã‚Â©curitÃƒÆ’Ã‚Â© au cas oÃƒÆ’Ã‚Â¹ la date rÃƒÆ’Ã‚Â©cupÃƒÆ’Ã‚Â©rÃƒÆ’Ã‚Â©e serait sans timezone
    if scheduled_departure.tzinfo is None:
        scheduled_departure = scheduled_departure.replace(
            tzinfo=timezone.utc
        )

    earliest_start = scheduled_departure - timedelta(minutes=30)

    if now_utc < earliest_start:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "TRIP_TOO_EARLY",
                "message": "Cette course ne peut pas encore ÃƒÆ’Ã‚Âªtre dÃƒÆ’Ã‚Â©marrÃƒÆ’Ã‚Â©e",
                "scheduled_departure": scheduled_departure.isoformat(),
                "earliest_start": earliest_start.isoformat()
            }
        )

    # ========================================================
    # BOUKOULOU TRANSPORT V5.9 - ETAPE 93.4.9.7.17
    #
    # Verrouillage transactionnel du vehicule.
    # Le verrou est conserve jusqu'au commit ou rollback.
    # ========================================================

    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.id == trip.vehicle_id)
        .with_for_update()
        .first()
    )

    if not vehicle:
        raise HTTPException(404, "VÃƒÆ’Ã‚Â©hicule introuvable")

    if vehicle.status != "ACTIVE":
        raise HTTPException(
            409,
            f"VÃƒÆ’Ã‚Â©hicule indisponible : {vehicle.status}"
        )

    if trip.driver_id is None:
        raise HTTPException(
            409,
            "Aucun chauffeur n'est affectÃƒÆ’Ã‚Â© ÃƒÆ’Ã‚Â  cette course"
        )

    # ========================================================
    # BOUKOULOU TRANSPORT V5.9 - ETAPE 93.4.9.7.18
    #
    # Verrouillage transactionnel du chauffeur.
    #
    # Ordre de verrouillage :
    # 1. Vehicule
    # 2. Chauffeur
    #
    # Empeche deux courses d'utiliser simultanement
    # le meme chauffeur.
    # ========================================================

    driver = (
        db.query(Driver)
        .filter(Driver.id == trip.driver_id)
        .with_for_update()
        .first()
    )

    if not driver or driver.status != "ACTIVE":
        raise HTTPException(
            409,
            "Chauffeur indisponible"
        )


    # ========================================================
    # BOUKOULOU TRANSPORT V5.9 - ETAPE 93.4.9.7.20
    #
    # Verrouiller et relire la course apres le vehicule
    # et le chauffeur.
    #
    # populate_existing=True force SQLAlchemy a actualiser
    # l'objet deja charge dans la session.
    # ========================================================

    trip = (
        db.query(Trip)
        .populate_existing()
        .filter(Trip.id == trip_id)
        .with_for_update()
        .first()
    )

    if not trip:
        raise HTTPException(
            404,
            "Course introuvable"
        )

    if trip.status != "SCHEDULED":
        raise HTTPException(
            409,
            f"Impossible de demarrer une course {trip.status}"
        )

    # Verifier que les affectations n'ont pas change.
    if trip.vehicle_id != vehicle.id or trip.driver_id != driver.id:
        raise HTTPException(
            409,
            "Les affectations de la course ont change"
        )

    if x.start_mileage < vehicle.mileage:
        raise HTTPException(
            409,
            f"KilomÃƒÆ’Ã‚Â©trage infÃƒÆ’Ã‚Â©rieur au compteur actuel ({vehicle.mileage} km)"
        )

    # EmpÃƒÆ’Ã‚Âªche le mÃƒÆ’Ã‚Âªme vÃƒÆ’Ã‚Â©hicule d'effectuer deux courses simultanÃƒÆ’Ã‚Â©ment.
    vehicle_busy = (
        db.query(Trip)
        .filter(
            Trip.vehicle_id == trip.vehicle_id,
            Trip.status == "IN_PROGRESS",
            Trip.id != trip.id
        )
        .first()
    )

    if vehicle_busy:
        raise HTTPException(
            409,
            f"Le vÃƒÆ’Ã‚Â©hicule est dÃƒÆ’Ã‚Â©jÃƒÆ’Ã‚Â  sur la course #{vehicle_busy.id}"
        )

    # EmpÃƒÆ’Ã‚Âªche le mÃƒÆ’Ã‚Âªme chauffeur d'effectuer deux courses simultanÃƒÆ’Ã‚Â©ment.
    driver_busy = (
        db.query(Trip)
        .filter(
            Trip.driver_id == trip.driver_id,
            Trip.status == "IN_PROGRESS",
            Trip.id != trip.id
        )
        .first()
    )

    if driver_busy:
        raise HTTPException(
            409,
            f"Le chauffeur est dÃƒÆ’Ã‚Â©jÃƒÆ’Ã‚Â  sur la course #{driver_busy.id}"
        )

    trip.start_mileage = x.start_mileage
    trip.actual_departure_at = datetime.now(timezone.utc)
    trip.status = "IN_PROGRESS"

    vehicle.mileage = x.start_mileage

    db.commit()
    db.refresh(trip)

    audit(db, u, "START_TRIP", str(trip.id))

    return {
        "id": trip.id,
        "status": trip.status,
        "actual_departure_at": trip.actual_departure_at,
        "start_mileage": trip.start_mileage,
        "vehicle_id": trip.vehicle_id,
        "driver_id": trip.driver_id
    }


# ============================================================
# FIN D'UNE COURSE
# ============================================================

@app.get("/operations/dashboard")
def operations_dashboard(
    u=Depends(roles("ADMIN", "CONTROLLER")),
    db: Session = Depends(get_db)
):
    trips = db.query(Trip).all()

    completed = [
        t for t in trips
        if t.status == "COMPLETED"
    ]

    total_distance = sum(
        (t.end_mileage - t.start_mileage)
        for t in completed
        if (
            t.start_mileage is not None
            and t.end_mileage is not None
        )
    )

    successful_payments = (
        db.query(Payment)
        .filter(
            Payment.status == PaymentStatus.SUCCESS
        )
        .all()
    )

    revenue = sum(
        p.amount for p in successful_payments
    )

    return {
        "trips_total": len(trips),

        "scheduled": sum(
            1 for t in trips
            if t.status == "SCHEDULED"
        ),

        "in_progress": sum(
            1 for t in trips
            if t.status == "IN_PROGRESS"
        ),

        "completed": len(completed),

        "cancelled": sum(
            1 for t in trips
            if t.status == "CANCELLED"
        ),

        "distance_km": total_distance,

        "tickets": db.query(Ticket).count(),

        "revenue": revenue
    }


@app.put("/trips/{trip_id}/complete")
def complete_trip(
    trip_id: int,
    x: TripCompleteIn,
    u=Depends(roles("ADMIN", "DRIVER")),
    db: Session = Depends(get_db)
):
    # --------------------------------------------------------
    # V5.9 - ETAPE 93 : CONTROLE D'ACCES A LA COURSE
    #
    # Le chauffeur ne peut modifier que ses propres courses.
    # Une course non autorisee retourne HTTP 404.
    # --------------------------------------------------------
    trip = verifier_acces_course(db, u, trip_id)

    if trip.status != "IN_PROGRESS":
        raise HTTPException(
            409,
            "Seule une course en cours peut ÃƒÆ’Ã‚Âªtre terminÃƒÆ’Ã‚Â©e"
        )

    if trip.start_mileage is None:
        raise HTTPException(
            409,
            "KilomÃƒÆ’Ã‚Â©trage de dÃƒÆ’Ã‚Â©part absent"
        )

    if x.end_mileage < trip.start_mileage:
        raise HTTPException(
            409,
            "Le kilomÃƒÆ’Ã‚Â©trage d'arrivÃƒÆ’Ã‚Â©e ne peut pas ÃƒÆ’Ã‚Âªtre infÃƒÆ’Ã‚Â©rieur au dÃƒÆ’Ã‚Â©part"
        )

    # ========================================================
    # BOUKOULOU TRANSPORT V5.9 - ETAPE 93.4.9.7.22
    #
    # Verrouillage transactionnel du vehicule
    # pendant la cloture d'une course.
    #
    # Permet de coordonner les modifications du kilometrage
    # avec les autres operations sur ce vehicule.
    # ========================================================

    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.id == trip.vehicle_id)
        .with_for_update()
        .first()
    )

    # ========================================================
    # BOUKOULOU TRANSPORT V5.9 - ETAPE 93.4.9.7.23
    #
    # Verrouillage et relecture de la course apres
    # le verrouillage du vehicule.
    # ========================================================

    if not vehicle:
        raise HTTPException(
            404,
            "Vehicule introuvable"
        )

    trip = (
        db.query(Trip)
        .populate_existing()
        .filter(Trip.id == trip_id)
        .with_for_update()
        .first()
    )

    if not trip:
        raise HTTPException(
            404,
            "Course introuvable"
        )

    # Verifier que le vehicule affecte n'a pas change.
    if trip.vehicle_id != vehicle.id:
        raise HTTPException(
            409,
            "Le vehicule affecte a la course a change"
        )

    # Verifier a nouveau le statut apres verrouillage.
    if trip.status != "IN_PROGRESS":
        raise HTTPException(
            409,
            "Cette course n'est plus en cours"
        )

    if trip.start_mileage is None:
        raise HTTPException(
            409,
            "Kilometrage de depart absent"
        )

    if x.end_mileage < trip.start_mileage:
        raise HTTPException(
            409,
            "Le kilometrage d'arrivee est inferieur au depart"
        )

    # Ne pas diminuer le compteur actuel du vehicule.
    if x.end_mileage < vehicle.mileage:
        raise HTTPException(
            409,
            f"Kilometrage inferieur au compteur du bus ({vehicle.mileage} km)"
        )

    trip.end_mileage = x.end_mileage
    trip.actual_arrival_at = datetime.now(timezone.utc)
    trip.status = "COMPLETED"

    if vehicle:
        vehicle.mileage = x.end_mileage

    db.commit()
    db.refresh(trip)

    audit(db, u, "COMPLETE_TRIP", str(trip.id))

    return {
        "id": trip.id,
        "status": trip.status,
        "actual_departure_at": trip.actual_departure_at,
        "actual_arrival_at": trip.actual_arrival_at,
        "start_mileage": trip.start_mileage,
        "end_mileage": trip.end_mileage,
        "distance_km": (
            trip.end_mileage - trip.start_mileage
        )
    }


# ============================================================
# ANNULATION
# ============================================================

@app.put("/trips/{trip_id}/cancel")
def cancel_trip(
    trip_id: int,
    x: TripCancelIn,
    u=Depends(roles("ADMIN")),
    db: Session = Depends(get_db)
):
    # ========================================================
    # BOUKOULOU TRANSPORT V5.9 - ETAPE 93.4.9.7.29
    #
    # Securiser l'annulation contre un depart simultane.
    #
    # Ordre des verrous :
    # 1. Vehicule
    # 2. Course
    # ========================================================

    # Premiere lecture pour identifier le vehicule.
    trip = db.get(Trip, trip_id)

    if not trip:
        raise HTTPException(404, "Course introuvable")

    vehicle_id_initial = trip.vehicle_id

    # Verrouiller le vehicule.
    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.id == vehicle_id_initial)
        .with_for_update()
        .first()
    )

    if not vehicle:
        raise HTTPException(404, "Vehicule introuvable")

    # Verrouiller et relire la course apres le vehicule.
    trip = (
        db.query(Trip)
        .populate_existing()
        .filter(Trip.id == trip_id)
        .with_for_update()
        .first()
    )

    if not trip:
        raise HTTPException(404, "Course introuvable")

    # Verifier que l'affectation n'a pas change.
    if trip.vehicle_id != vehicle.id:
        raise HTTPException(
            409,
            "Le vehicule affecte a la course a change"
        )

    # Les controles de statut existants suivent ici.

    # ========================================================
    # BOUKOULOU TRANSPORT V5.9 - ETAPE 93.4.9.7.27
    #
    # Interdire l'annulation d'une course deja commencee.
    # Une course en cours doit suivre sa procedure de fin.
    # ========================================================

    if trip.status == "IN_PROGRESS":
        raise HTTPException(
            status_code=409,
            detail=(
                "Impossible d'annuler une course en cours. "
                "Terminez d'abord la course."
            )
        )

    if trip.status == "COMPLETED":
        raise HTTPException(
            409,
            "Une course terminÃƒÆ’Ã‚Â©e ne peut pas ÃƒÆ’Ã‚Âªtre annulÃƒÆ’Ã‚Â©e"
        )


    if trip.status == "CANCELLED":
        raise HTTPException(
            409,
            "Cette course est dÃƒÆ’Ã‚Â©jÃƒÆ’Ã‚Â  annulÃƒÆ’Ã‚Â©e"
        )
    # ========================================================
    # BOUKOULOU TRANSPORT V5.9 - ETAPE 93.4.9.7.30
    #
    # Seules les courses planifiees peuvent etre annulees.
    # ========================================================

    if trip.status != "SCHEDULED":
        raise HTTPException(
            status_code=409,
            detail=(
                "Annulation impossible : "
                f"statut actuel {trip.status}"
            )
        )

    trip.status = "CANCELLED"

    if x.notes:
        trip.notes = x.notes

    db.commit()
    db.refresh(trip)

    audit(db, u, "CANCEL_TRIP", str(trip.id))

    return {
        "id": trip.id,
        "status": trip.status,
        "notes": trip.notes
    }

@app.get("/trips/{trip_id}/report")
def trip_report(
    trip_id: int,
    u=Depends(roles("ADMIN", "COUNTRY_MANAGER", "CONTROLLER", "DRIVER")),
    db: Session = Depends(get_db)
):
    # ========================================================
    # BOUKOULOU TRANSPORT V5.9 - ETAPE 93.4.5
    #
    # Verification des droits d'acces au rapport de course.
    #
    # ADMIN           : toutes les courses
    # COUNTRY_MANAGER : courses de son pays
    # DRIVER          : courses attribuees
    # CONTROLLER      : courses affectees
    #
    # Retour HTTP 404 si la course est inaccessible.
    # ========================================================

    trip = verifier_acces_course(db, u, trip_id)

    tickets = (
        db.query(Ticket)
        .filter(Ticket.trip_id == trip.id)
        .all()
    )

    ticket_ids = [t.id for t in tickets]

    payments = []

    if ticket_ids:
        payments = (
            db.query(Payment)
            .filter(
                Payment.ticket_id.in_(ticket_ids),
                Payment.status == PaymentStatus.SUCCESS
            )
            .all()
        )

    revenue = sum(p.amount for p in payments)

    distance = None

    if (
        trip.start_mileage is not None
        and trip.end_mileage is not None
    ):
        distance = trip.end_mileage - trip.start_mileage

    return {
        "trip_id": trip.id,

        "status": trip.status,

        "line": (
            f"{trip.line.code} - {trip.line.name}"
            if trip.line else None
        ),

        "vehicle": (
            f"{trip.vehicle.code} - {trip.vehicle.plate}"
            if trip.vehicle else None
        ),

        "driver": (
            f"{trip.driver.first_name} {trip.driver.last_name}"
            if trip.driver else None
        ),

        "scheduled_departure": trip.departure_at,
        "actual_departure": trip.actual_departure_at,
        "actual_arrival": trip.actual_arrival_at,

        "start_mileage": trip.start_mileage,
        "end_mileage": trip.end_mileage,
        "distance_km": distance,

        "tickets_total": len(tickets),

        "tickets_paid": sum(
            1 for t in tickets
            if t.status in (
                TicketStatus.PAID,
                TicketStatus.USED
            )
        ),

        "tickets_used": sum(
            1 for t in tickets
            if t.status == TicketStatus.USED
        ),

        "successful_payments": len(payments),

        "revenue": revenue,

        "notes": trip.notes
    }


# ============================================================
# V5.8 - CAPACITÃƒÆ’Ã¢â‚¬Â° DES BUS ET DISPONIBILITÃƒÆ’Ã¢â‚¬Â° DES PLACES
# ============================================================
# Un billet PENDING non expirÃƒÆ’Ã‚Â© rÃƒÆ’Ã‚Â©serve une place pendant 12 heures.
# Les billets PAID et USED occupent ÃƒÆ’Ã‚Â©galement une place.
# CANCELLED, EXPIRED et PENDING expirÃƒÆ’Ã‚Â©s ne sont pas comptabilisÃƒÆ’Ã‚Â©s.
# Le verrou PostgreSQL sur la course empÃƒÆ’Ã‚Âªche deux agents de vendre
# simultanÃƒÆ’Ã‚Â©ment la derniÃƒÆ’Ã‚Â¨re place disponible.

def _places_occupees(db: Session, trip_id: int, instant: datetime) -> int:
    # V5.9 : ajouter les voyages dÃƒÆ’Ã‚Â©jÃƒÆ’Ã‚Â  validÃƒÆ’Ã‚Â©s sur cette course.
    nouveaux = db.query(func.count(Boarding59.id)).filter(Boarding59.trip_id == trip_id).scalar() or 0
    anciens = (
        db.query(func.count(Ticket.id))
        .filter(
            Ticket.trip_id == trip_id,
            (
                Ticket.status.in_([TicketStatus.PAID, TicketStatus.USED])
                | ((Ticket.status == TicketStatus.PENDING) & (Ticket.expires_at > instant))
            ),
        )
        .scalar() or 0
    )
    return anciens + nouveaux


@app.get("/trips/{trip_id}/availability")
def trip_availability(trip_id: int, u=Depends(roles("ADMIN", "AGENT", "CONTROLLER", "DRIVER")),
                      db: Session = Depends(get_db)):
    # --------------------------------------------------------
    # V5.9 - ETAPE 93.4 : SECURITE DES DISPONIBILITES
    #
    # ADMIN : acces global.
    # DRIVER : uniquement ses courses affectees.
    # CONTROLLER : uniquement ses courses affectees.
    #
    # Les autres roles conservent les regles de filtrage
    # definies dans filtrer_courses_utilisateur().
    #
    # Une course non autorisee retourne HTTP 404.
    # --------------------------------------------------------

    trip = verifier_acces_course(db, u, trip_id)

    # V5.8 : addition des places assises et des places debout autorisÃƒÆ’Ã‚Â©es.
    capacity = trip.vehicle.capacity + trip.vehicle.standing_capacity
    occupied = _places_occupees(db, trip.id, datetime.now(timezone.utc))
    return {"trip_id": trip.id, "capacity": capacity,
            "seated_capacity": trip.vehicle.capacity,
            "standing_capacity": trip.vehicle.standing_capacity,
            "occupied": occupied, "available": max(0, capacity - occupied),
            "status": trip.status}


@app.post("/tickets")
def ticket(x: TicketIn, u=Depends(roles("ADMIN", "AGENT", "CONTROLLER")),
           db: Session = Depends(get_db)):
    # V5.9 : crÃƒÆ’Ã‚Â©ation directe par course dÃƒÆ’Ã‚Â©sactivÃƒÆ’Ã‚Â©e ; utiliser le stock ADMIN.
    raise HTTPException(410, "Utilisez la billetterie V5.9 : stock ADMIN, vente AGENT")
@app.get("/tickets")
def list_tickets(
    u=Depends(roles("ADMIN","CONTROLLER")),
    db:Session=Depends(get_db)
):
    rows = db.query(Ticket).order_by(Ticket.id.desc()).all()

    return [{
        "id": q.id,
        "code": q.code,
        "trip_id": q.trip_id,
        "amount": q.amount,
        "status": q.status,
        "expires_at": q.expires_at,
        "used_at": q.used_at
    } for q in rows]


@app.get("/payments")
def list_payments(
    u=Depends(roles("ADMIN","CONTROLLER")),
    db:Session=Depends(get_db)
):
    rows = db.query(Payment).order_by(Payment.id.desc()).all()

    return [{
        "id": p.id,
        "ticket_id": p.ticket_id,
        "provider": p.provider,
        "reference": p.reference,
        "amount": p.amount,
        "status": p.status
    } for p in rows]
@app.post("/tickets/{ticket_id}/payment")
def payment(
    ticket_id: int,
    x: PaymentIn,
    u=Depends(roles("ADMIN", "AGENT")),
    db: Session = Depends(get_db)
):
    # V5.9 : ancien paiement dÃƒÆ’Ã‚Â©sactivÃƒÆ’Ã‚Â©.
    # La billetterie actuelle utilise les ventes V5.9.
    # Ne jamais confirmer un paiement via simulate_success.
    raise HTTPException(
        status_code=410,
        detail="Ancien paiement dÃƒÆ’Ã‚Â©sactivÃƒÆ’Ã‚Â© : utilisez la billetterie V5.9"
    )

@app.post("/gps")
def gps(x:GPSIn,u=Depends(roles("ADMIN","DRIVER")),db:Session=Depends(get_db)):
 if not db.get(Vehicle,x.vehicle_id): raise HTTPException(404,"VÃƒÆ’Ã‚Â©hicule introuvable")
 return save(db,GPSPosition(**x.model_dump()))
@app.get("/gps/{vehicle_id}/latest")
def latest(vehicle_id:int,u=Depends(roles("ADMIN","CONTROLLER","DRIVER")),db:Session=Depends(get_db)): return db.query(GPSPosition).filter_by(vehicle_id=vehicle_id).order_by(GPSPosition.recorded_at.desc()).first()
# ============================================================
# V4.2 - MAINTENANCE
# ============================================================

@app.get("/maintenance")
def list_maintenance(
    u=Depends(roles("ADMIN", "CONTROLLER")),
    db: Session = Depends(get_db)
):
    rows = (
        db.query(Maintenance)
        .order_by(Maintenance.id.desc())
        .all()
    )

    return [{
        "id": m.id,
        "vehicle_id": m.vehicle_id,
        "vehicle": (
            f"{m.vehicle.code} - {m.vehicle.plate}"
            if m.vehicle else None
        ),
        "description": m.description,
        "maintenance_type": m.maintenance_type,
        "cost": m.cost,
        "mileage": m.mileage,
        "scheduled_at": m.scheduled_at,
        "completed_at": m.completed_at,
        "next_maintenance_at": m.next_maintenance_at,
        "status": m.status,
        "done": m.done,
        "created_at": m.created_at
    } for m in rows]



@app.post("/maintenance")
def create_maintenance(
    x: MaintenanceIn,
    u=Depends(roles("ADMIN")),
    db: Session = Depends(get_db)
):
    # Verrouiller le vehicule pendant toute la transaction.
    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.id == x.vehicle_id)
        .with_for_update()
        .first()
    )

    if not vehicle:
        db.rollback()
        raise HTTPException(404, "Vehicule introuvable")

    if x.status not in ("PLANNED", "IN_PROGRESS", "COMPLETED"):
        db.rollback()
        raise HTTPException(422, "Statut de maintenance invalide")

    # Une maintenance en cours immobilise le vehicule.
    if x.status == "IN_PROGRESS":
        course = (
            db.query(Trip)
            .filter(
                Trip.vehicle_id == vehicle.id,
                Trip.status == "IN_PROGRESS"
            )
            .first()
        )

        if course:
            db.rollback()
            raise HTTPException(
                409,
                f"Le bus effectue deja la course #{course.id}"
            )

        maintenance_active = (
            db.query(Maintenance)
            .filter(
                Maintenance.vehicle_id == vehicle.id,
                Maintenance.status == "IN_PROGRESS"
            )
            .first()
        )

        if maintenance_active:
            db.rollback()
            raise HTTPException(
                409,
                f"Le bus possede deja une maintenance active "
                f"#{maintenance_active.id}"
            )

    data = x.model_dump()

    m = Maintenance(
        **data,
        done=(x.status == "COMPLETED")
    )

    if x.status == "COMPLETED":
        m.completed_at = datetime.now(timezone.utc)

    # PLANNED n'immobilise pas le bus.
    # IN_PROGRESS immobilise le bus.
    if x.status == "IN_PROGRESS":
        vehicle.status = "MAINTENANCE"

    # Une maintenance terminee ou planifiee ne doit pas
    # annuler une autre immobilisation.
    if x.mileage is not None and x.mileage > vehicle.mileage:
        vehicle.mileage = x.mileage

    db.add(m)
    db.commit()
    db.refresh(m)

    audit(db, u, "CREATE_MAINTENANCE", f"{vehicle.code}:{m.id}")

    return m


@app.get("/maintenance/{maintenance_id}")
def get_maintenance(
    maintenance_id: int,
    u=Depends(roles("ADMIN", "CONTROLLER")),
    db: Session = Depends(get_db)
):
    m = db.get(Maintenance, maintenance_id)

    if not m:
        raise HTTPException(404, "Maintenance introuvable")

    return m


@app.put("/maintenance/{maintenance_id}")
def update_maintenance(
    maintenance_id: int,
    x: MaintenanceUpdate,
    u=Depends(roles("ADMIN")),
    db: Session = Depends(get_db)
):
    # Identifier d'abord le vehicule de la maintenance.
    m = db.get(Maintenance, maintenance_id)

    if not m:
        db.rollback()
        raise HTTPException(404, "Maintenance introuvable")

    # Verrouiller le vehicule avant les modifications.
    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.id == m.vehicle_id)
        .with_for_update()
        .first()
    )

    if not vehicle:
        db.rollback()
        raise HTTPException(404, "Vehicule introuvable")

    # Verrouiller egalement la maintenance concernee.
    # ========================================================
    # BOUKOULOU TRANSPORT V5.9 - ETAPE 93.4.9.7.47
    #
    # Relire les donnees apres acquisition du verrou.
    # ========================================================

    m = (
        db.query(Maintenance)
        .populate_existing()
        .filter(Maintenance.id == maintenance_id)
        .with_for_update()
        .first()
    )

    if not m:
        db.rollback()
        raise HTTPException(404, "Maintenance introuvable")

    if m.vehicle_id != vehicle.id:
        db.rollback()
        raise HTTPException(
            409,
            "Le vehicule de la maintenance a change"
        )

    data = x.model_dump(exclude_unset=True)

    # Ne pas accepter de statut inconnu.
    nouveau_statut = data.get("status", m.status)

    if nouveau_statut not in ("PLANNED", "IN_PROGRESS", "COMPLETED"):
        db.rollback()
        raise HTTPException(422, "Statut de maintenance invalide")

    # Interdire une immobilisation pendant une course.
    if nouveau_statut == "IN_PROGRESS":
        course = (
            db.query(Trip)
            .filter(
                Trip.vehicle_id == vehicle.id,
                Trip.status == "IN_PROGRESS"
            )
            .first()
        )

        if course:
            db.rollback()
            raise HTTPException(
                409,
                f"Maintenance impossible : course #{course.id} en cours"
            )

        maintenance_active = (
            db.query(Maintenance)
            .filter(
                Maintenance.vehicle_id == vehicle.id,
                Maintenance.id != m.id,
                Maintenance.status == "IN_PROGRESS"
            )
            .first()
        )

        if maintenance_active:
            db.rollback()
            raise HTTPException(
                409,
                f"Le bus possede deja une autre maintenance active "
                f"#{maintenance_active.id}"
            )

    # Appliquer les modifications apres les controles.
    for field, value in data.items():
        setattr(m, field, value)

    if m.mileage is not None and m.mileage > vehicle.mileage:
        vehicle.mileage = m.mileage

    if nouveau_statut == "COMPLETED":
        m.done = True

        if m.completed_at is None:
            m.completed_at = datetime.now(timezone.utc)

    else:
        m.done = False

    # Verifier si une autre maintenance immobilise le bus.
    # autoflush=False : inclure explicitement le nouveau
    # statut de la maintenance actuelle dans le calcul.
    autre_maintenance_active = (
        db.query(Maintenance)
        .filter(
            Maintenance.vehicle_id == vehicle.id,
            Maintenance.id != m.id,
            Maintenance.status == "IN_PROGRESS"
        )
        .first()
    )

    immobilisation_active = (
        nouveau_statut == "IN_PROGRESS"
        or autre_maintenance_active is not None
    )

    if immobilisation_active:
        vehicle.status = "MAINTENANCE"
    elif vehicle.status == "MAINTENANCE":
        vehicle.status = "ACTIVE"

    db.commit()
    db.refresh(m)

    audit(db, u, "UPDATE_MAINTENANCE", str(m.id))

    return m


# ============================================================
# V4.2 - CARBURANT
# ============================================================

@app.get("/fuel")
def list_fuel(
    u=Depends(roles("ADMIN", "CONTROLLER")),
    db: Session = Depends(get_db)
):
    rows = (
        db.query(Fuel)
        .order_by(Fuel.id.desc())
        .all()
    )

    return [{
        "id": f.id,
        "vehicle_id": f.vehicle_id,
        "vehicle": (
            f"{f.vehicle.code} - {f.vehicle.plate}"
            if f.vehicle else None
        ),
        "driver_id": f.driver_id,
        "driver": (
            f"{f.driver.first_name} {f.driver.last_name}"
            if f.driver else None
        ),
        "liters": f.liters,
        "cost": f.cost,
        "mileage": f.mileage,
        "created_at": f.created_at
    } for f in rows]


@app.post("/fuel")
def create_fuel(
    x: FuelIn,

    # Seuls les administrateurs peuvent creer des courses.
    # Les chauffeurs conservent leurs droits de consultation,
    # de demarrage et de cloture sur leurs courses attribuees.
    u=Depends(roles("ADMIN")),
    db: Session = Depends(get_db)
):
    vehicle = db.get(Vehicle, x.vehicle_id)

    if not vehicle:
        raise HTTPException(404, "VÃƒÆ’Ã‚Â©hicule introuvable")

    if x.driver_id is not None:
        driver = db.get(Driver, x.driver_id)

        if not driver:
            raise HTTPException(404, "Chauffeur introuvable")

    f = Fuel(**x.model_dump())

    db.add(f)

    if x.mileage is not None and x.mileage > vehicle.mileage:
        vehicle.mileage = x.mileage

    db.commit()
    db.refresh(f)

    audit(
        db,
        u,
        "CREATE_FUEL",
        f"{vehicle.code}:{f.id}"
    )

    return f


@app.get("/fuel/{fuel_id}")
def get_fuel(
    fuel_id: int,
    u=Depends(roles("ADMIN", "CONTROLLER")),
    db: Session = Depends(get_db)
):
    f = db.get(Fuel, fuel_id)

    if not f:
        raise HTTPException(404, "Enregistrement carburant introuvable")

    return f


@app.put("/fuel/{fuel_id}")
def update_fuel(
    fuel_id: int,
    x: FuelUpdate,
    u=Depends(roles("ADMIN")),
    db: Session = Depends(get_db)
):
    f = db.get(Fuel, fuel_id)

    if not f:
        raise HTTPException(404, "Enregistrement carburant introuvable")

    data = x.model_dump(exclude_unset=True)

    if "driver_id" in data and data["driver_id"] is not None:
        if not db.get(Driver, data["driver_id"]):
            raise HTTPException(404, "Chauffeur introuvable")

    for field, value in data.items():
        setattr(f, field, value)

    vehicle = db.get(Vehicle, f.vehicle_id)

    if f.mileage is not None and f.mileage > vehicle.mileage:
        vehicle.mileage = f.mileage

    db.commit()
    db.refresh(f)

    audit(
        db,
        u,
        "UPDATE_FUEL",
        str(f.id)
    )

    return f


# ============================================================
# V4.2 - DASHBOARD FLOTTE
# ============================================================

@app.get("/fleet/dashboard")
def fleet_dashboard(
    u=Depends(roles("ADMIN", "CONTROLLER")),
    db: Session = Depends(get_db)
):
    vehicles = db.query(Vehicle).all()
    drivers = db.query(Driver).all()

    total_fuel_cost = sum(
        value[0] or 0
        for value in db.query(Fuel.cost).all()
    )

    total_fuel_liters = sum(
        value[0] or 0
        for value in db.query(Fuel.liters).all()
    )

    total_maintenance_cost = sum(
        value[0] or 0
        for value in db.query(Maintenance.cost).all()
    )

    active_assignments = (
        db.query(DriverAssignment)
        .filter(DriverAssignment.active == True)
        .count()
    )

    return {
        "vehicles": len(vehicles),

        "vehicles_active": sum(
            1 for v in vehicles
            if v.status == "ACTIVE"
        ),

        "vehicles_maintenance": sum(
            1 for v in vehicles
            if v.status == "MAINTENANCE"
        ),

        "vehicles_out_of_service": sum(
            1 for v in vehicles
            if v.status == "OUT_OF_SERVICE"
        ),

        "drivers": len(drivers),

        "drivers_active": sum(
            1 for d in drivers
            if d.status == "ACTIVE"
        ),

        "active_assignments": active_assignments,

        "fuel_cost": total_fuel_cost,
        "fuel_liters": total_fuel_liters,

        "maintenance_cost": total_maintenance_cost
    }
@app.get("/dashboard")
def dashboard(
    u=Depends(roles("ADMIN", "CONTROLLER", "DRIVER")),
    db: Session = Depends(get_db)
):
    # Calculer les recettes des paiements classiques.
    payment_revenue = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.status == PaymentStatus.SUCCESS)
        .scalar()
    ) or 0

    # Calculer les recettes des ventes ÃƒÆ’Ã‚Â  bord.
    onboard_revenue = (
        db.query(func.coalesce(func.sum(OnboardSale59.total_amount), 0))
        .scalar()
    ) or 0

    # Calculer les recettes des ventes au guichet.
    # Les ventes ÃƒÆ’Ã‚Â  bord sont exclues pour ÃƒÆ’Ã‚Â©viter le double comptage.
    agency_revenue = calculate_agency_revenue(db)

    # Additionner les trois sources de recettes.
    revenue = payment_revenue + onboard_revenue + agency_revenue

    # Compter les billets classiques et les passes V5.9.
    tickets_count = (
        db.query(Ticket).count()
        + db.query(Pass59).count()
    )

    # Compter les billets classiques utilisÃƒÆ’Ã‚Â©s et les embarquements V5.9.
    # Pour V5.9, chaque embarquement reprÃƒÆ’Ã‚Â©sente un voyage consommÃƒÆ’Ã‚Â©.
    tickets_used = (
        db.query(Ticket)
        .filter_by(status=TicketStatus.USED)
        .count()
        + db.query(Boarding59).count()
    )

    # Compter les paiements classiques et les ventes V5.9.
    payments_count = (
        db.query(Payment)
        .filter_by(status=PaymentStatus.SUCCESS)
        .count()
        + db.query(Pass59).count()
    )

    # Retourner les indicateurs du dashboard global.
    return {
        "countries": db.query(Country).count(),
        "lines": db.query(Line).count(),
        "vehicles": db.query(Vehicle).count(),
        "trips": db.query(Trip).count(),
        "tickets": tickets_count,
        "tickets_used": tickets_used,
        "successful_payments": payments_count,
        "revenue": revenue
    }

# ============================================================
# V5.3 - CAISSE & RECETTES
# ============================================================

CASH_TZ = ZoneInfo("Africa/Brazzaville")


def cash_day_bounds(day: date):
    """
    Transforme une journÃƒÆ’Ã‚Â©e locale Congo/Gabon en bornes UTC.
    Exemple :
    07/10/2026 00:00 locale -> 06/10/2026 23:00 UTC
    """
    local_start = datetime(
        day.year, day.month, day.day,
        0, 0, 0,
        tzinfo=CASH_TZ
    )

    local_end = local_start + timedelta(days=1)

    return (
        local_start.astimezone(timezone.utc),
        local_end.astimezone(timezone.utc)
    )


# ============================================================
# V5.9 - INDICATEURS DU MENU CAISSE UNIQUEMENT
# Les autres tableaux de bord et les sessions restent inchangÃƒÆ’Ã‚Â©s.
# ============================================================

def _cash_ventes_v59(db: Session, selected_day: date, user):
    """Lire les ventes V5.9 du jour, sans compter deux fois les ventes ÃƒÆ’Ã‚Â  bord."""
    start_utc, end_utc = cash_day_bounds(selected_day)

    # Une vente ÃƒÆ’Ã‚Â  bord possÃƒÆ’Ã‚Â¨de ÃƒÆ’Ã‚Â©galement un Pass59 : l'exclure du guichet.
    passes_vendus_bord = db.query(OnboardSale59.pass_id)
    guichet = db.query(Pass59).filter(
        ~Pass59.id.in_(passes_vendus_bord),
        Pass59.sold_at >= start_utc,
        Pass59.sold_at < end_utc,
    )
    bord = db.query(OnboardSale59, Pass59).join(
        Pass59, OnboardSale59.pass_id == Pass59.id
    ).filter(
        Pass59.sold_at >= start_utc,
        Pass59.sold_at < end_utc,
    )

    # PrÃƒÆ’Ã‚Â©server la restriction d'accÃƒÆ’Ã‚Â¨s aux propres ventes des agents.
    if user.role.value == "AGENT":
        guichet = guichet.filter(Pass59.agent_id == user.id)
        bord = bord.filter(OnboardSale59.controller_id == user.id)

    return guichet.all(), bord.all()


def _cash_details_v59(db: Session, guichet, bord):
    """Construire les transactions avec les clÃƒÆ’Ã‚Â©s attendues par le frontend."""
    details = []
    # PrÃƒÆ’Ã‚Â©charger les lignes et les courses utilisÃƒÆ’Ã‚Â©es pour limiter les requÃƒÆ’Ã‚Âªtes.
    trip_ids = {vente.trip_id for vente, _ in bord if vente.trip_id is not None}
    trips = {t.id: t for t in db.query(Trip).filter(Trip.id.in_(trip_ids)).all()} if trip_ids else {}
    line_ids = {t.line_id for t in trips.values() if t.line_id is not None}
    lines = {l.id: l for l in db.query(Line).filter(Line.id.in_(line_ids)).all()} if line_ids else {}

    for passage in guichet:
        # Les pass guichet ne sont pas liÃƒÆ’Ã‚Â©s ÃƒÆ’Ã‚Â  une course ÃƒÆ’Ã‚Â  la vente.
        details.append({
            "payment_id": passage.id,
            "user_id": passage.agent_id,
            "cash_session_id": passage.cash_session_id,
            "reference": passage.reference,
            "provider": "GUICHET",
            "amount": int(passage.total or 0),
            "payment_status": "SUCCESS",
            "paid_at": passage.sold_at,
            "ticket_id": passage.id,
            "ticket_code": passage.code,
            "trip_id": None,
            "line_id": None,
            "line_code": "ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â",
            "line_name": "Non attribuÃƒÆ’Ã‚Â©e",
        })

    for vente, passage in bord:
        trip = trips.get(vente.trip_id)
        line = lines.get(trip.line_id) if trip else None
        details.append({
            "payment_id": vente.id,
            "user_id": vente.controller_id,
            "cash_session_id": vente.cash_session_id,
            "reference": passage.reference,
            "provider": "BORD",
            # Le montant calculÃƒÆ’Ã‚Â© inclut les frais historiques enregistrÃƒÆ’Ã‚Â©s.
            "amount": int(vente.total_amount or 0),
            "payment_status": "SUCCESS",
            "paid_at": passage.sold_at,
            "ticket_id": passage.id,
            "ticket_code": passage.code,
            "trip_id": trip.id if trip else None,
            "line_id": line.id if line else None,
            "line_code": line.code if line else "ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â",
            "line_name": line.name if line else "Non attribuÃƒÆ’Ã‚Â©e",
        })

    # Normaliser la comparaison des dates pour ÃƒÆ’Ã‚Â©viter les mÃƒÆ’Ã‚Â©langes naÃƒÆ’Ã‚Â¯f/UTC.
    def ordre(item):
        instant = item["paid_at"]
        if instant is None:
            return datetime.min.replace(tzinfo=timezone.utc)
        if instant.tzinfo is None:
            instant = instant.replace(tzinfo=timezone.utc)
        return instant.astimezone(timezone.utc)

    details.sort(key=ordre, reverse=True)
    return details


@app.get("/cash/daily")
def cash_daily(
    day: date | None = None,
    db: Session = Depends(get_db),
    user=Depends(roles("ADMIN", "AGENT")),
):
    """Afficher les recettes et compteurs du menu Caisse."""
    selected_day = day or datetime.now(CASH_TZ).date()
    guichet, bord = _cash_ventes_v59(db, selected_day, user)
    providers = {}
    noms = {u.id: u.username for u in db.query(User).all()}

    def ajouter(agent_id, montant):
        # Ici Ãƒâ€šÃ‚Â« paiements Ãƒâ€šÃ‚Â» signifie opÃƒÆ’Ã‚Â©rations de vente encaissÃƒÆ’Ã‚Â©es.
        if agent_id not in providers:
            providers[agent_id] = {
                "provider": noms.get(agent_id, "Non renseignÃƒÆ’Ã‚Â©" if agent_id is None else f"Utilisateur #{agent_id}"),
                "payments": 0,
                "revenue": 0,
            }
        providers[agent_id]["payments"] += 1
        providers[agent_id]["revenue"] += montant

    recettes = 0
    billets = 0
    for passage in guichet:
        montant = int(passage.total or 0)
        recettes += montant
        billets += int(passage.quantity or 0)
        ajouter(passage.agent_id, montant)
    for vente, passage in bord:
        montant = int(vente.total_amount or 0)
        recettes += montant
        billets += int(passage.quantity or 0)
        ajouter(vente.controller_id, montant)

    # Une course est encaissÃƒÆ’Ã‚Â©e si elle a au moins une vente ÃƒÆ’Ã‚Â  bord attribuÃƒÆ’Ã‚Â©e.
    courses = {vente.trip_id for vente, _ in bord if vente.trip_id is not None}
    return {
        "date": selected_day.isoformat(),
        "timezone": "Africa/Brazzaville",
        "payments_success": len(guichet) + len(bord),
        "tickets_sold": billets,
        "courses_encaissees": len(courses),
        "revenue": recettes,
        "providers": sorted(providers.values(), key=lambda p: p["revenue"], reverse=True),
    }


@app.get("/cash/daily/details")
def cash_daily_details(
    day: date | None = None,
    db: Session = Depends(get_db),
    user=Depends(roles("ADMIN", "AGENT")),
):
    """Afficher les transactions V5.9 du jour."""
    selected_day = day or datetime.now(CASH_TZ).date()
    guichet, bord = _cash_ventes_v59(db, selected_day, user)
    return _cash_details_v59(db, guichet, bord)


@app.get("/cash/by-line")
def cash_by_line(
    day: date | None = None,
    db: Session = Depends(get_db),
    user=Depends(roles("ADMIN", "AGENT")),
):
    """Regrouper les ventes ÃƒÆ’Ã‚Â  bord par ligne (guichet non attribuable)."""
    selected_day = day or datetime.now(CASH_TZ).date()
    _, bord = _cash_ventes_v59(db, selected_day, user)
    lignes = {}
    for vente, passage in bord:
        trip = db.get(Trip, vente.trip_id) if vente.trip_id is not None else None
        line = db.get(Line, trip.line_id) if trip else None
        if line is None:
            continue
        if line.id not in lignes:
            lignes[line.id] = {
                "line_id": line.id, "line_code": line.code,
                "line_name": line.name, "tickets": 0, "revenue": 0,
            }
        lignes[line.id]["tickets"] += int(passage.quantity or 0)
        lignes[line.id]["revenue"] += int(vente.total_amount or 0)
    return sorted(lignes.values(), key=lambda ligne: ligne["revenue"], reverse=True)


@app.get("/cash/by-trip")
def cash_by_trip(
    day: date | None = None,
    db: Session = Depends(get_db),
    user=Depends(roles("ADMIN", "AGENT")),
):
    """Regrouper les ventes ÃƒÆ’Ã‚Â  bord par course (guichet non attribuable)."""
    selected_day = day or datetime.now(CASH_TZ).date()
    _, bord = _cash_ventes_v59(db, selected_day, user)
    courses = {}
    for vente, passage in bord:
        trip = db.get(Trip, vente.trip_id) if vente.trip_id is not None else None
        if trip is None:
            continue
        line = db.get(Line, trip.line_id)
        if trip.id not in courses:
            courses[trip.id] = {
                "trip_id": trip.id, "departure_at": trip.departure_at,
                "line_code": line.code if line else "ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â",
                "line_name": line.name if line else "Non attribuÃƒÆ’Ã‚Â©e",
                "tickets": 0, "revenue": 0,
            }
        courses[trip.id]["tickets"] += int(passage.quantity or 0)
        courses[trip.id]["revenue"] += int(vente.total_amount or 0)
    return sorted(courses.values(), key=lambda row: row["departure_at"], reverse=True)


@app.post("/cash/sessions/open")
def open_cash_session(
    data: CashSessionOpenIn,
    db: Session = Depends(get_db),
    user = Depends(roles("ADMIN", "AGENT", "CONTROLLER", "DRIVER"))
):
    existing = (
        db.query(CashSession)
        .filter(
            CashSession.user_id == user.id,
            CashSession.status == "OPEN"
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "CASH_ALREADY_OPEN",
                "message": "Une caisse est dÃƒÆ’Ã‚Â©jÃƒÆ’Ã‚Â  ouverte pour cet utilisateur"
            }
        )

    session = CashSession(
        user_id=user.id,
        opening_amount=data.opening_amount,
        status="OPEN",
        notes=data.notes
    )

    db.add(session)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        # Un index unique partiel en base doit empÃƒÆ’Ã‚Âªcher deux caisses
        # ouvertes simultanÃƒÆ’Ã‚Â©ment pour le mÃƒÆ’Ã‚Âªme utilisateur.
        # Ne pas confondre ce conflit avec une autre erreur d'intÃƒÆ’Ã‚Â©gritÃƒÆ’Ã‚Â©.
        constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
        if constraint == "ux_cash_sessions_one_open_per_user":
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "CASH_ALREADY_OPEN",
                    "message": "Une caisse est dÃƒÆ’Ã‚Â©jÃƒÆ’Ã‚Â  ouverte pour cet utilisateur"
                }
            ) from exc
        raise
    db.refresh(session)
    audit(db, user, "OPEN_CASH_SESSION", str(session.id))

    return {
        "id": session.id,
        "user_id": session.user_id,
        "username": user.username,
        "opened_at": session.opened_at,
        "opening_amount": session.opening_amount,
        "status": session.status,
        "notes": session.notes
    }

@app.get("/cash/sessions/current")
def current_cash_session(
    db: Session = Depends(get_db),
    user = Depends(roles("ADMIN","CONTROLLER", "AGENT", "DRIVER"))
):
    session = (
        db.query(CashSession)
        .filter(
            CashSession.user_id == user.id,
            CashSession.status == "OPEN"
        )
        .order_by(CashSession.opened_at.desc())
        .first()
    )

    if not session:
        return {
            "open": False,
            "session": None
        }

    revenue = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(
            Payment.cash_session_id == session.id,
            Payment.status == PaymentStatus.SUCCESS
        )
        .scalar()
    )

    payments = (
        db.query(func.count(Payment.id))
        .filter(
            Payment.cash_session_id == session.id,
            Payment.status == PaymentStatus.SUCCESS
        )
        .scalar()
    )

    # Calculer les recettes des ventes au guichet V5.9.
    agency_revenue = calculate_agency_revenue(
        db,
        cash_session_id=session.id
    )

    # Calculer les recettes des ventes ÃƒÆ’Ã‚Â  bord V5.9.
    onboard_revenue = (
      db.query(
        func.coalesce(func.sum(OnboardSale59.total_amount), 0)
      )
      .filter(
            OnboardSale59.cash_session_id == session.id
      )
      .scalar()
    ) or 0

    # RÃƒÆ’Ã‚Â©cupÃƒÆ’Ã‚Â©rer les recettes des paiements classiques.
    payment_revenue = revenue or 0

    # Additionner les trois sources de recettes.
    total_revenue = (
        payment_revenue
        + agency_revenue
        + onboard_revenue
    )

    # RÃƒÆ’Ã‚Â©partir les recettes selon le moyen de paiement.
    # Cette fonction inclut les ventes au guichet, ÃƒÆ’Ã‚Â  bord
    # et les paiements classiques, sans compter deux fois les billets.
    recettes_par_provider = calculer_recettes_par_provider(
        db,
        cash_session_id=session.id
    )

    # Calculer uniquement les recettes encaissÃƒÆ’Ã‚Â©es en espÃƒÆ’Ã‚Â¨ces.
    cash_revenue = recettes_par_provider.get("CASH", 0)

    # Le montant thÃƒÆ’Ã‚Â©orique de la caisse physique correspond
    # au fonds initial augmentÃƒÆ’Ã‚Â© des encaissements en espÃƒÆ’Ã‚Â¨ces.
    expected_amount = session.opening_amount + cash_revenue

    # Compter les billets vendus pendant cette session de caisse.
    # Les ventes au guichet et ÃƒÆ’Ã‚Â  bord sont dÃƒÆ’Ã‚Â©jÃƒÆ’Ã‚Â  enregistrÃƒÆ’Ã‚Â©es dans v59_passes.
    billets_vendus = (
        db.query(func.count(Pass59.id))
        .filter(Pass59.cash_session_id == session.id)
        .scalar()
    ) or 0

    # Retourner les informations actualisÃƒÆ’Ã‚Â©es de la caisse ouverte.
    return {
        "open": True,
        "session": {
            "id": session.id,
            "user_id": session.user_id,
            "username": user.username,
            "opened_at": session.opened_at,
            "opening_amount": session.opening_amount,
            "sales_revenue": total_revenue,
            "expected_amount": expected_amount,
            "payments": billets_vendus,
            "agency_revenue": agency_revenue,
            "onboard_revenue": onboard_revenue,
            "status": session.status,
            "notes": session.notes
        }

    }


@app.post("/cash/sessions/{session_id}/close")
def close_cash_session(
    session_id: int,
    data: CashSessionCloseIn,
    db: Session = Depends(get_db),
    user = Depends(roles("ADMIN", "AGENT","CONTROLLER", "DRIVER"))
):
    # Verrouillage PostgreSQL de la ligne jusqu'au commit/rollback.
    # Une seconde clÃƒÆ’Ã‚Â´ture attend la premiÃƒÆ’Ã‚Â¨re, puis constate CLOSED (409).
    session = db.query(CashSession).filter(
        CashSession.id == session_id
    ).with_for_update().first()

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session de caisse introuvable"
        )

    # L'agent ne peut clÃƒÆ’Ã‚Â´turer que sa propre caisse.
    # Un ADMIN peut clÃƒÆ’Ã‚Â´turer une autre caisse.
    role_value = (
        user.role.value
        if hasattr(user.role, "value")
        else str(user.role)
    )

    if session.user_id != user.id and role_value != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Vous ne pouvez pas clÃƒÆ’Ã‚Â´turer cette caisse"
        )

    if session.status != "OPEN":
        raise HTTPException(
            status_code=409,
            detail={
                "code": "CASH_ALREADY_CLOSED",
                "message": "Cette caisse est dÃƒÆ’Ã‚Â©jÃƒÆ’Ã‚Â  clÃƒÆ’Ã‚Â´turÃƒÆ’Ã‚Â©e"
            }
        )

    revenue = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(
            Payment.cash_session_id == session.id,
            Payment.status == PaymentStatus.SUCCESS
        )
        .scalar()
    ) or 0

    onboard_revenue = (
        db.query(func.coalesce(func.sum(OnboardSale59.total_amount), 0))
        .filter(
            OnboardSale59.cash_session_id == session.id
        )
        .scalar()
    ) or 0

    # Calculer les recettes des billets vendus au guichet.
    # Les billets vendus ÃƒÆ’Ã‚Â  bord sont exclus pour ÃƒÆ’Ã‚Â©viter le double comptage.
    agency_revenue = calculate_agency_revenue(
        db,
        cash_session_id=session.id
    )

    # SÃƒÆ’Ã‚Â©parer les recettes selon le moyen de paiement.
    recettes_par_provider = calculer_recettes_par_provider(
        db,
        cash_session_id=session.id
    )

    # Seules les espÃƒÆ’Ã‚Â¨ces entrent dans la caisse physique.
    cash_revenue = recettes_par_provider.get("CASH", 0)

    # Total commercial, tous moyens de paiement confondus.
    total_revenue = sum(recettes_par_provider.values())

    # Fonds initial + ventes rÃƒÆ’Ã‚Â©ellement encaissÃƒÆ’Ã‚Â©es en espÃƒÆ’Ã‚Â¨ces.
    expected = session.opening_amount + cash_revenue

    session.expected_amount = expected
    session.declared_amount = data.declared_amount
    session.difference_amount = data.declared_amount - expected
    session.closed_at = datetime.now(timezone.utc)
    session.status = "CLOSED"

    if data.notes is not None:
        session.notes = data.notes

    # ClÃƒÆ’Ã‚Â´ture et journal d'audit dans une seule transaction.
    # Si l'audit ÃƒÆ’Ã‚Â©choue, la clÃƒÆ’Ã‚Â´ture n'est pas validÃƒÆ’Ã‚Â©e en base.
    try:
        db.add(Audit(
            username=user.username,
            action="CLOSE_CASH_SESSION",
            target=str(session.id),
        ))
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(session)

    return {
        "id": session.id,
        "user_id": session.user_id,
        "opened_at": session.opened_at,
        "closed_at": session.closed_at,
        "opening_amount": session.opening_amount,
        # Retourner le dÃƒÆ’Ã‚Â©tail des recettes de la caisse.
        "sales_revenue": total_revenue,
        "cash_revenue": cash_revenue,
        "payment_breakdown": recettes_par_provider,
        "other_payments_revenue": revenue,
        "onboard_revenue": onboard_revenue,
        "agency_revenue": agency_revenue,
        "expected_amount": session.expected_amount,
        "declared_amount": session.declared_amount,
        "difference_amount": session.difference_amount,
        "status": session.status,
        "notes": session.notes
    }



# ============================================================
# V5.9 - RECTIFICATION ADMINISTRATIVE D'UNE CAISSE
# ============================================================
# Seul un administrateur peut rectifier une caisse clÃƒÆ’Ã‚Â´turÃƒÆ’Ã‚Â©e.
# L'ancien montant et le nouveau montant sont historisÃƒÆ’Ã‚Â©s.
# Les ventes et le statut CLOSED ne sont jamais modifiÃƒÆ’Ã‚Â©s.

class CashSessionRectifyIn(BaseModel):
    # Montant rÃƒÆ’Ã‚Â©ellement comptÃƒÆ’Ã‚Â© lors de la vÃƒÆ’Ã‚Â©rification.
    declared_amount: int = Field(ge=0)

    # Justification obligatoire de la rectification.
    reason: str = Field(min_length=10, max_length=500)


@app.post("/cash/sessions/{session_id}/rectify")
def rectify_cash_session(
    session_id: int,
    data: CashSessionRectifyIn,
    db: Session = Depends(get_db),
    user=Depends(roles("ADMIN"))
):
    # Verrouiller la caisse pendant la rectification.
    session = (
        db.query(CashSession)
        .filter(CashSession.id == session_id)
        .with_for_update()
        .first()
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Caisse introuvable"
        )

    # Interdire toute rectification d'une caisse ouverte.
    if session.status != "CLOSED":
        raise HTTPException(
            status_code=409,
            detail="Seule une caisse clÃƒÆ’Ã‚Â´turÃƒÆ’Ã‚Â©e peut ÃƒÆ’Ã‚Âªtre rectifiÃƒÆ’Ã‚Â©e"
        )

    # VÃƒÆ’Ã‚Â©rifier que les montants de clÃƒÆ’Ã‚Â´ture existent.
    if (
        session.expected_amount is None
        or session.declared_amount is None
        or session.difference_amount is None
    ):
        raise HTTPException(
            status_code=409,
            detail="Montants de clÃƒÆ’Ã‚Â´ture incomplets"
        )

    # Nettoyer et contrÃƒÆ’Ã‚Â´ler le motif.
    reason = data.reason.strip()

    if len(reason) < 10:
        raise HTTPException(
            status_code=422,
            detail="Le motif doit contenir au moins 10 caractÃƒÆ’Ã‚Â¨res"
        )

    # Conserver les anciennes valeurs.
    old_declared = session.declared_amount
    old_difference = session.difference_amount

    # Calculer le nouvel ÃƒÆ’Ã‚Â©cart sans modifier les recettes.
    new_difference = (
        data.declared_amount - session.expected_amount
    )

    # Refuser une rectification sans changement.
    if old_declared == data.declared_amount:
        raise HTTPException(
            status_code=409,
            detail="Le montant dÃƒÆ’Ã‚Â©clarÃƒÆ’Ã‚Â© est dÃƒÆ’Ã‚Â©jÃƒÆ’Ã‚Â  identique"
        )

    # PrÃƒÆ’Ã‚Â©parer l'historique de la rectification.
    rectification = CashSessionRectification(
        cash_session_id=session.id,
        admin_user_id=user.id,
        old_declared_amount=old_declared,
        new_declared_amount=data.declared_amount,
        old_difference_amount=old_difference,
        new_difference_amount=new_difference,
        reason=reason
    )

    try:
        # Corriger uniquement le montant dÃƒÆ’Ã‚Â©clarÃƒÆ’Ã‚Â© et l'ÃƒÆ’Ã‚Â©cart.
        session.declared_amount = data.declared_amount
        session.difference_amount = new_difference

        # Enregistrer la correction et sa trace d'audit.
        # Un seul commit garantit la cohÃƒÆ’Ã‚Â©rence des ÃƒÆ’Ã‚Â©critures.
        db.add(rectification)
        db.add(
            Audit(
                username=user.username,
                action="RECTIFY_CASH_SESSION",
                target=str(session.id)
            )
        )

        db.commit()
        db.refresh(rectification)

    except Exception:
        # Annuler toutes les modifications en cas d'erreur.
        db.rollback()
        raise

    return {
        "message": "Rectification enregistrÃƒÆ’Ã‚Â©e",
        "rectification_id": rectification.id,
        "cash_session_id": session.id,
        "status": session.status,
        "expected_amount": session.expected_amount,
        "old_declared_amount": old_declared,
        "new_declared_amount": session.declared_amount,
        "old_difference_amount": old_difference,
        "new_difference_amount": session.difference_amount,
        "reason": reason,
        "admin_user_id": user.id
    }



# ============================================================
# V5.9 - CONSULTATION DES RECTIFICATIONS DE CAISSE
# ============================================================
# Seul un administrateur peut consulter l'historique.
# Cette opÃƒÆ’Ã‚Â©ration est en lecture seule.

@app.get("/cash/sessions/{session_id}/rectifications")
def list_cash_rectifications(
    session_id: int,
    db: Session = Depends(get_db),
    user=Depends(roles("ADMIN"))
):
    # VÃƒÆ’Ã‚Â©rifier que la caisse demandÃƒÆ’Ã‚Â©e existe.
    session = db.get(CashSession, session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Caisse introuvable"
        )

    # RÃƒÆ’Ã‚Â©cupÃƒÆ’Ã‚Â©rer les rectifications dans l'ordre chronologique.
    rectifications = (
        db.query(CashSessionRectification)
        .filter(
            CashSessionRectification.cash_session_id == session_id
        )
        .order_by(
            CashSessionRectification.created_at.asc(),
            CashSessionRectification.id.asc()
        )
        .all()
    )

    # Retourner l'historique sans modifier la caisse.
    return {
        "cash_session_id": session_id,
        "status": session.status,
        "nombre_rectifications": len(rectifications),
        "rectifications": [
            {
                "id": r.id,
                "admin_user_id": r.admin_user_id,
                "old_declared_amount": r.old_declared_amount,
                "new_declared_amount": r.new_declared_amount,
                "old_difference_amount": r.old_difference_amount,
                "new_difference_amount": r.new_difference_amount,
                "reason": r.reason,
                "created_at": r.created_at
            }
            for r in rectifications
        ]
    }


# ============================================================
# V5.9 - TABLEAU DE BORD ADMINISTRATEUR DES CAISSES
# ============================================================
# Cet endpoint est rÃƒÆ’Ã‚Â©servÃƒÆ’Ã‚Â© aux administrateurs.
# Les recettes des paiements et des ventes ÃƒÆ’Ã‚Â  bord sont
# calculÃƒÆ’Ã‚Â©es sÃƒÆ’Ã‚Â©parÃƒÆ’Ã‚Â©ment pour ÃƒÆ’Ã‚Â©viter les doubles comptages.
# Les montants sont exprimÃƒÆ’Ã‚Â©s en XAF.

def calculate_agency_revenue(db: Session, cash_session_id=None):
    """
    Calculer les recettes des ventes au guichet.

    Les billets vendus ÃƒÆ’Ã‚Â  bord sont exclus, car leurs recettes
    sont dÃƒÆ’Ã‚Â©jÃƒÆ’Ã‚Â  comptabilisÃƒÆ’Ã‚Â©es dans v59_onboard_sales.
    """

    # Identifier les billets provenant d'une vente ÃƒÆ’Ã‚Â  bord.
    onboard_passes = db.query(OnboardSale59.pass_id)

    # SÃƒÆ’Ã‚Â©lectionner uniquement les billets vendus au guichet.
    query = db.query(
        func.coalesce(func.sum(Pass59.total), 0)
    ).filter(
        ~Pass59.id.in_(onboard_passes)
    )

    # Limiter le calcul ÃƒÆ’Ã‚Â  une caisse lorsqu'un identifiant est fourni.
    if cash_session_id is not None:
        query = query.filter(
            Pass59.cash_session_id == cash_session_id
        )

    # Retourner le montant total des ventes au guichet.
    return query.scalar() or 0


@app.get("/admin/dashboard/cash")
def admin_cash_dashboard(
    db: Session = Depends(get_db),
    user=Depends(roles("ADMIN"))
):
    # Compter les caisses ouvertes.
    open_sessions = (
        db.query(func.count(CashSession.id))
        .filter(CashSession.status == "OPEN")
        .scalar()
    ) or 0

    # Compter les caisses clÃƒÆ’Ã‚Â´turÃƒÆ’Ã‚Â©es.
    closed_sessions = (
        db.query(func.count(CashSession.id))
        .filter(CashSession.status == "CLOSED")
        .scalar()
    ) or 0

    # Calculer les paiements classiques rÃƒÆ’Ã‚Â©ussis
    # associÃƒÆ’Ã‚Â©s ÃƒÆ’Ã‚Â  une session de caisse.
    payment_revenue = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(
            Payment.status == PaymentStatus.SUCCESS,
            Payment.cash_session_id.isnot(None)
        )
        .scalar()
    ) or 0

    # Calculer les recettes des ventes ÃƒÆ’Ã‚Â  bord.
    onboard_revenue = (
        db.query(func.coalesce(func.sum(OnboardSale59.total_amount), 0))
        .scalar()
    ) or 0

    # Calculer les recettes des ventes au guichet.
    # Les ventes ÃƒÆ’Ã‚Â  bord sont exclues pour ÃƒÆ’Ã‚Â©viter le double comptage.
    agency_revenue = calculate_agency_revenue(db)

    # Additionner les trois sources de recettes.
    total_revenue = payment_revenue + onboard_revenue + agency_revenue

    # Calculer les ÃƒÆ’Ã‚Â©carts des caisses clÃƒÆ’Ã‚Â´turÃƒÆ’Ã‚Â©es.
    total_difference = (
        db.query(
            func.coalesce(
                func.sum(CashSession.difference_amount),
                0
            )
        )
        .filter(CashSession.status == "CLOSED")
        .scalar()
    ) or 0

    # Compter les rectifications administratives.
    rectification_count = (
        db.query(func.count(CashSessionRectification.id))
        .scalar()
    ) or 0

    # Retourner les indicateurs globaux.
    return {
        "currency": "XAF",
        "cash_sessions": {
            "open": open_sessions,
            "closed": closed_sessions,
            "total": open_sessions + closed_sessions
        },
                # PrÃƒÆ’Ã‚Â©senter sÃƒÆ’Ã‚Â©parÃƒÆ’Ã‚Â©ment chaque source de recettes.
        "revenue": {
            "payments": payment_revenue,
            "onboard_sales": onboard_revenue,
            "agency_sales": agency_revenue,
            "total": total_revenue
        },

        # Retourner la somme des ÃƒÆ’Ã‚Â©carts des caisses clÃƒÆ’Ã‚Â´turÃƒÆ’Ã‚Â©es.
        "cash_difference": total_difference,

        # Retourner le nombre rÃƒÆ’Ã‚Â©el de rectifications administratives.
        "rectifications": rectification_count

    }

# ============================================================
# V5.9 - TABLEAU DÃƒÆ’Ã¢â‚¬Â°TAILLÃƒÆ’Ã¢â‚¬Â° DES CAISSES
# ============================================================
# Cette route est rÃƒÆ’Ã‚Â©servÃƒÆ’Ã‚Â©e aux administrateurs.
# Elle prÃƒÆ’Ã‚Â©sente les recettes et les montants de chaque caisse.
# Les fonds initiaux ne sont pas comptÃƒÆ’Ã‚Â©s comme des recettes.


@app.get("/admin/dashboard/cash/sessions")
def admin_cash_sessions_dashboard(
    db: Session = Depends(get_db),
    user=Depends(roles("ADMIN"))
):
    # RÃƒÆ’Ã‚Â©cupÃƒÆ’Ã‚Â©rer toutes les caisses avec leur responsable.
    sessions = (
        db.query(CashSession, User.username)
        .join(User, User.id == CashSession.user_id)
        .order_by(CashSession.id.desc())
        .all()
    )

    results = []

    for session, username in sessions:

        # Calculer les paiements classiques rÃƒÆ’Ã‚Â©ussis.
        payments_amount = (
            db.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(
                Payment.cash_session_id == session.id,
                Payment.status == PaymentStatus.SUCCESS
            )
            .scalar()
        ) or 0

        # Calculer les ventes ÃƒÆ’Ã‚Â  bord de cette caisse.
        onboard_amount = (
            db.query(
                func.coalesce(
                    func.sum(OnboardSale59.total_amount), 0
                )
            )
            .filter(
                OnboardSale59.cash_session_id == session.id
            )
            .scalar()
        ) or 0

        # Additionner uniquement les recettes.
        # Calculer les ventes au guichet associÃƒÆ’Ã‚Â©es ÃƒÆ’Ã‚Â  cette caisse.
        # Les ventes ÃƒÆ’Ã‚Â  bord sont exclues pour ÃƒÆ’Ã‚Â©viter le double comptage.
        agency_amount = calculate_agency_revenue(
            db,
            cash_session_id=session.id
        )

        # Additionner les trois sources de recettes.
        total_revenue = payments_amount + onboard_amount + agency_amount

        # Calculer le montant thÃƒÆ’Ã‚Â©orique de la caisse.
        # SÃƒÆ’Ã‚Â©parer les recettes en espÃƒÆ’Ã‚Â¨ces du chiffre d'affaires total.
        # Les paiements ÃƒÆ’Ã‚Â©lectroniques ne doivent pas augmenter la caisse physique.
        recettes_par_provider = calculer_recettes_par_provider(
            db,
            cash_session_id=session.id
        )
        cash_revenue = recettes_par_provider.get("CASH", 0)

        # Fonds initial + encaissements en espÃƒÆ’Ã‚Â¨ces uniquement.
        theoretical_amount = (
            session.opening_amount + cash_revenue
        )

        # PrÃƒÆ’Ã‚Â©parer les donnÃƒÆ’Ã‚Â©es de la caisse.
        results.append({
            "cash_session_id": session.id,
            "username": username,
            "status": session.status,
            "opening_amount": session.opening_amount,
            "payments_revenue": payments_amount,
            "onboard_revenue": onboard_amount,
            "agency_revenue": agency_amount,
            "total_revenue": total_revenue,
            "theoretical_amount": theoretical_amount,
            "expected_amount": session.expected_amount,
            "declared_amount": session.declared_amount,
            "difference_amount": session.difference_amount,
            "opened_at": session.opened_at,
            "closed_at": session.closed_at
        })

    return {
        "currency": "XAF",
        "total_sessions": len(results),
        "sessions": results
    }


# ============================================================
# V5.9 - EXPORT EXCEL DE L'HISTORIQUE DES CAISSES
# ============================================================

@app.get("/admin/dashboard/cash/sessions/export.xlsx")
def export_cash_sessions_excel(
    agent: str = "",
    status: str = "",
    day: str = "",
    db: Session = Depends(get_db),
    user = Depends(roles("ADMIN"))
):
    # RÃƒÆ’Ã‚Â©cupÃƒÆ’Ã‚Â©rer les sessions ÃƒÆ’Ã‚Â  partir du tableau de bord existant.
    data = admin_cash_sessions_dashboard(db=db, user=user)
    sessions = data["sessions"]

    # Appliquer les filtres sÃƒÆ’Ã‚Â©lectionnÃƒÆ’Ã‚Â©s dans l'interface.
    if agent:
        sessions = [s for s in sessions if s["username"] == agent]

    if status:
        sessions = [s for s in sessions if s["status"] == status]

    if day:
        sessions = [
            s for s in sessions
            if s["opened_at"] is not None
            and s["opened_at"].date().isoformat() == day
        ]

    # CrÃƒÆ’Ã‚Â©er le classeur et sa feuille principale.
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Historique des caisses"

    # Ajouter le titre du rapport.
    sheet.merge_cells("A1:M1")
    sheet["A1"] = "BOUKOULOU TRANSPORT - HISTORIQUE DES CAISSES"
    sheet["A1"].font = Font(size=16, bold=True, color="FFFFFF")
    sheet["A1"].fill = PatternFill(
        fill_type="solid",
        fgColor="17365D"
    )
    sheet["A1"].alignment = Alignment(horizontal="center")
    sheet.row_dimensions[1].height = 32

    # Ajouter la date de gÃƒÆ’Ã‚Â©nÃƒÆ’Ã‚Â©ration et le nombre de sessions.
    sheet["A2"] = "Date de gÃƒÆ’Ã‚Â©nÃƒÆ’Ã‚Â©ration"
    sheet["B2"] = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    sheet["D2"] = "Sessions exportÃƒÆ’Ã‚Â©es"
    sheet["E2"] = len(sessions)

    # DÃƒÆ’Ã‚Â©finir les colonnes du rapport.
    headers = [
        "Caisse",
        "Responsable",
        "Ouverture",
        "ClÃƒÆ’Ã‚Â´ture",
        "Statut",
        "Fonds initial (XAF)",
        "Guichet (XAF)",
        "ÃƒÆ’Ã¢â€šÂ¬ bord (XAF)",
        "Autres paiements (XAF)",
        "Recettes (XAF)",
        "Attendu (XAF)",
        "DÃƒÆ’Ã‚Â©clarÃƒÆ’Ã‚Â© (XAF)",
        "ÃƒÆ’Ã¢â‚¬Â°cart (XAF)"
    ]

    header_row = 4

    for column, title in enumerate(headers, start=1):
        cell = sheet.cell(row=header_row, column=column, value=title)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(fill_type="solid", fgColor="237A57")
        cell.alignment = Alignment(horizontal="center")

    # Ajouter les donnÃƒÆ’Ã‚Â©es de chaque session.
    for row_number, session in enumerate(sessions, start=5):
        values = [
            session["cash_session_id"],
            session["username"],
            str(session["opened_at"] or ""),
            str(session["closed_at"] or ""),
            session["status"],
            session["opening_amount"],
            session["agency_revenue"],
            session["onboard_revenue"],
            session["payments_revenue"],
            session["total_revenue"],
            session["expected_amount"],
            session["declared_amount"],
            session["difference_amount"]
        ]

        for column, value in enumerate(values, start=1):
            cell = sheet.cell(
                row=row_number,
                column=column,
                value=value
            )

            # Appliquer le format numÃƒÆ’Ã‚Â©rique aux montants.
            if column >= 6:
                cell.number_format = '#,##0 "XAF";-#,##0 "XAF";0 "XAF"'

            # Mettre en ÃƒÆ’Ã‚Â©vidence les ÃƒÆ’Ã‚Â©carts non nuls.
            if column == 13 and value not in (None, 0):
                cell.font = Font(bold=True, color="C00000")

    # Ajouter une ligne de totaux avec des formules Excel.
    total_row = len(sessions) + 5
    sheet.cell(row=total_row, column=2, value="TOTAL")

    for column in range(6, 14):
        letter = get_column_letter(column)
        cell = sheet.cell(
            row=total_row,
            column=column,
            value=f"=SUM({letter}5:{letter}{total_row - 1})"
        )
        cell.number_format = '#,##0 "XAF";-#,##0 "XAF";0 "XAF"'

    # Mettre en ÃƒÆ’Ã‚Â©vidence les totaux.
    for cell in sheet[total_row]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(
            fill_type="solid",
            fgColor="17365D"
        )

    # Ajuster la largeur des colonnes.
    widths = [12, 20, 24, 24, 14, 22, 20, 20, 24, 20, 20, 20, 18]

    for column, width in enumerate(widths, start=1):
        sheet.column_dimensions[get_column_letter(column)].width = width

    # Ajouter des filtres automatiques et figer les en-tÃƒÆ’Ã‚Âªtes.
    sheet.auto_filter.ref = f"A4:M{max(4, total_row - 1)}"
    sheet.freeze_panes = "C5"

    # Enregistrer le classeur en mÃƒÆ’Ã‚Â©moire.
    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    # Retourner le fichier Excel ÃƒÆ’Ã‚Â  tÃƒÆ’Ã‚Â©lÃƒÆ’Ã‚Â©charger.
    filename = "boukoulou_historique_caisses.xlsx"

    return StreamingResponse(
        output,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


# ============================================================
# V5.9 - RAPPORT PDF INDIVIDUEL DE CLÃƒÆ’Ã¢â‚¬ÂTURE DE CAISSE
# ============================================================

@app.get("/admin/cash/sessions/{session_id}/report.pdf")
def export_cash_session_pdf(
    session_id: int,
    db: Session = Depends(get_db),
    user=Depends(roles("ADMIN"))
):
    # VÃƒÆ’Ã‚Â©rifier que la caisse existe et qu'elle est clÃƒÆ’Ã‚Â´turÃƒÆ’Ã‚Â©e.
    session = db.get(CashSession, session_id)

    if session is None:
        raise HTTPException(404, "Caisse introuvable")

    if session.status != "CLOSED":
        raise HTTPException(409, "La caisse doit ÃƒÆ’Ã‚Âªtre clÃƒÆ’Ã‚Â´turÃƒÆ’Ã‚Â©e")

    # RÃƒÆ’Ã‚Â©utiliser les donnÃƒÆ’Ã‚Â©es du tableau de bord financier.
    dashboard = admin_cash_sessions_dashboard(db=db, user=user)

    session_data = next(
        (
            item for item in dashboard["sessions"]
            if item["cash_session_id"] == session_id
        ),
        None,
    )

    if session_data is None:
        raise HTTPException(404, "DonnÃƒÆ’Ã‚Â©es de caisse introuvables")

    # RÃƒÆ’Ã‚Â©cupÃƒÆ’Ã‚Â©rer l'historique des rectifications.
    history = list_cash_rectifications(
        session_id=session_id,
        db=db,
        user=user,
    )

    # Construire le rapport PDF en mÃƒÆ’Ã‚Â©moire.
    pdf = generer_rapport_caisse(
        session_data,
        history["rectifications"],
    )

    # Transmettre le document au navigateur.
    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="boukoulou_caisse_{session_id}.pdf"'
            )
        },
    )

# ============================================================
# V5.9 - LIAISON SECURISEE COMPTE UTILISATEUR / CHAUFFEUR
# ============================================================

class DriverUserLinkIn(BaseModel):
    """Identifiant du compte utilisateur a associer au chauffeur."""
    user_id: int = Field(gt=0)


@app.put("/drivers/{driver_id}/user")
def link_driver_user(
    driver_id: int,
    data: DriverUserLinkIn,
    admin=Depends(roles("ADMIN")),
    db: Session=Depends(get_db)
):
    """
    Associe un compte DRIVER actif a une fiche chauffeur.
    Reserve aux administrateurs.
    """

    # Verifier que le chauffeur existe.
    driver = db.query(Driver).filter(
        Driver.id == driver_id
    ).with_for_update().first()

    if driver is None:
        raise HTTPException(404, "CHAUFFEUR_INTROUVABLE")

    # Verifier le compte utilisateur.
    account = db.get(User, data.user_id)

    if account is None:
        raise HTTPException(404, "COMPTE_INTROUVABLE")

    if not account.is_active or account.role != Role.DRIVER:
        raise HTTPException(409, "COMPTE_CHAUFFEUR_INVALIDE")

    # Verifier qu'un compte n'est pas utilise par un autre chauffeur.
    existing = db.query(Driver).filter(
        Driver.user_id == account.id,
        Driver.id != driver.id
    ).first()

    if existing:
        raise HTTPException(409, "COMPTE_DEJA_ASSOCIE")

    # Ne rien modifier si la liaison existe deja.
    if driver.user_id == account.id:
        return {
            "driver_id": driver.id,
            "user_id": account.id,
            "message": "LIAISON_DEJA_EXISTANTE"
        }

    # Interdire le remplacement direct d'un compte deja associe.
    # Une reaffectation devra utiliser une procedure distincte et auditee.
    if driver.user_id is not None:
        raise HTTPException(
            status_code=409,
            detail="CHAUFFEUR_DEJA_ASSOCIE"
        )

    # Enregistrer la nouvelle association.
    previous_user_id = driver.user_id

    try:
        driver.user_id = account.id

        # Journaliser la modification dans la meme transaction.
        db.add(Audit(
            username=admin.username,
            action="DRIVER_USER_LINKED",
            target=(
                f"driver={driver.id};"
                f"old_user={previous_user_id};"
                f"new_user={account.id}"
            )
        ))

        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "CONFLIT_ASSOCIATION_CHAUFFEUR")

    return {
        "driver_id": driver.id,
        "user_id": account.id,
        "username": account.username,
        "message": "COMPTE_CHAUFFEUR_ASSOCIE"
    }

app.include_router(gps_phone_router)

app.include_router(gps_device_router)

app.include_router(gps_fleet_router)
app.include_router(gps_live_router)
