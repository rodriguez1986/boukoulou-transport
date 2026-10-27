
# ============================================================
# BOUKOULOU TRANSPORT V5.9 - ETAPE 93.4.7
#
# OBJECTIF :
# Verifier qu'un chauffeur ne peut pas annuler une course.
#
# SECURITE :
# - Authentification avec le compte chauffeur.jean
# - Mot de passe saisi sans affichage
# - Identifiant de course fictif
# - Aucun changement attendu dans PostgreSQL
# ============================================================

$ErrorActionPreference = "Stop"

# Configuration de l'API.
$BaseUrl = "http://localhost:8000"
$Utilisateur = "chauffeur.jean"
$CourseFictive = 999999999

# Demander le mot de passe sans l'afficher.
$MotDePasseSecurise = Read-Host "Mot de passe de $Utilisateur" -AsSecureString

# Convertir temporairement le mot de passe pour construire le JSON.
$Ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($MotDePasseSecurise)

try {
    $MotDePasse = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($Ptr)

    # Construire le corps JSON de connexion.
    $CorpsConnexion = @{
        username = $Utilisateur
        password = $MotDePasse
    } | ConvertTo-Json -Compress
}
finally {
    # Liberer la memoire non geree utilisee pour le mot de passe.
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Ptr)
}

Remove-Variable MotDePasse -ErrorAction SilentlyContinue

# Authentifier le chauffeur avec un JSON encode en UTF-8.
try {
    $Connexion = Invoke-RestMethod `
        -Uri "$BaseUrl/auth/login" `
        -Method Post `
        -ContentType "application/json; charset=utf-8" `
        -Body ([System.Text.Encoding]::UTF8.GetBytes($CorpsConnexion))
}
catch {
    Write-Host "ECHEC : authentification impossible." -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

# Effacer le corps de connexion des variables du script.
$CorpsConnexion = $null

if (-not $Connexion.access_token) {
    Write-Host "ECHEC : aucun jeton JWT recu." -ForegroundColor Red
    exit 1
}

Write-Host "SUCCES : authentification du chauffeur." -ForegroundColor Green

# Confirmer le role du compte connecte.
if ($Connexion.role -ne "DRIVER") {
    Write-Host "ECHEC : le compte n'a pas le role DRIVER." -ForegroundColor Red
    exit 1
}

Write-Host "SUCCES : role DRIVER confirme." -ForegroundColor Green

# Preparer le jeton d'authentification.
$Headers = @{
    Authorization = "Bearer $($Connexion.access_token)"
}

# Construire une requete d'annulation valide.
$CorpsAnnulation = @{
    notes = "TEST SECURITE - ANNULATION INTERDITE"
} | ConvertTo-Json -Compress

# Tenter d'annuler une course fictive.
# Le resultat attendu est HTTP 403.
try {
    $null = Invoke-RestMethod `
        -Uri "$BaseUrl/trips/$CourseFictive/cancel" `
        -Method Put `
        -Headers $Headers `
        -ContentType "application/json; charset=utf-8" `
        -Body ([System.Text.Encoding]::UTF8.GetBytes($CorpsAnnulation))

    Write-Host "ECHEC : la requete d'annulation a ete acceptee !" -ForegroundColor Red
    exit 1
}
catch {
    # Recuperer le code HTTP retourne par l'API.
    $Code = 0

    if ($null -ne $_.Exception.Response) {
        $Code = [int]$_.Exception.Response.StatusCode
    }

    if ($Code -eq 403) {
        Write-Host "SUCCES : annulation refusee au chauffeur (HTTP 403)." -ForegroundColor Green
    }
    else {
        Write-Host "ECHEC : code HTTP inattendu : $Code" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "TEST DE SECURITE ANNULATION REUSSI." -ForegroundColor Green
