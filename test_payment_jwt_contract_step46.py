"""Vérifications de sécurité structurelles exécutables sans passlib."""
from pathlib import Path


def test_route_exige_jwt_et_base():
    p = (Path(__file__).parent / "app" / "payment_api_step45.py").read_text()
    assert "Depends(user)" in p
    assert "Depends(get_db)" in p
    assert "db.get(Country, country_id)" in p
    assert "paiement_reel_confirme" in p


def test_jwt_verifie_signature_expiration_version_et_statut():
    p = (Path(__file__).parent / "app" / "security.py").read_text()
    assert 'algorithms=[JWT_ALGORITHM]' in p
    assert 'JWT_ALGORITHM = "HS256"' in p
    assert 'jwt.decode(' in p
    assert 'u.is_active' in p
    assert 'version != u.token_version' in p


def test_pas_montage_automatique():
    p = (Path(__file__).parent / "app" / "main.py").read_text()
    assert "payment_api_step45" not in p
