"""Étape 44 — règles d'autorisation métier, sans authentification ni écriture.

L'identité et ses habilitations doivent être obtenues d'un service
d'authentification fiable, jamais des paramètres libres d'une requête HTTP.
Ce module ne peut pas confirmer de paiement réel.
"""
from dataclasses import dataclass
from app.payment_routing_step38 import (
    CONGO, GABON, AGENCE, BUS, EN_LIGNE, ESPECES,
    moyens_disponibles,
)

CAISSIER = "CAISSIER"
AGENT_BUS = "AGENT_BUS"
SUPERVISEUR = "SUPERVISEUR"
SERVICE_PSP = "SERVICE_PSP"
AUDITEUR = "AUDITEUR"

CREER_INTENTION = "CREER_INTENTION"
CONFIRMER_ESPECES = "CONFIRMER_ESPECES"
RECEVOIR_RESULTAT_PSP = "RECEVOIR_RESULTAT_PSP"
CONSULTER_AUDIT = "CONSULTER_AUDIT"
ANNULER_INTENTION = "ANNULER_INTENTION"

ROLES = frozenset((CAISSIER, AGENT_BUS, SUPERVISEUR, SERVICE_PSP, AUDITEUR))
ACTIONS = frozenset((CREER_INTENTION, CONFIRMER_ESPECES,
                     RECEVOIR_RESULTAT_PSP, CONSULTER_AUDIT, ANNULER_INTENTION))


@dataclass(frozen=True)
class IdentiteHabilitee:
    identifiant: str
    role: str
    pays_autorises: frozenset
    canaux_autorises: frozenset
    active: bool = True
    authentifiee: bool = False


@dataclass(frozen=True)
class OperationPaiement:
    pays: str
    canal: str
    moyen: str
    action: str


def verifier_autorisation(identite, operation):
    """Refus par défaut, décision pure; jamais une preuve d'authentification."""
    motifs = []
    if not isinstance(identite, IdentiteHabilitee) or not isinstance(operation, OperationPaiement):
        return {"autorise": False, "motifs": ["CONTEXTE_INVALIDE"],
                "action_executee": False}
    if not identite.authentifiee:
        motifs.append("IDENTITE_NON_AUTHENTIFIEE")
    if not identite.active:
        motifs.append("COMPTE_INACTIF")
    if not isinstance(identite.identifiant, str) or not identite.identifiant.strip():
        motifs.append("IDENTIFIANT_INVALIDE")
    if identite.role not in ROLES:
        motifs.append("ROLE_INCONNU")
    if operation.pays not in (CONGO, GABON):
        motifs.append("PAYS_INCONNU")
    if operation.canal not in (AGENCE, BUS, EN_LIGNE):
        motifs.append("CANAL_INCONNU")
    if operation.moyen not in moyens_disponibles(operation.pays, operation.canal):
        motifs.append("MOYEN_NON_AUTORISE")
    if operation.action not in ACTIONS:
        motifs.append("ACTION_INCONNUE")
    if (not isinstance(identite.pays_autorises, frozenset)
            or operation.pays not in identite.pays_autorises):
        motifs.append("PAYS_HORS_PERIMETRE")
    if (not isinstance(identite.canaux_autorises, frozenset)
            or operation.canal not in identite.canaux_autorises):
        motifs.append("CANAL_HORS_PERIMETRE")
    permissions = {
        CAISSIER: {
            AGENCE: {CREER_INTENTION, CONFIRMER_ESPECES, ANNULER_INTENTION},
        },
        AGENT_BUS: {
            BUS: {CREER_INTENTION, CONFIRMER_ESPECES, ANNULER_INTENTION},
        },
        SUPERVISEUR: {
            AGENCE: {CONSULTER_AUDIT, ANNULER_INTENTION},
            BUS: {CONSULTER_AUDIT, ANNULER_INTENTION},
            EN_LIGNE: {CONSULTER_AUDIT, ANNULER_INTENTION},
        },
        SERVICE_PSP: {
            EN_LIGNE: {RECEVOIR_RESULTAT_PSP},
        },
        AUDITEUR: {
            AGENCE: {CONSULTER_AUDIT},
            BUS: {CONSULTER_AUDIT},
            EN_LIGNE: {CONSULTER_AUDIT},
        },
    }
    autorise_role = operation.action in permissions.get(
        identite.role, {}).get(operation.canal, set())
    if not autorise_role:
        motifs.append("ACTION_INTERDITE_POUR_ROLE_ET_CANAL")
    if operation.action == CONFIRMER_ESPECES and operation.moyen != ESPECES:
        motifs.append("CONFIRMATION_ESPECES_SEULEMENT")
    if operation.action == RECEVOIR_RESULTAT_PSP and operation.canal != EN_LIGNE:
        motifs.append("RESULTAT_PSP_EN_LIGNE_SEULEMENT")
    return {"autorise": not motifs, "motifs": motifs,
            "identifiant": identite.identifiant, "role": identite.role,
            "pays": operation.pays, "canal": operation.canal,
            "moyen": operation.moyen, "action": operation.action,
            "action_executee": False, "paiement_reel_confirme": False}


def preparer_trace_decision(identite, operation):
    """Trace structurée à enregistrer par un composant futur, sans persistance."""
    decision = verifier_autorisation(identite, operation)
    return {
        "identifiant": decision.get("identifiant"),
        "role": decision.get("role"),
        "pays": decision.get("pays"),
        "canal": decision.get("canal"),
        "moyen": decision.get("moyen"),
        "action": decision.get("action"),
        "autorise": decision["autorise"],
        "motifs": tuple(decision["motifs"]),
        "trace_persistee": False,
        "horodatage_fiable": False,
    }
