import pytest
from app.payment_lifecycle_step39 import demarrer_simulation
from app.payment_routing_step38 import DemandePaiement
from app.payment_audit_step40 import initialiser_journal, journaliser_transition
from app.payment_audit_transaction_step42 import (
    enregistrer_journal_initial, enregistrer_transition,
    EcritureAuditRefusee, ConfigurationTransactionInvalide)


class Cursor:
    def __init__(self, db): self.db = db
    def execute(self, sql, params):
        assert '%s' in sql and params and not any(str(p) in sql for p in params if isinstance(p, str) and p.startswith('BIL-'))
        self.db.calls.append((sql, params))
        if self.db.fail_on and len(self.db.calls) == self.db.fail_on:
            raise RuntimeError('erreur SQL simulée')
    def fetchone(self): return self.db.results.pop(0)
    def close(self): self.db.closed += 1


class DB:
    autocommit = False
    def __init__(self, *results, fail_on=None):
        self.results = list(results); self.fail_on = fail_on
        self.calls = []; self.commits = 0; self.rollbacks = 0; self.closed = 0
    def cursor(self): return Cursor(self)
    def commit(self): self.commits += 1
    def rollback(self): self.rollbacks += 1


def journals():
    p = demarrer_simulation(DemandePaiement('CG','EN_LIGNE','MTN_MOMO',2500), 'BIL-42')['paiement']
    j = initialiser_journal(p)['journal']
    jt = journaliser_transition(p,j,'CONFIRME',acteur='PSP_SIMULE',reference_confirmation='SIM-42')['journal']
    return j,jt


def test_initial_atomic():
    j,_ = journals(); db=DB((7,))
    r=enregistrer_journal_initial(db,j)
    assert r['enregistre'] and r['stream_id']==7
    assert db.commits==1 and db.rollbacks==0 and db.closed==1
    assert len(db.calls)==2
    assert 'RETURNING stream_id' in db.calls[0][0]


def test_transition_lock_and_commit():
    j,jt=journals(); x=j[0]
    db=DB((7,x['pays'],x['canal'],x['moyen'],x['montant_xaf'],x['statut'],1,x['empreinte']))
    r=enregistrer_transition(db,jt)
    assert r['sequence']==2 and db.commits==1 and len(db.calls)==3
    assert 'FOR UPDATE' in db.calls[0][0]


def test_duplicate_transition_rejected():
    _,jt=journals(); x=jt[1]
    db=DB((7,x['pays'],x['canal'],x['moyen'],x['montant_xaf'],x['statut'],2,x['empreinte']))
    with pytest.raises(EcritureAuditRefusee): enregistrer_transition(db,jt)
    assert db.rollbacks==1 and db.commits==0


def test_missing_stream_rejected():
    _,jt=journals(); db=DB(None)
    with pytest.raises(EcritureAuditRefusee): enregistrer_transition(db,jt)
    assert db.rollbacks==1


@pytest.mark.parametrize('failure', [1,2])
def test_initial_sql_failure_rolls_back(failure):
    j,_=journals(); db=DB((7,),fail_on=failure)
    with pytest.raises(RuntimeError): enregistrer_journal_initial(db,j)
    assert db.rollbacks==1 and db.commits==0 and db.closed==1


@pytest.mark.parametrize('failure', [1,2,3])
def test_transition_sql_failure_rolls_back(failure):
    j,jt=journals(); x=j[0]
    db=DB((7,x['pays'],x['canal'],x['moyen'],x['montant_xaf'],x['statut'],1,x['empreinte']),fail_on=failure)
    with pytest.raises(RuntimeError): enregistrer_transition(db,jt)
    assert db.rollbacks==1 and db.commits==0 and db.closed==1


def test_autocommit_refused():
    j,_=journals(); db=DB(); db.autocommit=True
    with pytest.raises(ConfigurationTransactionInvalide): enregistrer_journal_initial(db,j)
    assert not db.calls


def test_bad_connection_refused():
    j,_=journals()
    with pytest.raises(ConfigurationTransactionInvalide): enregistrer_journal_initial(None,j)


def test_initial_rejects_transition():
    _,jt=journals(); db=DB()
    with pytest.raises(EcritureAuditRefusee): enregistrer_journal_initial(db,jt)
    assert not db.calls


def test_transition_rejects_initial():
    j,_=journals(); db=DB()
    with pytest.raises(EcritureAuditRefusee): enregistrer_transition(db,j)
    assert not db.calls
