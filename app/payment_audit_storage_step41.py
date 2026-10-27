"""Étape 41 — prévalidation de lignes pour une persistance future.

Aucune connexion à PostgreSQL. Ne pas considérer ce module comme une transaction.
"""
from app.payment_audit_step40 import verifier_journal
from app.payment_routing_step38 import DemandePaiement, verifier_demande_paiement

STATUTS = frozenset(("EN_ATTENTE", "CONFIRME", "ECHOUE", "ANNULE"))


def preparer_lignes_audit(journal):
    """Convertit un journal simulé vérifié en données candidates SQL, sans écriture."""
    if not verifier_journal(journal):
        return {"pret_pour_revue": False, "motifs": ["JOURNAL_INVALIDE"],
                "flux": None, "lignes": (), "base_modifiee": False}
    premier = journal[0]
    dernier = journal[-1]
    base = ("reference_billet", "pays", "canal", "moyen", "montant_xaf")
    if any(any(ligne[k] != premier[k] for k in base) for ligne in journal):
        return {"pret_pour_revue": False, "motifs": ["IDENTITE_FLUX_DIVERGENTE"],
                "flux": None, "lignes": (), "base_modifiee": False}
    regles = verifier_demande_paiement(DemandePaiement(
        premier["pays"], premier["canal"], premier["moyen"], premier["montant_xaf"]))
    if not regles["autorise_par_regles_metier"]:
        return {"pret_pour_revue": False, "motifs": regles["motifs"],
                "flux": None, "lignes": (), "base_modifiee": False}
    if not isinstance(premier["reference_billet"], str) or not premier["reference_billet"].strip():
        return {"pret_pour_revue": False, "motifs": ["REFERENCE_BILLET_INVALIDE"],
                "flux": None, "lignes": (), "base_modifiee": False}
    if premier["action"] != "CREATION_SIMULEE" or premier["statut"] != "EN_ATTENTE":
        return {"pret_pour_revue": False, "motifs": ["PREMIERE_ENTREE_INVALIDE"],
                "flux": None, "lignes": (), "base_modifiee": False}
    if any(l["statut"] not in STATUTS for l in journal):
        return {"pret_pour_revue": False, "motifs": ["STATUT_INVALIDE"],
                "flux": None, "lignes": (), "base_modifiee": False}
    if any(l["action"] != "TRANSITION_SIMULEE" for l in journal[1:]):
        return {"pret_pour_revue": False, "motifs": ["ACTION_INVALIDE"],
                "flux": None, "lignes": (), "base_modifiee": False}
    if len(journal) > 2 or (len(journal) == 2 and dernier["statut"] == "EN_ATTENTE"):
        return {"pret_pour_revue": False, "motifs": ["CYCLE_INCOHERENT"],
                "flux": None, "lignes": (), "base_modifiee": False}
    flux = {k: premier[k] for k in base}
    flux.update(statut=dernier["statut"], derniere_sequence=dernier["sequence"],
                derniere_empreinte=dernier["empreinte"])
    champs = ("sequence", "action", "acteur", "statut", "reference_confirmation",
              "empreinte_precedente", "empreinte")
    lignes = tuple({k: l[k] for k in champs} for l in journal)
    return {"pret_pour_revue": True, "motifs": [], "flux": flux,
            "lignes": lignes, "base_modifiee": False,
            "transaction_postgresql_implementee": False}
