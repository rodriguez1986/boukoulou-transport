# ============================================================
# BOUKOULOU TRANSPORT V5.9 - ETAPE 93.4.6
#
# OBJECTIF :
# Verifier qu'un chauffeur authentifie ne peut pas
# creer une course.
#
# SECURITE :
# - Mot de passe masque.
# - Jeton JWT non affiche.
# - Aucun identifiant reel de course utilise.
# - Une reponse HTTP 403 est obligatoire.
# ============================================================

$ErrorActionPreference = "Stop"

$BaseUrl = "http://localhost:8000"
$Utilisateur = "chauffeur.jean"

# ------------------------------------------------------------
# 1. Demander le mot de passe du chauffeur.
# ------------------------------------------------------------

$MotDePasseSecurise = Read-Host `
    "Mot de passe de $Utilisateur" -AsSecureString

$Ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR(
    $MotDePasseSecurise
)

try {
    $MotDePasse = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($Ptr)

    # --------------------------------------------------------
    # 2. Preparer les identifiants au format JSON.
    # --------------------------------------------------------

    # Construire explicitement le JSON de connexion.
    # ConvertTo-Json gere les caracteres speciaux du mot de passe.

    $CorpsConnexion = @{
        username = $Utilisateur.Trim()
        password = $MotDePasse
    } | ConvertTo-Json -Compress

    # Ne jamais afficher le JSON : il contient le mot de passe.

  }
   finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Ptr)
  }

# Ne plus conserver la variable du mot de passe.
Remove-Variable MotDePasse -ErrorAction SilentlyContinue

# ------------------------------------------------------------
# 3. Se connecter a l'API.
# ------------------------------------------------------------

try {
    $Connexion = Invoke-RestMethod `
        -Uri "$BaseUrl/auth/login" `
        -Method Post `
        -ContentType "application/json" `
        -Body ([System.Text.Encoding]::UTF8.GetBytes($CorpsConnexion))

}
catch {
    Write-Host "ECHEC : authentification impossible." -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

# Effacer le corps contenant les identifiants.
$CorpsConnexion = $null

if (-not $Connexion.access_token) {
    Write-Host "ECHEC : aucun jeton JWT recu." -ForegroundColor Red
    exit 1
}

Write-Host "SUCCES : authentification du chauffeur." -ForegroundColor Green

# ------------------------------------------------------------
# 4. Verifier le role retourne par l'API.
# ------------------------------------------------------------

if ($Connexion.role -ne "DRIVER") {
    Write-Host "ECHEC : le compte n'a pas le role DRIVER." -ForegroundColor Red
    exit 1
}

Write-Host "SUCCES : role DRIVER confirme." -ForegroundColor Green

# ------------------------------------------------------------
# 5. Preparer la requete de creation interdite.
#
# Identifiants fictifs pour eviter toute interaction avec
# une course existante.
# ------------------------------------------------------------

$Headers = @{
    Authorization = "Bearer $($Connexion.access_token)"
}

$CorpsCourse = @{
    line_id = 999999999
    vehicle_id = 999999999
    driver_id = 999999999
    departure_at = "2030-01-01T08:00:00Z"
    notes = "TEST SECURITE - CREATION INTERDITE"
} | ConvertTo-Json

# ------------------------------------------------------------
# 6. Tenter la creation avec le compte DRIVER.
# ------------------------------------------------------------

try {
    $null = Invoke-RestMethod `
        -Uri "$BaseUrl/trips" `
        -Method Post `
        -Headers $Headers `
        -ContentType "application/json" `
        -Body $CorpsCourse

    Write-Host "ECHEC : la requete de creation a ete acceptee !" -ForegroundColor Red
    exit 1
}
catch {
    $Code = 0

    if ($null -ne $_.Exception.Response) {
        $Code = [int]$_.Exception.Response.StatusCode
    }

    if ($Code -eq 403) {
        Write-Host "SUCCES : creation refusee au chauffeur (HTTP 403)." -ForegroundColor Green
    }
    else {
        Write-Host "ECHEC : code HTTP inattendu : $Code" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "TEST DE SECURITE HTTP REUSSI." -ForegroundColor Green