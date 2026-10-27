import copy
import pytest
from app.payment_routing_step38 import DemandePaiement
from app.payment_lifecycle_step39 import demarrer_simulation, CONFIRME, ECHOUE, ANNULE
from app.payment_audit_step40 import initialiser_journal, verifier_journal, journaliser_transition


def payer(pays='CG', canal='AGENCE', moyen='ESPECES', billet='B-1'):
    return demarrer_simulation(DemandePaiement(pays, canal, moyen, 2500), billet)['paiement']


def test_creation():
    p=payer(); r=initialiser_journal(p)
    assert r['ok'] and verifier_journal(r['journal'])
    assert r['journal'][0]['action']=='CREATION_SIMULEE'

@pytest.mark.parametrize('pays,canal,moyen,acteur', [
    ('CG','AGENCE','ESPECES','CAISSIER'),('CG','BUS','ESPECES','CAISSIER'),
    ('GA','AGENCE','ESPECES','CAISSIER'),('GA','BUS','ESPECES','CAISSIER'),
    ('CG','EN_LIGNE','AIRTEL_MONEY','PSP_SIMULE'),
    ('CG','EN_LIGNE','MTN_MOMO','PSP_SIMULE'),
    ('GA','EN_LIGNE','AIRTEL_MONEY','PSP_SIMULE'),
    ('GA','EN_LIGNE','MOOV_MONEY','PSP_SIMULE')])
def test_confirmation_journalisee(pays,canal,moyen,acteur):
    p=payer(pays,canal,moyen)
    journal=initialiser_journal(p)['journal']
    r=journaliser_transition(p,journal,CONFIRME,acteur=acteur,reference_confirmation='SIM-1')
    assert r['ok'] and verifier_journal(r['journal']) and len(r['journal'])==2
    assert len(journal)==1 and not r['audit_persistant']
    assert not r['paiement_reel_confirme'] and not r['billet_emis']

@pytest.mark.parametrize('etat', [ECHOUE, ANNULE])
def test_fin_alternative(etat):
    p=payer('GA','EN_LIGNE','MOOV_MONEY'); j=initialiser_journal(p)['journal']
    assert journaliser_transition(p,j,etat,acteur='PSP_SIMULE')['ok']

def test_journal_modifie_refuse():
    p=payer(); j=list(copy.deepcopy(initialiser_journal(p)['journal']))
    j[0]['montant_xaf']=1
    assert not verifier_journal(j)
    assert 'JOURNAL_INVALIDE' in journaliser_transition(p,j,CONFIRME,acteur='CAISSIER')['motifs']

def test_journal_tronque_ou_vide():
    assert not verifier_journal([])
    assert not verifier_journal(None)

def test_journal_d_autre_billet_refuse():
    p=payer(billet='B-1'); j=initialiser_journal(p)['journal']
    q=payer(billet='B-2')
    assert 'JOURNAL_ET_PAIEMENT_DIVERGENTS' in journaliser_transition(q,j,CONFIRME,acteur='CAISSIER')['motifs']

def test_refus_acteur_ne_journalise_pas():
    p=payer('CG','EN_LIGNE','MTN_MOMO'); j=initialiser_journal(p)['journal']
    r=journaliser_transition(p,j,CONFIRME,acteur='CAISSIER',reference_confirmation='SIM-1')
    assert not r['ok'] and r['journal']==j

def test_pas_de_confirmation_sans_reference():
    p=payer(); j=initialiser_journal(p)['journal']
    assert not journaliser_transition(p,j,CONFIRME,acteur='CAISSIER')['ok']

def test_repetition_transition_refusee():
    p=payer(); j=initialiser_journal(p)['journal']
    r=journaliser_transition(p,j,CONFIRME,acteur='CAISSIER',reference_confirmation='SIM-1')
    assert 'ETAT_TERMINAL' in journaliser_transition(r['paiement'],r['journal'],ANNULE,acteur='CAISSIER')['motifs']

def test_journal_ordre_invalide():
    p=payer(); j=list(copy.deepcopy(initialiser_journal(p)['journal']))
    j[0]['sequence']=3
    assert not verifier_journal(j)

def test_creation_refuse_objet_invalide():
    assert not initialiser_journal(None)['ok']

def test_historique_falsifie_empreinte():
    p=payer(); j=list(copy.deepcopy(initialiser_journal(p)['journal']))
    j[0]['empreinte']='0'*64
    assert not verifier_journal(j)

def test_reference_paiement_divergente():
    p=payer(); j=initialiser_journal(p)['journal']
    q=payer(billet='B-1')
    r=journaliser_transition(q,j,ECHOUE,acteur='CAISSIER')
    assert r['ok']
