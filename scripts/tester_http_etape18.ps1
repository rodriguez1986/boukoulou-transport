# Exécuter depuis le dossier extrait. Test local sans Docker/PostgreSQL.
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    py -3 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Impossible de créer .venv' }
}
$python = '.venv\Scripts\python.exe'
& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Installation des dépendances échouée' }
& $python scripts\diagnostic_import_etape17.py
if ($LASTEXITCODE -ne 0) { throw 'Import FastAPI échoué' }
& $python scripts\smoke_http_etape18.py
if ($LASTEXITCODE -ne 0) { throw 'Smoke HTTP échoué : transmettre la sortie complète' }
