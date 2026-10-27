"""Étape 39 : cycle de vie simulé d'un paiement de billet, sans effet de bord.

Ce module ne constitue PAS un processeur de paiements réel.
"""
from dataclasses import dataclass
from app.payment_routing_step38 import (
    DemandePaiement, preparer_intention_paiement, EN_LIGNE, AGENCE, BUS
)

EN_ATTENTE = "EN_ATTENTE"
CONFIRME = "CONFIRME"
ECHOUE = "ECHOUE"
ANNULE = "ANNULE"

@dataclass(frozen=True)
class SimulationPaiement:
    pays: str
    canal: str
    moyen: str
    montant_xaf: int
    statut: str
    reference_billet: str
    reference_confirmation: str = ""


def demarrer_simulation(demande, reference_billet):
    """Prépare une simulation à partir d'une demande validée ; aucune réservation créée."""
    preparation = preparer_intention_paiement(demande)
    if not preparation['intention_preparee']:
        return {'ok': False, 'motifs': preparation['validation']['motifs'], 'paiement': None}
    if not isinstance(reference_billet, str) or not reference_billet.strip():
        return {'ok': False, 'motifs': ['REFERENCE_BILLET_INVALIDE'], 'paiement': None}
    intention = preparation['intention']
    return {'ok': True, 'motifs': [], 'paiement': SimulationPaiement(
        pays=intention['pays'], canal=intention['canal'], moyen=intention['moyen'],
        montant_xaf=intention['montant_xaf'], statut=EN_ATTENTE,
        reference_billet=reference_billet.strip()
    )}


def simuler_transition(paiement, nouvel_etat, *, acteur, reference_confirmation=''):
    """Retourne un nouvel objet ; aucun changement de base ou encaissement.

    acteur = CAISSIER pour agence/bus, PSP_SIMULE pour vente en ligne.
    Un résultat PSP simulé ne peut jamais confirmer un vrai paiement.
    """
    if not isinstance(paiement, SimulationPaiement):
        return {'ok': False, 'motifs': ['PAIEMENT_INVALIDE'], 'paiement': None}
    if paiement.statut != EN_ATTENTE:
        return {'ok': False, 'motifs': ['ETAT_TERMINAL'], 'paiement': paiement}
    if nouvel_etat not in (CONFIRME, ECHOUE, ANNULE):
        return {'ok': False, 'motifs': ['TRANSITION_INTERDITE'], 'paiement': paiement}
    if nouvel_etat == CONFIRME:
        attendu = 'PSP_SIMULE' if paiement.canal == EN_LIGNE else 'CAISSIER'
        if acteur != attendu:
            return {'ok': False, 'motifs': ['ACTEUR_NON_AUTORISE'], 'paiement': paiement}
        if not isinstance(reference_confirmation, str) or not reference_confirmation.strip():
            return {'ok': False, 'motifs': ['REFERENCE_CONFIRMATION_OBLIGATOIRE'], 'paiement': paiement}
    else:
        attendu = 'PSP_SIMULE' if paiement.canal == EN_LIGNE else 'CAISSIER'
        if acteur != attendu:
            return {'ok': False, 'motifs': ['ACTEUR_NON_AUTORISE'], 'paiement': paiement}
    nouveau = SimulationPaiement(
        pays=paiement.pays, canal=paiement.canal, moyen=paiement.moyen,
        montant_xaf=paiement.montant_xaf, statut=nouvel_etat,
        reference_billet=paiement.reference_billet,
        reference_confirmation=reference_confirmation.strip() if nouvel_etat == CONFIRME else ''
    )
    return {'ok': True, 'motifs': [], 'paiement': nouveau,
            'paiement_reel_confirme': False, 'billet_emis': False,
            'base_modifiee': False, 'transaction_executee': False}
