"""Étape 32 — validation PURE des transitions d'un remboursement.

Ne déclenche ni paiement, ni écriture, ni audit durable. Les preuves externes
ne sont pas vérifiées ici : une intégration PSP sécurisée reste nécessaire.
"""

STATUSES = frozenset({'PENDING', 'PROCESSING', 'CONFIRMED', 'FAILED', 'CANCELLED'})
ALLOWED = {
    'PENDING': frozenset({'PROCESSING', 'CANCELLED'}),
    'PROCESSING': frozenset({'CONFIRMED', 'FAILED'}),
    'CONFIRMED': frozenset(),
    'FAILED': frozenset(),
    'CANCELLED': frozenset(),
}


def verifier_transition_remboursement(*, role, etat_actuel, nouvel_etat,
                                       reference_psp=None, motif=None):
    """Retourne une décision explicite, sans modifier de remboursement.

    Les états terminaux sont immuables. La confirmation exige une référence
    PSP non vide, sans pour autant attester que le PSP a réellement payé.
    """
    erreurs = []
    actuel = etat_actuel if isinstance(etat_actuel, str) else None
    nouveau = nouvel_etat if isinstance(nouvel_etat, str) else None
    if actuel not in STATUSES or nouveau not in STATUSES:
        erreurs.append('ETAT_INCONNU')
    elif actuel == nouveau:
        erreurs.append('TRANSITION_IDENTIQUE')
    elif nouveau not in ALLOWED[actuel]:
        erreurs.append('TRANSITION_INTERDITE')
    if role != 'ADMIN':
        erreurs.append('ROLE_NON_AUTORISE')
    if nouveau == 'CONFIRMED' and (not isinstance(reference_psp, str) or not reference_psp.strip()):
        erreurs.append('REFERENCE_PSP_OBLIGATOIRE')
    if nouveau in {'FAILED', 'CANCELLED'} and (not isinstance(motif, str) or not motif.strip()):
        erreurs.append('MOTIF_OBLIGATOIRE')
    return {
        'transition_autorisee_en_simulation': not erreurs,
        'motifs': erreurs,
        'etat_actuel': actuel,
        'nouvel_etat': nouveau,
        'transition_effectuee': False,
        'remboursement_execute': False,
        'audit_enregistre': False,
        'verification_psp_effectuee': False,
    }
