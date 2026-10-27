"""Diagnostic en lecture seule des dépendances et fichiers nécessaires au backend."""
import ast
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULES = ("fastapi","uvicorn","sqlalchemy","psycopg","pydantic","jwt",
           "passlib","bcrypt","qrcode","multipart","httpx","pytest",
           "reportlab","openpyxl")
MISSING = [name for name in MODULES if importlib.util.find_spec(name) is None]
print("Dépendances absentes :", ", ".join(MISSING) if MISSING else "aucune")
for path in ("app/main.py","app/models.py","app/security.py","app/db.py",
             "app/pdf_reports.py","app/finance_dashboard.py","app/finance_audit.py"):
    file = ROOT / path
    try:
        ast.parse(file.read_text(encoding="utf-8-sig"), filename=path)
        print("OK :",path)
    except (OSError,SyntaxError) as exc:
        print("ERREUR :",path,exc)
print("Ce diagnostic ne lance ni serveur, ni base de données, ni migration.")
