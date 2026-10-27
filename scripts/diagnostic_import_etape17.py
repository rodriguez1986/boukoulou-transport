"""Import FastAPI isolé, sans création de tables ni accès PostgreSQL."""
import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
env = os.environ.copy()
env['DATABASE_URL'] = 'sqlite:///:memory:'
env['BOUKOULOU_ENABLE_DEV_SEED'] = '0'
env['JWT_SECRET'] = 'test-only-not-for-production'
result = subprocess.run(
    [sys.executable, '-m', 'scripts.smoke_import_etape16'],
    cwd=root, env=env, capture_output=True, text=True, timeout=30,
)
print(result.stdout, end='')
if result.stderr:
    print(result.stderr, file=sys.stderr, end='')
if result.returncode:
    print('ECHEC de l’import FastAPI (aucune migration exécutée).', file=sys.stderr)
sys.exit(result.returncode)
