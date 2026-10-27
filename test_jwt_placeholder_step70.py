"""Étape 70 : clés de démonstration longues refusées en production."""
import pytest
from app.jwt_config_step63 import get_jwt_secret, is_unsafe_production_secret
from app.startup_config_step68 import validate_startup_config

@pytest.mark.parametrize('secret', [
    'CHANGE_THIS_SECRET_TO_A_REAL_SECRET_123456',
    'replace-me-with-your-secret-key-1234567890',
    'your-secret-key-must-be-changed-123456789',
    'placeholder-secret-for-deployment-123456',
    'example-secret-please-change-this-value',
    'dummy_secret_long_enough_for_jwt_123456',
    'default-secret-that-is-long-enough-12345',
    'a' * 64, 'ab' * 32, '0123456789' * 4,
    'abcdef' * 7,
])
def test_production_refuse_secret_factice_long(secret):
    assert len(secret.encode()) >= 32
    assert is_unsafe_production_secret(secret)
    with pytest.raises(RuntimeError, match='JWT_SECRET'):
        get_jwt_secret({'APP_ENV': 'production', 'JWT_SECRET': secret})
    with pytest.raises(RuntimeError, match='JWT_SECRET'):
        validate_startup_config({'BOUKOULOU_ENV': 'production', 'JWT_SECRET': secret})

def test_secret_complexe_accepte_sans_transformation():
    secret = 'L8^aR3!uP9#fG2%qY7&wT4+zN6?mK1@vB5'
    assert not is_unsafe_production_secret(secret)
    assert get_jwt_secret({'APP_ENV': 'production', 'JWT_SECRET': secret}) == secret

def test_validation_ne_divulgue_pas_le_secret():
    secret = 'placeholder-secret-super-long-private-value'
    with pytest.raises(RuntimeError) as exc:
        get_jwt_secret({'APP_ENV': 'production', 'JWT_SECRET': secret})
    assert secret not in str(exc.value)
