"""API administrative expérimentale, volontairement non montée dans main.py."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from .db import get_db
from .security import user
from .models import Role
from .crew_assignment_report_step59 import rapport_anomalies_affectations

router = APIRouter(prefix="/api/step60/crew-assignment-anomalies", tags=["step60-crew-audit"])

@router.get("")
def lire_anomalies(
    limit: int = Query(default=100, ge=1, le=500),
    after_id: int = Query(default=0, ge=0),
    utilisateur=Depends(user),
    db: Session = Depends(get_db),
):
    # JWT validé par security.user, compte actif et token_version vérifiés.
    role = getattr(utilisateur.role, "value", utilisateur.role)
    if role == Role.ADMIN.value:
        country_id = None
    elif role == Role.COUNTRY_MANAGER.value and type(utilisateur.country_id) is int and utilisateur.country_id > 0:
        country_id = utilisateur.country_id
    else:
        raise HTTPException(status_code=403, detail="Accès refusé")
    return rapport_anomalies_affectations(db, limit=limit, after_id=after_id, country_id=country_id)
