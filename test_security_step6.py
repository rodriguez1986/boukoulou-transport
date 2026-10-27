"""Tests unitaires de sécurité sans connexion PostgreSQL."""
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
pytest.importorskip("passlib", reason="Tests JWT : passlib non installé")
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from app.security import token, user, verifier_acces_pays
from app.models import Role


def compte(role='COUNTRY_MANAGER', pays=1, version=0, actif=True):
    return SimpleNamespace(id=8, role=SimpleNamespace(value=role), country_id=pays,
                           token_version=version, is_active=actif)


def test_jeton_valide():
    u=compte()
    db=Mock(); db.get.return_value=u
    assert user(HTTPAuthorizationCredentials(scheme='Bearer',credentials=token(u)),db) is u


def test_jeton_invalide_apres_changement_role_ou_mot_de_passe():
    u=compte()
    ancien=token(u)
    u.token_version=1
    db=Mock(); db.get.return_value=u
    with pytest.raises(HTTPException) as exc:
        user(HTTPAuthorizationCredentials(scheme='Bearer',credentials=ancien),db)
    assert exc.value.status_code==401


def test_compte_desactive_refuse():
    u=compte(actif=False)
    db=Mock(); db.get.return_value=u
    with pytest.raises(HTTPException) as exc:
        user(HTTPAuthorizationCredentials(scheme='Bearer',credentials=token(u)),db)
    assert exc.value.status_code==401


def test_jeton_falsifie_refuse():
    db=Mock()
    with pytest.raises(HTTPException) as exc:
        user(HTTPAuthorizationCredentials(scheme='Bearer',credentials='jeton-invalide'),db)
    assert exc.value.status_code==401


def test_responsable_national_pays_autorise():
    assert verifier_acces_pays(compte(pays=1),1) is None


def test_responsable_national_autre_pays_refuse():
    with pytest.raises(HTTPException) as exc:
        verifier_acces_pays(compte(pays=1),2)
    assert exc.value.status_code==403


def test_responsable_national_sans_pays_refuse():
    with pytest.raises(HTTPException) as exc:
        verifier_acces_pays(compte(pays=None),1)
    assert exc.value.status_code==403


def test_admin_tous_pays():
    assert verifier_acces_pays(compte(role='ADMIN',pays=None),2) is None


def test_autre_role_refuse_par_controle_territorial():
    with pytest.raises(HTTPException) as exc:
        verifier_acces_pays(compte(role='AGENT',pays=1),1)
    assert exc.value.status_code==403
