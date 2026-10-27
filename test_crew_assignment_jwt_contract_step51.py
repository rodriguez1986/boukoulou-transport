"""Contrats statiques indépendants des dépendances JWT facultatives."""
import ast
from pathlib import Path


def test_jwt_dependency_present():
    root = Path(__file__).parent / "app"
    api = (root / "crew_assignment_api_step50.py").read_text()
    sec = (root / "security.py").read_text()
    assert "Depends(user)" in api
    assert "jwt.decode(" in sec
    assert 'algorithms=[JWT_ALGORITHM]' in sec
    assert 'JWT_ALGORITHM = "HS256"' in sec
    assert "token_version" in sec
    assert "crew_assignment_api_step50" not in (root / "main.py").read_text()


def test_actor_id_from_authenticated_user():
    api = (Path(__file__).parent / "app" / "crew_assignment_api_step50.py").read_text()
    assert "actor_id = _acteur_id(utilisateur)" in api
    assert "actor_id: int" not in api
    ast.parse(api)


def test_transaction_audit():
    src = (Path(__file__).parent / "app" / "crew_assignment_admin_step49.py").read_text()
    assert "CrewAssignmentAuditStep49(" in src
    assert "db.commit()" in src
    assert "db.rollback()" in src
