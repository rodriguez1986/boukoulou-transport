import pytest
from app.payment_routing_step38 import DemandePaiement
from app.payment_lifecycle_step39 import (
    demarrer_simulation, simuler_transition, EN_ATTENTE, CONFIRME, ECHOUE, ANNULE
)

@pytest.mark.parametrize('pays,canal,moyen', [
    ('CG','AGENCE','ESPECES'), ('CG','BUS','ESPECES'),
    ('GA','AGENCE','ESPECES'), ('GA','BUS','ESPECES'),
    ('CG','EN_LIGNE','AIRTEL_MONEY'), ('CG','EN_LIGNE','MTN_MOMO'),
    ('GA','EN_LIGNE','AIRTEL_MONEY'), ('GA','EN_LIGNE','MOOV_MONEY')
])
def test_demarrage_parcours_valides(pays,canal,moyen):
    r=demarrer_simulation(DemandePaiement(pays,canal,moyen,2500),'BILLET-1')
    assert r['ok'] and r['paiement'].statut==EN_ATTENTE

def test_billet_absent():
    r=demarrer_simulation(DemandePaiement('CG','BUS','ESPECES',2500),'')
    assert r['motifs']==['REFERENCE_BILLET_INVALIDE']

def test_moyen_interdit():
    r=demarrer_simulation(DemandePaiement('GA','EN_LIGNE','MTN_MOMO',2500),'B1')
    assert not r['ok']

@pytest.mark.parametrize('canal,acteur', [('AGENCE','CAISSIER'),('BUS','CAISSIER'),('EN_LIGNE','PSP_SIMULE')])
def test_confirmation_simulee(canal,acteur):
    moyen='ESPECES' if canal!='EN_LIGNE' else 'AIRTEL_MONEY'
    p=demarrer_simulation(DemandePaiement('CG',canal,moyen,2000),'B1')['paiement']
    r=simuler_transition(p,CONFIRME,acteur=acteur,reference_confirmation='REF-TEST')
    assert r['ok'] and r['paiement'].statut==CONFIRME
    assert not r['paiement_reel_confirme'] and not r['billet_emis']
    assert p.statut==EN_ATTENTE

@pytest.mark.parametrize('etat', [ECHOUE, ANNULE])
def test_echec_ou_annulation(etat):
    p=demarrer_simulation(DemandePaiement('GA','EN_LIGNE','MOOV_MONEY',2000),'B1')['paiement']
    assert simuler_transition(p,etat,acteur='PSP_SIMULE')['ok']

def test_caissier_ne_confirme_pas_mobile_money():
    p=demarrer_simulation(DemandePaiement('CG','EN_LIGNE','MTN_MOMO',2000),'B1')['paiement']
    assert 'ACTEUR_NON_AUTORISE' in simuler_transition(p,CONFIRME,acteur='CAISSIER',reference_confirmation='R')['motifs']

def test_psp_ne_confirme_pas_especes():
    p=demarrer_simulation(DemandePaiement('GA','BUS','ESPECES',2000),'B1')['paiement']
    assert 'ACTEUR_NON_AUTORISE' in simuler_transition(p,CONFIRME,acteur='PSP_SIMULE',reference_confirmation='R')['motifs']

def test_confirmation_sans_reference():
    p=demarrer_simulation(DemandePaiement('CG','AGENCE','ESPECES',2000),'B1')['paiement']
    assert 'REFERENCE_CONFIRMATION_OBLIGATOIRE' in simuler_transition(p,CONFIRME,acteur='CAISSIER')['motifs']

def test_transition_inconnue():
    p=demarrer_simulation(DemandePaiement('CG','BUS','ESPECES',2000),'B1')['paiement']
    assert 'TRANSITION_INTERDITE' in simuler_transition(p,'REMBOURSE',acteur='CAISSIER')['motifs']

def test_etat_terminal_irreversible():
    p=demarrer_simulation(DemandePaiement('CG','BUS','ESPECES',2000),'B1')['paiement']
    confirme=simuler_transition(p,CONFIRME,acteur='CAISSIER',reference_confirmation='R')['paiement']
    assert 'ETAT_TERMINAL' in simuler_transition(confirme,ANNULE,acteur='CAISSIER')['motifs']

def test_paiement_invalide():
    assert 'PAIEMENT_INVALIDE' in simuler_transition(None,CONFIRME,acteur='CAISSIER')['motifs']

def test_acteur_incorrect_sur_echec():
    p=demarrer_simulation(DemandePaiement('CG','EN_LIGNE','AIRTEL_MONEY',2000),'B1')['paiement']
    assert 'ACTEUR_NON_AUTORISE' in simuler_transition(p,ECHOUE,acteur='CAISSIER')['motifs']
