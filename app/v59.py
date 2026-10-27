from sqlalchemy.dialects.postgresql import insert as pg_insert
"""V5.9 - Stock administrateur, ventes multi-voyages et embarquement par QR."""
import uuid
from datetime import datetime, timezone, timedelta
from calendar import monthrange
from zoneinfo import ZoneInfo
from io import BytesIO
import qrcode
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import Integer, String, DateTime, ForeignKey, CheckConstraint, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, Session
from .db import Base, get_db
from .models import Country, Line, Trip, Ticket, TicketStatus, User, CashSession, Audit, Driver, TripController
from .security import roles, sign_qr, check_qr, verifier_acces_pays

router = APIRouter(prefix='/v59', tags=['V5.9 - Billetterie multi-voyages'])

class CountryFees59(Base):
    """Frais V5.9 configurables par pays, appliqués par billet."""
    __tablename__ = 'v59_country_fees'
    __table_args__ = (
        UniqueConstraint('country_id', name='uq_v59_country_fees_country'),
        CheckConstraint(
            'onboard_fee >= 0 AND printing_fee >= 0',
            name='ck_v59_country_fees_nonnegative'
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    country_id: Mapped[int] = mapped_column(
        ForeignKey('countries.id'), nullable=False
    )
    onboard_fee: Mapped[int] = mapped_column(Integer, nullable=False)
    printing_fee: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_by: Mapped[int] = mapped_column(
        ForeignKey('users.id'), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

class Stock59(Base):
    __tablename__ = 'v59_stocks'
    __table_args__ = (CheckConstraint('created >= 0 AND available >= 0 AND available <= created', name='ck_v59_stock'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    country_id: Mapped[int] = mapped_column(ForeignKey('countries.id'), nullable=False)
    fare: Mapped[int] = mapped_column(Integer, nullable=False)
    created: Mapped[int] = mapped_column(Integer, nullable=False)
    available: Mapped[int] = mapped_column(Integer, nullable=False)
    admin_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Pass59(Base):
    __tablename__ = 'v59_passes'
    __table_args__ = (CheckConstraint('remaining >= 0 AND remaining <= quantity', name='ck_v59_remaining'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    stock_id: Mapped[int] = mapped_column(ForeignKey('v59_stocks.id'), nullable=False)
    country_id: Mapped[int] = mapped_column(ForeignKey('countries.id'), nullable=False)
    fare: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining: Mapped[int] = mapped_column(Integer, nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    cash_session_id: Mapped[int] = mapped_column(ForeignKey('cash_sessions.id'), nullable=False)
    reference: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    sold_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

class Boarding59(Base):
    __tablename__ = 'v59_boardings'
    id: Mapped[int] = mapped_column(primary_key=True)
    pass_id: Mapped[int] = mapped_column(ForeignKey('v59_passes.id'), nullable=False)
    trip_id: Mapped[int] = mapped_column(ForeignKey('trips.id'), nullable=False)
    controller_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    boarded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    remaining_after: Mapped[int] = mapped_column(Integer, nullable=False)

class OnboardSale59(Base):
    """Trace comptable d'une vente V5.9 à bord, liée à un titre existant.

    Les montants enregistrés sont ceux de la transaction d'origine ; ce modèle
    n'invente pas les frais et ne déclenche aucune vente à lui seul.
    """
    __tablename__ = 'v59_onboard_sales'
    __table_args__ = (
        UniqueConstraint('pass_id', name='uq_v59_onboard_pass'),
        CheckConstraint('total_amount >= 0', name='ck_v59_onboard_total_nonnegative'),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    pass_id: Mapped[int] = mapped_column(ForeignKey('v59_passes.id'), nullable=False)
    trip_id: Mapped[int] = mapped_column(ForeignKey('trips.id'), nullable=False)
    controller_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    cash_session_id: Mapped[int] = mapped_column(ForeignKey('cash_sessions.id'), nullable=False)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    transport_amount: Mapped[int] = mapped_column(Integer, nullable=True)
    onboard_fee: Mapped[int] = mapped_column(Integer, nullable=False)
    printing_fee: Mapped[int] = mapped_column(Integer, nullable=False)
    sold_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CountryFeesIn(BaseModel):
    """Frais configurables par pays, appliques par billet."""
    onboard_fee: int = Field(ge=0)
    printing_fee: int = Field(ge=0)

class StockIn(BaseModel):
    country_id: int
    fare: int = Field(gt=0)
    quantity: int = Field(ge=1, le=100000)

class SaleIn(BaseModel):
    stock_id: int
    quantity: int = Field(ge=1, le=100)
    provider: str = Field(default='CASH', min_length=1, max_length=40)

class OnboardSaleIn(BaseModel):
    trip_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=100)
    print_ticket: bool = False


class BoardingIn(BaseModel):
    code: str
    signature: str
    trip_id: int

# Fuseaux des deux réseaux ; la fin du mois est calculée localement.
TZ = {'CG': 'Africa/Brazzaville', 'GA': 'Africa/Libreville'}

def expiry(country_code, now):
    local = now.astimezone(ZoneInfo(TZ[country_code]))
    last = monthrange(local.year, local.month)[1]
    end = local.replace(day=last, hour=23, minute=59, second=59, microsecond=999999)
    return end.astimezone(timezone.utc)

def public_pass(p):
    now = datetime.now(timezone.utc)
    exp = p.valid_until if p.valid_until.tzinfo else p.valid_until.replace(tzinfo=timezone.utc)
    return {'id':p.id, 'code':p.code, 'country_id':p.country_id, 'fare':p.fare,
            'quantity':p.quantity, 'remaining':p.remaining, 'total':p.total,
            'sold_at':p.sold_at, 'valid_until':p.valid_until,
            'status':'EXPIRED' if now > exp else ('USED' if p.remaining == 0 else 'ACTIVE')}

@router.get('/country-fees/{country_id}')
def get_country_fees(
    country_id: int,
    u=Depends(roles('ADMIN', 'COUNTRY_MANAGER')),
    db: Session = Depends(get_db),
):
    verifier_acces_pays(u, country_id)

    country = db.get(Country, country_id)
    if country is None:
        raise HTTPException(404, 'Pays introuvable')

    fees = db.query(CountryFees59).filter(
        CountryFees59.country_id == country_id
    ).first()

    if fees is None:
        return {
            'country_id': country_id,
            'configured': False,
            'onboard_fee': None,
            'printing_fee': None,
        }

    return {
        'country_id': country_id,
        'configured': True,
        'onboard_fee': fees.onboard_fee,
        'printing_fee': fees.printing_fee,
        'updated_by': fees.updated_by,
        'updated_at': fees.updated_at,
    }

@router.put('/country-fees/{country_id}')
def update_country_fees(
    country_id: int,
    x: CountryFeesIn,
    u=Depends(roles('ADMIN', 'COUNTRY_MANAGER')),
    db: Session = Depends(get_db),
):
    verifier_acces_pays(u, country_id)

    country = db.get(Country, country_id)
    if country is None:
        raise HTTPException(404, 'Pays introuvable')

    now = datetime.now(timezone.utc)

    stmt = pg_insert(CountryFees59).values(
        country_id=country_id,
        onboard_fee=x.onboard_fee,
        printing_fee=x.printing_fee,
        updated_by=u.id,
        updated_at=now,
    )

    stmt = stmt.on_conflict_do_update(
        constraint='uq_v59_country_fees_country',
        set_={
            'onboard_fee': stmt.excluded.onboard_fee,
            'printing_fee': stmt.excluded.printing_fee,
            'updated_by': stmt.excluded.updated_by,
            'updated_at': stmt.excluded.updated_at,
        },
    ).returning(CountryFees59.id)

    try:
        fees_id = db.execute(stmt).scalar_one()
        db.commit()
    except Exception:
        db.rollback()
        raise

    fees = db.get(CountryFees59, fees_id)

    return {
        'country_id': fees.country_id,
        'configured': True,
        'onboard_fee': fees.onboard_fee,
        'printing_fee': fees.printing_fee,
        'updated_by': fees.updated_by,
        'updated_at': fees.updated_at,
    }


@router.post('/stocks', status_code=201)
def create_stock(x: StockIn, admin=Depends(roles('ADMIN')), db: Session=Depends(get_db)):
    if not db.get(Country, x.country_id):
        raise HTTPException(404, 'Pays introuvable')
    s = Stock59(country_id=x.country_id, fare=x.fare, created=x.quantity,
                available=x.quantity, admin_id=admin.id)
    db.add(s)
    db.add(Audit(username=admin.username, action='V59_CREATE_STOCK', target=f'{x.country_id}:{x.fare}:{x.quantity}'))
    db.commit(); db.refresh(s)
    return {'id':s.id, 'country_id':s.country_id, 'fare':s.fare, 'created':s.created, 'available':s.available}

@router.get('/stocks')
def stocks(u=Depends(roles('ADMIN','AGENT')), db: Session=Depends(get_db)):
    return [{'id':s.id,'country_id':s.country_id,'fare':s.fare,'created':s.created,
             'available':s.available,'sold':s.created-s.available} for s in db.query(Stock59).order_by(Stock59.id.desc()).all()]

@router.post('/sales', status_code=201)
def sell(x: SaleIn, agent=Depends(roles('AGENT')), db: Session=Depends(get_db)):
    # Le verrou PostgreSQL interdit deux ventes du même stock au-delà du disponible.
    s = db.query(Stock59).filter(Stock59.id==x.stock_id).with_for_update().first()
    if not s: raise HTTPException(404, 'Stock introuvable')
    if s.available < x.quantity: raise HTTPException(409, 'STOCK_INSUFFICIENT')
    cash = db.query(CashSession).filter(CashSession.user_id==agent.id, CashSession.status=='OPEN').order_by(CashSession.id.desc()).first()
    if not cash: raise HTTPException(409, 'CASH_NOT_OPEN : ouvrez votre caisse')
    country = db.get(Country, s.country_id)
    if country.code not in TZ: raise HTTPException(409, 'Pays non pris en charge')
    now = datetime.now(timezone.utc)
    p = Pass59(code='BT-'+uuid.uuid4().hex.upper(), stock_id=s.id, country_id=s.country_id,
               fare=s.fare, quantity=x.quantity, remaining=x.quantity, total=s.fare*x.quantity,
               agent_id=agent.id, cash_session_id=cash.id, reference='V59-'+uuid.uuid4().hex.upper(),
               provider=x.provider, sold_at=now, valid_until=expiry(country.code, now))
    s.available -= x.quantity
    db.add(p); db.flush()
    db.add(Audit(username=agent.username, action='V59_SALE', target=p.code))
    db.commit(); db.refresh(p)
    return {**public_pass(p), 'signature':sign_qr(p.code), 'reference':p.reference}

@router.get('/passes/{code}')
def get_pass(code: str, u=Depends(roles('ADMIN','AGENT','CONTROLLER')), db: Session=Depends(get_db)):
    p=db.query(Pass59).filter_by(code=code).first()
    if not p: raise HTTPException(404, 'Titre introuvable')
    return public_pass(p)

@router.get('/passes/{code}/qr')
def pass_qr(code: str, u=Depends(roles('ADMIN','AGENT')), db: Session=Depends(get_db)):
    p=db.query(Pass59).filter_by(code=code).first()
    if not p: raise HTTPException(404, 'Titre introuvable')
    img=qrcode.make(f'{p.code}|{sign_qr(p.code)}'); b=BytesIO(); img.save(b,'PNG'); b.seek(0)
    return StreamingResponse(b, media_type='image/png')

@router.post('/onboard-sales', status_code=201)
def sell_onboard(
    x: OnboardSaleIn,
    seller=Depends(roles('DRIVER', 'CONTROLLER')),
    db: Session=Depends(get_db)
):
    # Verrouiller la course pour stabiliser son statut et son affectation.
    trip = db.query(Trip).filter(
        Trip.id == x.trip_id
    ).with_for_update().first()

    if not trip:
        raise HTTPException(404, 'Course introuvable')

    role = seller.role.value if hasattr(seller.role, 'value') else str(seller.role)

    if role == 'DRIVER':
        assigned = db.query(Driver.id).filter(
            Driver.id == trip.driver_id,
            Driver.user_id == seller.id
        ).first() is not None
    elif role == 'CONTROLLER':
        assigned = db.query(TripController.id).filter(
            TripController.trip_id == trip.id,
            TripController.controller_id == seller.id
        ).first() is not None
    else:
        assigned = False

    if not assigned:
        raise HTTPException(404, 'Course introuvable')

    if trip.status not in ('SCHEDULED', 'IN_PROGRESS'):
        raise HTTPException(409, 'COURSE_INDISPONIBLE')

    line = trip.line

    if not line or line.fare <= 0:
        raise HTTPException(409, 'TARIF_INVALIDE')

    # Verrouiller la caisse pour empecher une cloture simultanee.
    cash = db.query(CashSession).filter(
        CashSession.user_id == seller.id,
        CashSession.status == 'OPEN'
    ).with_for_update().first()

    if not cash:
        raise HTTPException(409, 'CASH_NOT_OPEN')

    # Utiliser exclusivement le stock correspondant au tarif de la course.
    stock = db.query(Stock59).filter(
        Stock59.country_id == line.country_id,
        Stock59.fare == line.fare,
        Stock59.available >= x.quantity
    ).order_by(Stock59.id).with_for_update().first()

    if not stock:
        raise HTTPException(409, 'STOCK_INSUFFICIENT')

    country = db.get(Country, line.country_id)

    if not country or country.code not in TZ:
        raise HTTPException(409, 'Pays non pris en charge')

    # Les frais nationaux doivent etre configures avant toute vente a bord.
    fees = db.query(CountryFees59).filter(
        CountryFees59.country_id == line.country_id
    ).first()

    if fees is None:
        raise HTTPException(409, 'FRAIS_PAYS_NON_CONFIGURES')

    onboard_fee = fees.onboard_fee
    printing_fee = fees.printing_fee if x.print_ticket else 0

    now = datetime.now(timezone.utc)

    transport_amount = line.fare * x.quantity

    amount = (
        line.fare + onboard_fee + printing_fee
    ) * x.quantity

    p = Pass59(
        code='BT-' + uuid.uuid4().hex.upper(),
        stock_id=stock.id,
        country_id=line.country_id,
        fare=line.fare,
        quantity=x.quantity,
        remaining=x.quantity,
        total=amount,
        agent_id=seller.id,
        cash_session_id=cash.id,
        reference='V59-BORD-' + uuid.uuid4().hex.upper(),
        provider='CASH',
        sold_at=now,
        valid_until=expiry(country.code, now)
    )

    stock.available -= x.quantity

    db.add(p)
    db.flush()

    db.add(OnboardSale59(
        pass_id=p.id,
        trip_id=trip.id,
        controller_id=seller.id,
        cash_session_id=cash.id,
        total_amount=amount,
        transport_amount=transport_amount,
        onboard_fee=onboard_fee,
        printing_fee=printing_fee,
        sold_at=now
    ))

    db.add(Audit(
        username=seller.username,
        action='V59_ONBOARD_SALE',
        target=f'{p.code}:{trip.id}:{amount}'
    ))

    db.commit()
    db.refresh(p)

    return {
        **public_pass(p),
        'signature': sign_qr(p.code),
        'reference': p.reference,
        'trip_id': trip.id,
        'cash_session_id': cash.id,
        'provider': 'CASH',
        'unit_fare': line.fare,
        'onboard_fee': onboard_fee,
        'printing_fee': printing_fee,
        'print_ticket': x.print_ticket,
        'total_amount': amount
    }

@router.post('/boardings')
def boarding(x: BoardingIn, controller=Depends(roles('CONTROLLER','DRIVER')), db: Session=Depends(get_db)):
    if not check_qr(x.code,x.signature): raise HTTPException(403, 'QR_INVALID')
    # Verrouiller d'abord la course, puis le titre, dans cet ordre pour tous les contrôles.
    trip=db.query(Trip).filter(Trip.id==x.trip_id).with_for_update().first()
    if not trip: raise HTTPException(404, 'Course introuvable')
    # Un chauffeur ou controleur ne peut intervenir que sur une course affectee.
    role = controller.role.value if hasattr(controller.role, 'value') else str(controller.role)
    if role == 'DRIVER':
        affecte = db.query(Driver.id).filter(
            Driver.id == trip.driver_id,
            Driver.user_id == controller.id
        ).first() is not None
    elif role == 'CONTROLLER':
        affecte = db.query(TripController.id).filter(
            TripController.trip_id == trip.id,
            TripController.controller_id == controller.id
        ).first() is not None
    else:
        affecte = False
    if not affecte:
        raise HTTPException(404, 'Course introuvable')
    if trip.status not in ('SCHEDULED','IN_PROGRESS'): raise HTTPException(409, 'COURSE_INDISPONIBLE')
    p=db.query(Pass59).filter(Pass59.code==x.code).with_for_update().first()
    if not p: raise HTTPException(404, 'Titre introuvable')
    now=datetime.now(timezone.utc)
    exp=p.valid_until if p.valid_until.tzinfo else p.valid_until.replace(tzinfo=timezone.utc)
    if now>exp: raise HTTPException(409, 'BILLET_EXPIRE')
    if p.remaining<=0: raise HTTPException(409, 'SOLDE_EPUISE')
    if p.country_id!=trip.line.country_id or p.fare!=trip.line.fare:
        raise HTTPException(409, 'TARIF_OU_PAYS_INCOMPATIBLE')
    capacity=trip.vehicle.capacity+trip.vehicle.standing_capacity
    # Inclure les anciens billets réservés/payés et les nouveaux embarquements.
    legacy=(db.query(func.count(Ticket.id)).filter(Ticket.trip_id==trip.id,
        (Ticket.status.in_([TicketStatus.PAID,TicketStatus.USED]) |
         ((Ticket.status==TicketStatus.PENDING)&(Ticket.expires_at>now)))).scalar() or 0)
    newer=db.query(func.count(Boarding59.id)).filter(Boarding59.trip_id==trip.id).scalar() or 0
    if legacy+newer>=capacity: raise HTTPException(409, 'BUS_FULL')
    p.remaining-=1
    db.add(Boarding59(pass_id=p.id,trip_id=trip.id,controller_id=controller.id,
                      boarded_at=now,remaining_after=p.remaining))
    db.add(Audit(username=controller.username,action='V59_BOARD',target=f'{p.code}:{trip.id}'))
    db.commit()
    return {'valid':True,'code':p.code,'trip_id':trip.id,'remaining':p.remaining,
            'places_restantes':capacity-legacy-newer-1}

@router.get('/boardings')
def boardings(u=Depends(roles('ADMIN')), db: Session=Depends(get_db)):
    return [{'id':b.id,'pass_id':b.pass_id,'trip_id':b.trip_id,'controller_id':b.controller_id,
             'boarded_at':b.boarded_at,'remaining_after':b.remaining_after}
            for b in db.query(Boarding59).order_by(Boarding59.id.desc()).limit(500).all()]
