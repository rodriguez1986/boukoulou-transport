# ============================================================
# BOUKOULOU TRANSPORT V5.9 - ETAPE 93
# TEST HTTP 404 - ACCES CHAUFFEUR
#
# Objectifs :
# - Authentifier chauffeur.jean.
# - Verifier l'acces a sa course 1.
# - Verifier le refus d'une course inexistante.
#
# Lecture seule : uniquement des requetes GET.
# ============================================================

$ErrorActionPreference = "Stop"
$API = "http://localhost:8000"

try {
    # 1. Authentifier le chauffeur.
    $Secret = Read-Host "Mot de passe chauffeur.jean" -AsSecureString
    $MotDePasse = [System.Net.NetworkCredential]::new("", $Secret).Password

    $Corps = @{
        username = "chauffeur.jean"
        password = $MotDePasse
    } | ConvertTo-Json

    $Connexion = Invoke-RestMethod `
        -Uri "$API/auth/login" `
        -Method Post `
        -ContentType "application/json" `
        -Body $Corps

    $Headers = @{
        Authorization = "Bearer $($Connexion.access_token)"
    }

    Write-Host "Connexion chauffeur reussie." -ForegroundColor Green

    # 2. Verifier une course autorisee.
    $Course = Invoke-RestMethod `
        -Uri "$API/trips/1" `
        -Method Get `
        -Headers $Headers

    if ($Course.id -ne 1) {
        throw "La course retournee ne correspond pas a la course 1."
    }

    Write-Host "SUCCES : course 1 accessible." -ForegroundColor Green

    # 3. Verifier une course inexistante.
    # Aucun endpoint de modification n'est utilise.
    $IdentifiantInexistant = 999999999

    try {
        $null = Invoke-RestMethod `
            -Uri "$API/trips/$IdentifiantInexistant" `
            -Method Get `
            -Headers $Headers

        throw "ECHEC : une course inexistante est accessible."
    }
    catch {
        # Le resultat attendu est exactement HTTP 404.
        $Code = [int]$_.Exception.Response.StatusCode

        if ($Code -eq 404) {
            Write-Host "SUCCES : course inexistante refusee (HTTP 404)." `
                -ForegroundColor Green
        }
        else {
            throw "Code HTTP inattendu : $Code"
        }
    }
}
catch {
    Write-Host "ERREUR :" $_.Exception.Message -ForegroundColor Red
}
finally {
    # Nettoyage des variables contenant les secrets.
    Remove-Variable Secret, MotDePasse, Corps, Connexion, Headers `
        -ErrorAction SilentlyContinue
}