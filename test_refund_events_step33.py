from app.refund_events_step33 import examiner_evenement_remboursement as check

BASE = {'provider': 'PSP-A', 'event_id': 'evt-1', 'refund_id': 'ref-1', 'status': 'CONFIRMED', 'amount': 100, 'currency': 'XAF'}


def test_new_event_is_candidate_only():
    result = check(evenement=BASE)
    assert result['nouvel_evenement_possible_en_simulation']
    assert not any(result[k] for k in ('evenement_traite', 'etat_modifie', 'remboursement_execute', 'audit_enregistre', 'signature_psp_verifiee', 'preuve_psp_verifiee'))


def test_identical_replay_detected():
    assert 'EVENEMENT_DEJA_VU' in check(evenement=BASE, historique=[dict(BASE)])['motifs']


def test_same_provider_and_id_different_payload_is_conflict():
    other = dict(BASE, amount=200)
    assert 'EVENEMENT_CONFLICTUEL' in check(evenement=other, historique=[BASE])['motifs']


def test_other_provider_same_event_id_is_distinct():
    other = dict(BASE, provider='PSP-B')
    assert check(evenement=other, historique=[BASE])['nouvel_evenement_possible_en_simulation']


def test_other_event_id_is_distinct():
    assert check(evenement=dict(BASE, event_id='evt-2'), historique=[BASE])['nouvel_evenement_possible_en_simulation']


def test_missing_identifiers_rejected():
    assert 'IDENTIFIANTS_OBLIGATOIRES' in check(evenement=dict(BASE, refund_id=' '))['motifs']


def test_unknown_external_status_rejected():
    assert 'ETAT_EXTERNE_INVALIDE' in check(evenement=dict(BASE, status='PROCESSING'))['motifs']


def test_malformed_history_rejected():
    assert 'HISTORIQUE_INVALIDE' in check(evenement=BASE, historique=[None])['motifs']


def test_malformed_event_rejected():
    assert 'EVENEMENT_INVALIDE' in check(evenement=None)['motifs']


def test_conflict_does_not_execute_or_audit():
    r = check(evenement=dict(BASE, status='FAILED'), historique=[BASE])
    assert 'EVENEMENT_CONFLICTUEL' in r['motifs']
    assert not r['etat_modifie'] and not r['audit_enregistre']
