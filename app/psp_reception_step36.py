"""Étape 36 — prévalidation orchestrée, sans effet de bord.

Le protocole HMAC de l'étape 35 est uniquement un protocole de démonstration.
Ne pas exposer cette fonction comme webhook réel.
"""
import json

from app.psp_signature_step35 import verifier_notification_psp
from app.refund_event_ledger_step34 import preparer_evenement_pour_registre


def simuler_reception_notification(*, corps_brut, signature, horodatage, secret,
                                   historique=(), remboursements_connus=(),
                                   maintenant=None, tolerance_secondes=300):
    """Vérifie signature, JSON strict et registre; ne stocke rien.

    N'accepte pas de champ 'evenement' séparé : le JSON doit venir du corps
    signé, pour éviter une divergence entre octets signés et données examinées.
    """
    signature_resultat = verifier_notification_psp(
        corps_brut=corps_brut, signature=signature,
        horodatage=horodatage, secret=secret,
        maintenant=maintenant, tolerance_secondes=tolerance_secondes
    )
    motifs = list(signature_resultat["motifs"])
    registre = None
    evenement = None
    if not motifs:
        try:
            evenement = json.loads(corps_brut.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            motifs.append("CORPS_JSON_INVALIDE")
        else:
            if not isinstance(evenement, dict):
                motifs.append("EVENEMENT_JSON_NON_OBJET")
            else:
                registre = preparer_evenement_pour_registre(
                    evenement=evenement, historique=historique,
                    remboursements_connus=remboursements_connus
                )
                motifs.extend(registre["motifs"])
    motifs = list(dict.fromkeys(motifs))
    return {
        "acceptable_en_simulation": not motifs,
        "motifs": motifs,
        "signature_valide_en_protocole_test": signature_resultat[
            "signature_valide_en_protocole_test"
        ],
        "controle_registre_effectue": registre is not None,
        "protocole_psp_reel_verifie": False,
        "deduplication_atomique_postgresql_active": False,
        "evenement_enregistre": False,
        "etat_modifie": False,
        "remboursement_execute": False,
    }
