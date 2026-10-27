"""Import FastAPI sans accès à PostgreSQL ni écriture en base."""
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.chdir(ROOT)
os.environ["DATABASE_URL"]="sqlite:///:memory:"
os.environ["BOUKOULOU_ENABLE_DEV_SEED"]="0"
os.environ["JWT_SECRET"]="step16-test-only-not-for-production"
from app.main import app
from fastapi.routing import APIRoute
routes=[r for r in app.routes if isinstance(r,APIRoute)]
assert any("/health" == r.path for r in routes)
assert any("/cash/sessions/open" == r.path for r in routes)
print(f"IMPORT OK : {len(routes)} routes HTTP ; aucune migration exécutée")
