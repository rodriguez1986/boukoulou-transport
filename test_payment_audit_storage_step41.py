from dataclasses import replace
from app.payment_routing_step38 import DemandePaiement
from app.payment_lifecycle_step39 import demarrer_simulation
from app.payment_audit_step40 import initialiser_journal, journaliser_transition, _empreinte
from app.payment_audit_storage_step41 import preparer_lignes_audit


def base():
    paiement = demarrer_simulation(
        DemandePaiement("GA", "EN_LIGNE", "MOOV_MONEY", 1500), "BIL-1")["paiement"]
    return paiement, initialiser_journal(paiement)["journal"]


def test_initial():
    _, journal = base()
    r = preparer_lignes_audit(journal)
    assert r["pret_pour_revue"] and not r["base_modifiee"]
    assert r["flux"]["derniere_sequence"] == 1
    assert r["flux"]["statut"] == "EN_ATTENTE"
    assert len(r["lignes"]) == 1


def test_transition():
    paiement, journal = base()
    suite = journaliser_transition(paiement, journal, "CONFIRME",
                                   acteur="PSP_SIMULE", reference_confirmation="TEST-1")
    r = preparer_lignes_audit(suite["journal"])
    assert r["pret_pour_revue"]
    assert r["flux"]["derniere_sequence"] == 2
    assert r["flux"]["statut"] == "CONFIRME"
    assert len(r["lignes"]) == 2
    assert not r["transaction_postgresql_implementee"]


def test_tampered_hash():
    _, journal = base()
    ligne = dict(journal[0], montant_xaf=9000)
    assert "JOURNAL_INVALIDE" in preparer_lignes_audit((ligne,))["motifs"]


def test_empty():
    assert not preparer_lignes_audit(())["pret_pour_revue"]


def test_invalid_identity_even_with_rehashed_entry():
    _, journal = base()
    ligne = dict(journal[0], pays="CG")
    ligne["empreinte"] = _empreinte({k:v for k,v in ligne.items() if k!="empreinte"})
    assert not preparer_lignes_audit((ligne,))["pret_pour_revue"]


def test_invalid_first_action_rehashed():
    _, journal = base()
    ligne = dict(journal[0], action="TRANSITION_SIMULEE")
    ligne["empreinte"] = _empreinte({k:v for k,v in ligne.items() if k!="empreinte"})
    assert "PREMIERE_ENTREE_INVALIDE" in preparer_lignes_audit((ligne,))["motifs"]


def test_missing_reference_rehashed():
    _, journal = base()
    ligne = dict(journal[0], reference_billet="")
    ligne["empreinte"] = _empreinte({k:v for k,v in ligne.items() if k!="empreinte"})
    assert "REFERENCE_BILLET_INVALIDE" in preparer_lignes_audit((ligne,))["motifs"]


def test_mutation_isolation():
    _, journal = base()
    r = preparer_lignes_audit(journal)
    r["lignes"][0]["acteur"] = "AUTRE"
    assert journal[0]["acteur"] == "SYSTEME_SIMULE"
