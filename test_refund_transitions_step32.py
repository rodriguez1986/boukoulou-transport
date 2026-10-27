from app.refund_transitions_step32 import verifier_transition_remboursement as check


def test_pending_to_processing():
    assert check(role='ADMIN', etat_actuel='PENDING', nouvel_etat='PROCESSING')['transition_autorisee_en_simulation']


def test_pending_to_cancelled_requires_reason():
    assert 'MOTIF_OBLIGATOIRE' in check(role='ADMIN', etat_actuel='PENDING', nouvel_etat='CANCELLED')['motifs']
    assert check(role='ADMIN', etat_actuel='PENDING', nouvel_etat='CANCELLED', motif='Erreur client')['transition_autorisee_en_simulation']


def test_processing_to_confirmed_requires_psp_reference():
    assert 'REFERENCE_PSP_OBLIGATOIRE' in check(role='ADMIN', etat_actuel='PROCESSING', nouvel_etat='CONFIRMED')['motifs']
    assert check(role='ADMIN', etat_actuel='PROCESSING', nouvel_etat='CONFIRMED', reference_psp='psp-123')['transition_autorisee_en_simulation']


def test_processing_to_failed_requires_reason():
    assert check(role='ADMIN', etat_actuel='PROCESSING', nouvel_etat='FAILED', motif='Refus PSP')['transition_autorisee_en_simulation']


def test_cannot_confirm_directly_from_pending():
    assert 'TRANSITION_INTERDITE' in check(role='ADMIN', etat_actuel='PENDING', nouvel_etat='CONFIRMED', reference_psp='psp-123')['motifs']


def test_terminal_states_are_immutable():
    for status in ('CONFIRMED', 'FAILED', 'CANCELLED'):
        assert 'TRANSITION_INTERDITE' in check(role='ADMIN', etat_actuel=status, nouvel_etat='PROCESSING')['motifs']


def test_same_state_is_not_a_transition():
    assert 'TRANSITION_IDENTIQUE' in check(role='ADMIN', etat_actuel='PENDING', nouvel_etat='PENDING')['motifs']


def test_unknown_state_rejected():
    assert 'ETAT_INCONNU' in check(role='ADMIN', etat_actuel='UNKNOWN', nouvel_etat='CONFIRMED')['motifs']


def test_non_admin_rejected():
    assert 'ROLE_NON_AUTORISE' in check(role='AGENT', etat_actuel='PENDING', nouvel_etat='PROCESSING')['motifs']


def test_never_changes_state_or_executes_refund():
    r = check(role='ADMIN', etat_actuel='PROCESSING', nouvel_etat='CONFIRMED', reference_psp='psp-123')
    assert not r['transition_effectuee'] and not r['remboursement_execute']
    assert not r['audit_enregistre'] and not r['verification_psp_effectuee']
