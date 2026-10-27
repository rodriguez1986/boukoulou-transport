"""Routeur de reconstruction : aperçu financier en lecture seule, réservé à ADMIN."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .db import get_db
from .security import roles
from .models import CashSession
from .payment_breakdown import calculer_recettes_par_provider

router = APIRouter(prefix='/finance', tags=['Finances (reconstruction)'])

@router.get('/summary')
def resume_financier(db: Session = Depends(get_db), admin=Depends(roles('ADMIN'))):
    """Synthèse informative ; ne remplace pas le tableau financier historique."""
    sessions = db.query(CashSession).all()
    return {
        'sessions_total': len(sessions),
        'sessions_ouvertes': sum(s.status == 'OPEN' for s in sessions),
        'sessions_cloturees': sum(s.status == 'CLOSED' for s in sessions),
        'recettes_par_moyen': calculer_recettes_par_provider(db),
        'reconstruction_partielle': True,
    }
