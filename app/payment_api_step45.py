"""Étape 45 : routeur FastAPI de PRÉVISUALISATION des droits.

Non monté dans main.py. Authentification JWT de l'application requise.
Aucun effet de bord financier, aucun appel PSP ni modification en base.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .db import get_db
from .models import Country
from .security import user
from .payment_access_step44 import (
    IdentiteHabilitee, OperationPaiement, verifier_autorisation,
    CAISSIER, AGENT_BUS, SUPERVISEUR, AUDITEUR,
)

router = APIRouter(prefix="/api/step45/payment-access", tags=["step45-payment-access"])

class OperationAExaminer(BaseModel):
    pays: str
    canal: str
    moyen: str
    action: str

# Association restrictive des rôles existants aux rôles métier de l'étape 44.
# Le rôle PSP n'est PAS attribué à un compte humain.
_ROLE_MAP = {
    "AGENT": CAISSIER,
    "DRIVER": AGENT_BUS,
    "COUNTRY_MANAGER": SUPERVISEUR,
    "CONTROLLER": AGENT_BUS,  # Encaissement espèces à bord, comme DRIVER
}
_CHANNELS = {
    CAISSIER: frozenset({"AGENCE"}),
    AGENT_BUS: frozenset({"BUS"}),
    SUPERVISEUR: frozenset({"AGENCE", "BUS", "EN_LIGNE"}),
    AUDITEUR: frozenset({"AGENCE", "BUS", "EN_LIGNE"}),
}


def construire_identite_depuis_utilisateur(u, pays, country_code):
    """Construit une identité depuis un objet utilisateur serveur vérifié.

    country_code vient de la base, jamais d'un champ fourni par le client.
    Refuse les rôles sans correspondance et les utilisateurs sans pays.
    """
    role_original = getattr(getattr(u, "role", None), "value", None)
    role = _ROLE_MAP.get(role_original)
    if role is None or not getattr(u, "is_active", False):
        raise HTTPException(status_code=403, detail="Rôle ou compte non autorisé")
    if country_code not in ("CG", "GA") or pays != country_code:
        raise HTTPException(status_code=403, detail="Pays hors périmètre")
    if not getattr(u, "username", None):
        raise HTTPException(status_code=403, detail="Identité invalide")
    return IdentiteHabilitee(
        identifiant=str(u.username), role=role,
        pays_autorises=frozenset({country_code}),
        canaux_autorises=_CHANNELS[role],
        active=True, authentifiee=True,
    )


def verifier_operation_authentifiee(u, db, donnees):
    """Contrôle pays via FK utilisateur→Country, puis politique de droits."""
    if not isinstance(donnees, OperationAExaminer):
        raise HTTPException(status_code=400, detail="Opération invalide")
    country_id = getattr(u, "country_id", None)
    if country_id is None:
        raise HTTPException(status_code=403, detail="Aucun pays affecté")
    pays = db.get(Country, country_id)
    if pays is None:
        raise HTTPException(status_code=403, detail="Pays affecté introuvable")
    identite = construire_identite_depuis_utilisateur(u, donnees.pays, pays.code)
    operation = OperationPaiement(
        pays=donnees.pays, canal=donnees.canal,
        moyen=donnees.moyen, action=donnees.action)
    decision = verifier_autorisation(identite, operation)
    if not decision["autorise"]:
        raise HTTPException(status_code=403, detail="Opération non autorisée")
    return {"autorise": True, "operation_executee": False,
            "paiement_reel_confirme": False,
            "pays": decision["pays"], "canal": decision["canal"],
            "moyen": decision["moyen"], "action": decision["action"]}


@router.post("/verifier")
def verifier_operation_route(
    donnees: OperationAExaminer,
    utilisateur=Depends(user),
    db: Session=Depends(get_db),
):
    return verifier_operation_authentifiee(utilisateur, db, donnees)
