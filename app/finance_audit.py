"""Audit de caisse conservateur, lecture seule, réservé à ADMIN."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .db import get_db
from .security import roles
from .models import CashSession

router = APIRouter(prefix='/finance/audit', tags=['Audit financier (reconstruction)'])

@router.get('/cash-anomalies')
def anomalies_caisses(db: Session = Depends(get_db), admin=Depends(roles('ADMIN'))):
    """Signale uniquement les écarts de caisse clôturée connus ; pas un audit exhaustif."""
    anomalies = []
    for session in db.query(CashSession).filter(CashSession.status == 'CLOSED').all():
        ecart = session.difference_amount
        if ecart is not None and ecart != 0:
            anomalies.append({'cash_session_id': session.id, 'difference_amount': ecart,
                              'type': 'ECART_CAISSE'})
    return {'anomalies': anomalies, 'nombre': len(anomalies), 'audit_exhaustif': False}
