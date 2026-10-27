"""Étape 37 — contrat de configuration d'un adaptateur PSP (sans intégration réelle).

Un prestataire doit être choisi et sa documentation officielle suivie
avant toute activation. Ce module ne valide AUCUNE signature PSP réelle.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ConfigurationPSP:
    fournisseur: str
    environnement: str
    signature_documentee: bool
    deduplication_transactionnelle_active: bool
    secret_configure: bool
    endpoint_active: bool = False


def evaluer_activation_psp(configuration):
    """Diagnostic de préparation. Toujours refuse l'activation à cette étape."""
    motifs = []
    if not isinstance(configuration, ConfigurationPSP):
        return {"activation_autorisee": False, "motifs": ["CONFIGURATION_INVALIDE"],
                "webhook_actif": False, "remboursement_actif": False}
    if not isinstance(configuration.fournisseur, str) or not configuration.fournisseur.strip():
        motifs.append("FOURNISSEUR_NON_CHOISI")
    if configuration.environnement not in ("sandbox", "production"):
        motifs.append("ENVIRONNEMENT_INVALIDE")
    if configuration.signature_documentee is not True:
        motifs.append("VERIFICATION_SIGNATURE_REELLE_MANQUANTE")
    if configuration.secret_configure is not True:
        motifs.append("SECRET_PSP_MANQUANT")
    if configuration.deduplication_transactionnelle_active is not True:
        motifs.append("DEDUPLICATION_ATOMIQUE_MANQUANTE")
    if configuration.endpoint_active:
        motifs.append("ENDPOINT_ACTIF_PREMATUREMENT")
    # Garde explicite : aucune configuration ne peut autoriser l'activation
    # dans cette étape préparatoire.
    motifs.append("INTEGRATION_REELLE_NON_IMPLEMENTEE")
    return {"activation_autorisee": False, "motifs": motifs,
            "webhook_actif": False, "remboursement_actif": False}


def decrire_plan_transactionnel():
    """Plan descriptif non exécutable, sans migration ni connexion SQL."""
    return (
        "Vérifier la signature PSP selon sa documentation sur le corps brut.",
        "Décoder le corps signé, valider le schéma et la référence de remboursement.",
        "Ouvrir une transaction PostgreSQL.",
        "Insérer l'identifiant (prestataire, evenement_id) sous contrainte UNIQUE.",
        "Si conflit UNIQUE, confirmer l'idempotence sans rejouer les effets.",
        "Verrouiller la ligne remboursement (SELECT FOR UPDATE).",
        "Valider montant, devise, transition d'état et référence PSP.",
        "Écrire le journal d'audit et le changement d'état dans la même transaction.",
        "COMMIT, puis répondre au PSP selon son protocole.",
    )
