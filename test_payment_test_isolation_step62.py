"""Régressions étape 62 : pas de substitution globale de l'authentification."""
import sys
from fastapi.params import Depends
from app import security
from app.payment_api_step45 import router


def test_security_module_is_real():
    assert sys.modules['app.security'] is security
    assert security.user.__module__ == 'app.security'
    assert callable(security.user)


def test_payment_router_uses_real_jwt_dependency():
    route = next(r for r in router.routes if r.path.endswith('/verifier'))
    assert any(dep.call is security.user for dep in route.dependant.dependencies)
