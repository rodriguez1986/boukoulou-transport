"""Étape 40 : journal d'audit *en mémoire*, à chaînage SHA-256.

Simulation uniquement. Le hash ne constitue ni une signature ni une preuve
contre un administrateur malveillant; pas de stockage durable ni d'horloge fiable.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
from app.payment_lifecycle_step39 import SimulationPaiement, simuler_transition


def _empreinte(contenu):
    return hashlib.sha256(json.dumps(contenu, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode('utf-8')).hexdigest()


def _entree(paiement, *, action, acteur, precedent, sequence):
    contenu = {'sequence': sequence, 'action': action, 'acteur': acteur,
               'reference_billet': paiement.reference_billet,
               'pays': paiement.pays, 'canal': paiement.canal,
               'moyen': paiement.moyen, 'montant_xaf': paiement.montant_xaf,
               'statut': paiement.statut,
               'reference_confirmation': paiement.reference_confirmation,
               'empreinte_precedente': precedent}
    return {**contenu, 'empreinte': _empreinte(contenu)}


def initialiser_journal(paiement):
    if not isinstance(paiement, SimulationPaiement) or paiement.statut != 'EN_ATTENTE':
        return {'ok': False, 'motifs': ['PAIEMENT_INITIAL_INVALIDE'], 'journal': ()}
    return {'ok': True, 'motifs': [], 'journal': (_entree(
        paiement, action='CREATION_SIMULEE', acteur='SYSTEME_SIMULE',
        precedent='', sequence=1),)}


def verifier_journal(journal):
    if not isinstance(journal, (tuple, list)) or not journal:
        return False
    precedent = ''
    for numero, ligne in enumerate(journal, start=1):
        if not isinstance(ligne, dict) or ligne.get('sequence') != numero:
            return False
        if ligne.get('empreinte_precedente') != precedent:
            return False
        if set(ligne) != {'sequence', 'action', 'acteur', 'reference_billet',
                          'pays', 'canal', 'moyen', 'montant_xaf', 'statut',
                          'reference_confirmation', 'empreinte_precedente', 'empreinte'}:
            return False
        contenu = {k: v for k, v in ligne.items() if k != 'empreinte'}
        try:
            if _empreinte(contenu) != ligne['empreinte']:
                return False
        except (TypeError, ValueError):
            return False
        precedent = ligne['empreinte']
    return True


def journaliser_transition(paiement, journal, nouvel_etat, *, acteur,
                           reference_confirmation=''):
    """Retourne un nouveau journal sans modifier l'original ni la base."""
    if not verifier_journal(journal):
        return {'ok': False, 'motifs': ['JOURNAL_INVALIDE'], 'paiement': paiement,
                'journal': journal}
    if not isinstance(paiement, SimulationPaiement):
        return {'ok': False, 'motifs': ['PAIEMENT_INVALIDE'], 'paiement': paiement,
                'journal': journal}
    dernier = journal[-1]
    # Empêche de réutiliser le journal d'un autre billet ou d'un autre état.
    for champ in ('reference_billet', 'pays', 'canal', 'moyen', 'montant_xaf',
                  'statut', 'reference_confirmation'):
        if getattr(paiement, champ) != dernier[champ]:
            return {'ok': False, 'motifs': ['JOURNAL_ET_PAIEMENT_DIVERGENTS'],
                    'paiement': paiement, 'journal': journal}
    resultat = simuler_transition(paiement, nouvel_etat, acteur=acteur,
                                  reference_confirmation=reference_confirmation)
    if not resultat['ok']:
        return {'ok': False, 'motifs': resultat['motifs'], 'paiement': paiement,
                'journal': journal}
    suivant = resultat['paiement']
    ligne = _entree(suivant, action='TRANSITION_SIMULEE', acteur=acteur,
                    precedent=dernier['empreinte'], sequence=len(journal) + 1)
    return {'ok': True, 'motifs': [], 'paiement': suivant,
            'journal': tuple(journal) + (ligne,),
            'audit_persistant': False, 'paiement_reel_confirme': False,
            'billet_emis': False, 'base_modifiee': False}
