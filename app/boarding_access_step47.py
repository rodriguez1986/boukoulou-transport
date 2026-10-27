"""Politique d'accès embarquement, non connectée aux routes réelles.
L'affectation doit être validée côté serveur, jamais fournie par le client.
"""
from dataclasses import dataclass

CONTROLER_BILLET = "CONTROLER_BILLET"
VALIDER_EMBARQUEMENT = "VALIDER_EMBARQUEMENT"
CONSULTER_PASSAGERS = "CONSULTER_PASSAGERS"
CONSULTER_VOYAGE = "CONSULTER_VOYAGE"
ACTIONS = frozenset((CONTROLER_BILLET, VALIDER_EMBARQUEMENT,
                     CONSULTER_PASSAGERS, CONSULTER_VOYAGE))

@dataclass(frozen=True)
class AffectationVerifiee:
    user_id: int
    voyage_id: int
    pays: str
    affectation_active: bool
    source_verifiee: bool = False


def autoriser_embarquement(*, user_id, role, actif, pays_utilisateur,
                          voyage_id, pays_voyage, action, affectation):
    motifs = []
    if type(user_id) is not int or user_id <= 0:
        motifs.append("UTILISATEUR_INVALIDE")
    if type(voyage_id) is not int or voyage_id <= 0:
        motifs.append("VOYAGE_INVALIDE")
    if actif is not True:
        motifs.append("COMPTE_INACTIF")
    if role not in ("DRIVER", "CONTROLLER"):
        motifs.append("ROLE_NON_AUTORISE")
    if (pays_utilisateur not in ("CG", "GA") or
            pays_voyage not in ("CG", "GA") or pays_utilisateur != pays_voyage):
        motifs.append("PAYS_HORS_PERIMETRE")
    if action not in ACTIONS:
        motifs.append("ACTION_NON_AUTORISEE")
    if (not isinstance(affectation, AffectationVerifiee) or
            affectation.source_verifiee is not True or
            affectation.affectation_active is not True or
            affectation.user_id != user_id or
            affectation.voyage_id != voyage_id or
            affectation.pays != pays_voyage):
        motifs.append("AFFECTATION_NON_VERIFIEE")
    return {"autorise": not motifs, "motifs": tuple(motifs),
            "operation_executee": False, "billet_valide": False,
            "embarquement_enregistre": False}
