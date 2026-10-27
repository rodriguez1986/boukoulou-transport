"""Étape 38 — catalogue et règles de paiement Boukoulou Transport.

Routage métier uniquement : aucun encaissement, aucun PSP connecté.
Les pays sont ceux de l'agence/vente concernée (CG=République du Congo,
GA=Gabon), pas une inférence à partir de la nationalité du voyageur.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional

CONGO = "CG"
GABON = "GA"
AGENCE = "AGENCE"
BUS = "BUS"
EN_LIGNE = "EN_LIGNE"
ESPECES = "ESPECES"
AIRTEL_MONEY = "AIRTEL_MONEY"
MTN_MOMO = "MTN_MOMO"
MOOV_MONEY = "MOOV_MONEY"

# Configuration métier validée par le demandeur.
MOYENS_AUTORISES = {
    (CONGO, AGENCE): (ESPECES,),
    (CONGO, BUS): (ESPECES,),
    (CONGO, EN_LIGNE): (AIRTEL_MONEY, MTN_MOMO),
    (GABON, AGENCE): (ESPECES,),
    (GABON, BUS): (ESPECES,),
    (GABON, EN_LIGNE): (AIRTEL_MONEY, MOOV_MONEY),
}
DEVISE = {CONGO: "XAF", GABON: "XAF"}


@dataclass(frozen=True)
class DemandePaiement:
    pays: str
    canal: str
    moyen: str
    montant: object
    devise: str = "XAF"


def moyens_disponibles(pays, canal):
    """Liste déterministe; tuple vide pour une combinaison inconnue."""
    if not isinstance(pays, str) or not isinstance(canal, str):
        return ()
    return MOYENS_AUTORISES.get((pays, canal), ())


def verifier_demande_paiement(demande):
    """Validation sans effet de bord, sans créer de paiement ni réservation."""
    motifs = []
    if not isinstance(demande, DemandePaiement):
        return {"autorise_par_regles_metier": False, "motifs": ["DEMANDE_INVALIDE"],
                "transaction_executee": False, "psp_connecte": False}
    if demande.pays not in DEVISE:
        motifs.append("PAYS_NON_PRIS_EN_CHARGE")
    if demande.canal not in (AGENCE, BUS, EN_LIGNE):
        motifs.append("CANAL_NON_PRIS_EN_CHARGE")
    if not isinstance(demande.moyen, str) or demande.moyen not in (
        ESPECES, AIRTEL_MONEY, MTN_MOMO, MOOV_MONEY
    ):
        motifs.append("MOYEN_INCONNU")
    elif demande.moyen not in moyens_disponibles(demande.pays, demande.canal):
        motifs.append("MOYEN_INTERDIT_POUR_PAYS_ET_CANAL")
    if demande.devise != "XAF":
        motifs.append("DEVISE_NON_AUTORISEE")
    # Exclure les floats : éviter les arrondis binaires dans les montants financiers.
    if isinstance(demande.montant, bool) or not isinstance(
        demande.montant, (int, str, Decimal)
    ):
        motifs.append("MONTANT_INVALIDE")
    else:
        try:
            montant = Decimal(str(demande.montant))
            if not montant.is_finite() or montant <= 0 or montant != montant.to_integral_value():
                motifs.append("MONTANT_INVALIDE")
        except (InvalidOperation, ValueError):
            motifs.append("MONTANT_INVALIDE")
    return {
        "autorise_par_regles_metier": not motifs,
        "motifs": motifs,
        "pays": demande.pays,
        "canal": demande.canal,
        "moyen": demande.moyen,
        "devise": demande.devise,
        "transaction_executee": False,
        "psp_connecte": False,
        "recu_emis": False,
    }


def preparer_intention_paiement(demande):
    """Préparer une intention *non persistée* si les règles métier passent."""
    validation = verifier_demande_paiement(demande)
    if not validation["autorise_par_regles_metier"]:
        return {"intention_preparee": False, "validation": validation, "intention": None}
    return {
        "intention_preparee": True,
        "validation": validation,
        "intention": {
            "pays": demande.pays,
            "canal": demande.canal,
            "moyen": demande.moyen,
            "montant_xaf": int(Decimal(str(demande.montant))),
            "devise": "XAF",
            "statut": "NON_EXECUTEE",
            "necessite_confirmation_externe": demande.canal == EN_LIGNE,
            "necessite_validation_caissier": demande.canal in (AGENCE, BUS),
        },
    }
