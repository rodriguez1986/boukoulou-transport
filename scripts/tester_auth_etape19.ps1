# Exécuter dans un dossier de développement extrait, jamais sur la production.
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    py -3 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Création de .venv impossible' }
}
$python = '.venv\Scripts\python.exe'
& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Installation des dépendances échouée' }
& $python -m pytest -q test_auth_step19.py
if ($LASTEXITCODE -ne 0) { throw 'Tests statiques échoués' }
& $python scripts\smoke_auth_etape19.py
if ($LASTEXITCODE -ne 0) { throw 'Tests HTTP JWT échoués : transmettre la sortie complète' }
