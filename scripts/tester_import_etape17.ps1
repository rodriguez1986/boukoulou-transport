# Exécuter depuis PowerShell après extraction de l'archive.
# Aucun conteneur Docker ni migration n'est lancé.
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
if ($LASTEXITCODE -ne 0) { throw 'Échec du chargement FastAPI ; transmettre le message d’erreur' }
& $python -m pytest -q test_import_step17.py
if ($LASTEXITCODE -ne 0) { throw 'Échec des tests étape 17' }
