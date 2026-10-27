"""Diagnostic sans écriture des annulations et remboursements (étape 29).

Les remboursements ne sont jamais inférés à partir d'une annulation.
Entrées: dictionnaires en mémoire; aucun accès à la base de données.
"""


def diagnostic_annulations(courses, billets, paiements, remboursements=()):
    courses = list(courses)
    billets = list(billets)
    paiements = list(paiements)
    remboursements = list(remboursements)
    courses_annulees = {c.get('id') for c in courses if str(c.get('status', '')).upper() == 'CANCELLED'}
    billets_par_id = {b.get('id'): b for b in billets}
    paiements_valides = [p for p in paiements if str(p.get('status', '')).upper() == 'SUCCESS']
    alertes = []
    paiements_concernes = []
    for p in paiements_valides:
        billet = billets_par_id.get(p.get('ticket_id'))
        if billet is not None and billet.get('trip_id') in courses_annulees:
            paiements_concernes.append(p)
            alertes.append({
                'code': 'PAIEMENT_VALIDE_COURSE_ANNULEE',
                'trip_id': billet.get('trip_id'), 'ticket_id': billet.get('id'),
                'payment_id': p.get('id'), 'montant': int(p.get('amount') or 0),
                'statut': 'A_VERIFIER',
            })
    for r in remboursements:
        if not r.get('payment_id') and not r.get('payment_reference'):
            alertes.append({'code': 'REMBOURSEMENT_SANS_LIEN_PAIEMENT', 'statut': 'A_VERIFIER'})
        if int(r.get('amount') or 0) < 0:
            alertes.append({'code': 'MONTANT_REMBOURSEMENT_NEGATIF', 'statut': 'A_VERIFIER'})
    return {
        'courses_annulees': len(courses_annulees),
        'paiements_valides_sur_courses_annulees': len(paiements_concernes),
        'montant_paiements_a_examiner': sum(int(p.get('amount') or 0) for p in paiements_concernes),
        'remboursements_fournis_pour_diagnostic': len(remboursements),
        'remboursements_confirmes': None,  # Impossible à certifier sans registre métier fiable.
        'alertes': alertes,
        'aucune_deduction_automatique': True,
        'aucune_ecriture': True,
    }
