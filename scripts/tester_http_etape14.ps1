# Exécuter dans PowerShell depuis le dossier racine du projet extrait.
# Crée un environnement virtuel local. Ne lance ni Docker ni migration.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    py -3 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Création de l'environnement virtuel impossible" }
}
$python = ".venv\Scripts\python.exe"
& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Installation des dépendances échouée" }
& $python -m pytest -q test_cash_api_step13.py test_cash_api_step14.py
if ($LASTEXITCODE -ne 0) { throw "Certains tests ont échoué" }
