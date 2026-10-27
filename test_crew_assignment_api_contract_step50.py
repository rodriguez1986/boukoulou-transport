from pathlib import Path

def test_jwt_depends_on_security_user():
    p=(Path(__file__).parent/'app'/'crew_assignment_api_step50.py').read_text()
    assert 'from .security import user' in p
    assert p.count('Depends(user)') == 3
    assert 'actor_id = _acteur_id(utilisateur)' in p

def test_router_not_mounted():
    p=(Path(__file__).parent/'app'/'main.py').read_text()
    assert 'crew_assignment_api_step50' not in p

def test_generic_error():
    p=(Path(__file__).parent/'app'/'crew_assignment_api_step50.py').read_text()
    assert 'except AffectationRefusee:' in p
    assert 'detail="Opération non autorisée"' in p
