# ============================================================
# BOUKOULOU TRANSPORT V5.9 - ETAPE 93
# TEST DE CONNEXION ET DES COURSES DU CHAUFFEUR
#
# Objectifs :
# - Authentifier chauffeur.jean.
# - Verifier son role DRIVER.
# - Recuperer uniquement ses courses affectees.
#
# Securite :
# - Mot de passe masque.
# - Jeton non affiche.
# - Aucune modification des courses.
# ============================================================

$ErrorActionPreference = "Stop"
$API = "http://localhost:8000"

try {

    # --------------------------------------------------------
    # 1. Demander le nouveau mot de passe du chauffeur
    # --------------------------------------------------------

    $DriverSecret = Read-Host `
        "Nouveau mot de passe de chauffeur.jean" `
        -AsSecureString

    $DriverPassword = [System.Net.NetworkCredential]::new(
        "",
        $DriverSecret
    ).Password

    # --------------------------------------------------------
    # 2. Preparer la demande d'authentification
    # --------------------------------------------------------

    $DriverBody = @{
        username = "chauffeur.jean"
        password = $DriverPassword
    } | ConvertTo-Json

    # --------------------------------------------------------
    # 3. Authentifier le chauffeur
    # --------------------------------------------------------

    $Connexion = Invoke-RestMethod `
        -Uri "$API/auth/login" `
        -Method Post `
        -ContentType "application/json" `
        -Body $DriverBody

    Write-Host "Connexion chauffeur reussie." -ForegroundColor Green
    Write-Host "Role :" $Connexion.role

    # --------------------------------------------------------
    # 4. Preparer le jeton d'authentification
    # --------------------------------------------------------

    $Headers = @{
        Authorization = "Bearer $($Connexion.access_token)"
    }

    # --------------------------------------------------------
    # 5. Recuperer les courses affectees
    # --------------------------------------------------------

    $Courses = @(
        Invoke-RestMethod `
            -Uri "$API/trips" `
            -Method Get `
            -Headers $Headers
    )

    Write-Host ""
    Write-Host "COURSES ACCESSIBLES AU CHAUFFEUR" -ForegroundColor Cyan

    $Courses | Format-Table id, status, departure_at

    # --------------------------------------------------------
    # 6. Verifier les courses attendues
    # --------------------------------------------------------

    $Ids = @($Courses | ForEach-Object { $_.id })

    if (
        $Connexion.role -eq "DRIVER" -and
        $Ids.Count -eq 2 -and
        $Ids -contains 1 -and
        $Ids -contains 2
    ) {
        Write-Host "TEST REUSSI : les courses 1 et 2 sont accessibles." `
            -ForegroundColor Green
    }
    else {
        Write-Host "ATTENTION : les courses obtenues sont differentes des attentes." `
            -ForegroundColor Yellow
    }

}
catch {

    # --------------------------------------------------------
    # 7. Afficher les erreurs sans exposer le mot de passe
    # --------------------------------------------------------

    Write-Host "ECHEC DU TEST :" $_.Exception.Message `
        -ForegroundColor Red

}
finally {

    # --------------------------------------------------------
    # 8. Supprimer les informations sensibles temporaires
    # --------------------------------------------------------

    Remove-Variable DriverSecret, DriverPassword, DriverBody, `
        Connexion, Headers -ErrorAction SilentlyContinue
}