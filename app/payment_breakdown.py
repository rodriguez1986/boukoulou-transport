"""Répartition des recettes réellement encaissées par moyen de paiement."""
from sqlalchemy import func
from sqlalchemy.orm import Session
from .models import Payment, PaymentStatus
from .v59 import Pass59


def calculer_recettes_par_provider(db: Session, cash_session_id=None):
    """Additionner les paiements validés et les ventes V5.9 sans double comptage."""
    # Les paiements historiques ne sont retenus qu'après validation.
    paiements = db.query(Payment.provider, func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.status == PaymentStatus.SUCCESS
    )
    # Les ventes V5.9 au guichet sont enregistrées directement dans les passes.
    ventes = db.query(Pass59.provider, func.coalesce(func.sum(Pass59.total), 0))
    if cash_session_id is not None:
        paiements = paiements.filter(Payment.cash_session_id == cash_session_id)
        ventes = ventes.filter(Pass59.cash_session_id == cash_session_id)
    resultats = {}
    for provider, montant in paiements.group_by(Payment.provider).all():
        cle = (provider or "INCONNU").upper()
        resultats[cle] = resultats.get(cle, 0) + int(montant or 0)
    for provider, montant in ventes.group_by(Pass59.provider).all():
        cle = (provider or "INCONNU").upper()
        resultats[cle] = resultats.get(cle, 0) + int(montant or 0)
    return resultats
