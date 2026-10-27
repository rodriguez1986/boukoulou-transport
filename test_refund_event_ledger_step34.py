from app.refund_event_ledger_step34 import preparer_evenement_pour_registre

E = dict(provider='psp_a', event_id='evt1', refund_id='ref1', status='CONFIRMED', amount=1200, currency='XAF')

def test_valide_sans_ecriture():
    r=preparer_evenement_pour_registre(evenement=E, remboursements_connus=['ref1'])
    assert r['enregistrement_possible_en_simulation']
    assert not r['enregistrement_effectue'] and not r['signature_psp_verifiee']

def test_doublon():
    r=preparer_evenement_pour_registre(evenement=E, historique=[E], remboursements_connus=['ref1'])
    assert 'EVENEMENT_DEJA_VU' in r['motifs']

def test_conflit():
    r=preparer_evenement_pour_registre(evenement={**E,'amount':1400}, historique=[E], remboursements_connus=['ref1'])
    assert 'EVENEMENT_CONFLICTUEL' in r['motifs']

def test_remboursement_inconnu():
    r=preparer_evenement_pour_registre(evenement=E, remboursements_connus=[])
    assert 'REMBOURSEMENT_INCONNU' in r['motifs']

def test_montant_invalide():
    for v in [0,-1,True,1.5,'1200']:
        assert 'MONTANT_INVALIDE' in preparer_evenement_pour_registre(evenement={**E,'amount':v}, remboursements_connus=['ref1'])['motifs']

def test_devise_invalide():
    for v in ['', 'xaf', 'EURO', 123, 'X1F']:
        assert 'DEVISE_INVALIDE' in preparer_evenement_pour_registre(evenement={**E,'currency':v}, remboursements_connus=['ref1'])['motifs']

def test_referentiel_invalide():
    assert 'REFERENTIEL_REMBOURSEMENTS_INVALIDE' in preparer_evenement_pour_registre(evenement=E, remboursements_connus=None)['motifs']
