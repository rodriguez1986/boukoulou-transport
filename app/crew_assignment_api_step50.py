"""API expérimentale pour affectations : non montée dans main.py.

L'acteur provient de la dépendance JWT serveur; ne jamais accepter actor_id
comme paramètre du client. L'autorisation et l'audit sont dans le service 49.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .db import get_db
from .security import user
from .crew_assignment_admin_step49 import (
    AffectationRefusee, attribuer, retirer, consulter,
)

router = APIRouter(prefix="/api/step50/crew-assignments", tags=["step50-crew-assignments"])

class AttributionPayload(BaseModel):
    target_user_id: int = Field(gt=0)
    trip_id: int = Field(gt=0)
    starts_at: datetime
    ends_at: datetime | None = None

class RetraitPayload(BaseModel):
    assignment_id: int = Field(gt=0)


def _acteur_id(utilisateur):
    # La dépendance security.user doit déjà avoir authentifié le JWT.
    uid = getattr(utilisateur, "id", None)
    if type(uid) is not int or uid <= 0:
        raise HTTPException(status_code=401, detail="Session invalide")
    return uid


def _operation(fn):
    try:
        return fn()
    except AffectationRefusee:
        # Pas de divulgation de l'existence des utilisateurs, voyages,
        # affectations, ni des règles internes d'autorisation.
        raise HTTPException(status_code=403, detail="Opération non autorisée")


@router.post("", status_code=status.HTTP_201_CREATED)
def creer_affectation(
    payload: AttributionPayload, utilisateur=Depends(user), db: Session=Depends(get_db)
):
    actor_id = _acteur_id(utilisateur)
    identifiant = _operation(lambda: attribuer(
        db, actor_id=actor_id, target_user_id=payload.target_user_id,
        trip_id=payload.trip_id, starts_at=payload.starts_at,
        ends_at=payload.ends_at))
    return {"assignment_id": identifiant, "action": "ATTRIBUER"}


@router.post("/retirer")
def retirer_affectation(
    payload: RetraitPayload, utilisateur=Depends(user), db: Session=Depends(get_db)
):
    actor_id = _acteur_id(utilisateur)
    _operation(lambda: retirer(db, actor_id=actor_id,
                              assignment_id=payload.assignment_id))
    return {"retire": True}


@router.get("/voyage/{trip_id}")
def consulter_affectations(
    trip_id: int, utilisateur=Depends(user), db: Session=Depends(get_db)
):
    actor_id = _acteur_id(utilisateur)
    if trip_id <= 0:
        raise HTTPException(status_code=422, detail="Voyage invalide")
    rows = _operation(lambda: consulter(db, actor_id=actor_id, trip_id=trip_id))
    return {"affectations": list(rows)}
