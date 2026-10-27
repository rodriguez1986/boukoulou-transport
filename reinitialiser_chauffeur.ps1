# ============================================================
# BOUKOULOU TRANSPORT V5.9 - ETAPE 93
# REINITIALISATION DU MOT DE PASSE CHAUFFEUR
#
# Utilisateur : chauffeur.jean
# Identifiant : 4
#
# Objectifs :
# - Authentifier l'administrateur.
# - Demander un nouveau mot de passe.
# - Verifier sa longueur.
# - Reinitialiser le mot de passe via l'API.
# - Afficher le detail d'une erreur HTTP si necessaire.
#
# Ce script ne modifie ni les courses ni les affectations.
# ============================================================

$ErrorActionPreference = "Stop"
$API = "http://localhost:8000"

try {

    # --------------------------------------------------------
    # 1. Authentification administrateur
    # --------------------------------------------------------

    $AdminSecret = Read-Host "Mot de passe ADMIN" -AsSecureString

    $AdminPassword = [System.Net.NetworkCredential]::new(
        "",
        $AdminSecret
    ).Password

    $AdminBody = @{
        username = "admin"
        password = $AdminPassword
    } | ConvertTo-Json

    $AdminConnexion = Invoke-RestMethod `
        -Uri "$API/auth/login" `
        -Method Post `
        -ContentType "application/json" `
        -Body $AdminBody

    # Conserver le jeton d'administration en memoire.
    $AdminHeaders = @{
        Authorization = "Bearer $($AdminConnexion.access_token)"
    }

    Write-Host "Connexion ADMIN reussie." -ForegroundColor Green

    # Effacer les variables contenant le mot de passe ADMIN.
    Remove-Variable AdminPassword, AdminSecret, AdminBody `
        -ErrorAction SilentlyContinue

    # --------------------------------------------------------
    # 2. Saisie du nouveau mot de passe chauffeur
    # --------------------------------------------------------

    $DriverSecret = Read-Host `
        "Nouveau mot de passe chauffeur.jean (12 a 128 caracteres)" `
        -AsSecureString

    $DriverPassword = [System.Net.NetworkCredential]::new(
        "",
        $DriverSecret
    ).Password

    # Respecter la validation imposee par FastAPI.
    if ($DriverPassword.Length -lt 12 -or $DriverPassword.Length -gt 128) {
        throw "Le mot de passe doit contenir entre 12 et 128 caracteres."
    }

    # --------------------------------------------------------
    # 3. Construction de la requete JSON
    # --------------------------------------------------------

    $ResetBody = @{
        password = $DriverPassword
    } | ConvertTo-Json

    # --------------------------------------------------------
    # 4. Reinitialisation via la route officielle
    # --------------------------------------------------------

    $Resultat = Invoke-RestMethod `
        -Uri "$API/users/4/reset-password" `
        -Method Post `
        -ContentType "application/json" `
        -Headers $AdminHeaders `
        -Body $ResetBody

    Write-Host "Mot de passe reinitialise avec succes !" `
        -ForegroundColor Green

    Write-Host "Utilisateur ID :" $Resultat.id
    Write-Host "Message :" $Resultat.message

}
catch {

    # --------------------------------------------------------
    # 5. Diagnostic des erreurs
    # --------------------------------------------------------

    Write-Host "Une erreur est survenue." -ForegroundColor Red
    Write-Host $_.Exception.Message

    # Afficher les details de validation FastAPI
    # sans afficher les valeurs envoyees.
    if ($_.ErrorDetails.Message) {

        try {
            $Reponse = $_.ErrorDetails.Message | ConvertFrom-Json

            if ($Reponse.detail -is [System.Array]) {
                foreach ($Element in $Reponse.detail) {
                    Write-Host "Champ :" ($Element.loc -join ".")
                    Write-Host "Type :" $Element.type
                    Write-Host "Message :" $Element.msg
                }
            }
            else {
                Write-Host "Detail API :" $Reponse.detail
            }
        }
        catch {
            Write-Host "Impossible de decoder la reponse API."
        }
    }
}
finally {

    # --------------------------------------------------------
    # 6. Nettoyage des donnees sensibles
    # --------------------------------------------------------

    Remove-Variable AdminPassword, AdminSecret, AdminBody, `
        DriverPassword, DriverSecret, ResetBody, `
        AdminHeaders, AdminConnexion `
        -ErrorAction SilentlyContinue
}