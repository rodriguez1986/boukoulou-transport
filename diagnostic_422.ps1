# ============================================================
# BOUKOULOU TRANSPORT V5.9 - ETAPE 93
# DIAGNOSTIC DE LA REINITIALISATION DU MOT DE PASSE
#
# Objectif :
# Retrouver une erreur HTTP 422 dans l'historique PowerShell.
#
# Securite :
# - Aucune connexion a l'API.
# - Aucune modification de PostgreSQL.
# - Aucun mot de passe affiche.
# ============================================================

$Erreur422 = $Error |
    Where-Object { $_.Exception.Message -match "422" } |
    Select-Object -First 1

if ($null -eq $Erreur422) {
    Write-Host "Erreur HTTP 422 introuvable." -ForegroundColor Yellow
}
else {
    Write-Host "Erreur HTTP 422 retrouvee." -ForegroundColor Green

    if ($Erreur422.ErrorDetails.Message) {
        try {
            $Reponse = $Erreur422.ErrorDetails.Message |
                ConvertFrom-Json

            foreach ($Element in $Reponse.detail) {
                Write-Host "Emplacement :" ($Element.loc -join ".")
                Write-Host "Type :" $Element.type
                Write-Host "Message :" $Element.msg
            }
        }
        catch {
            Write-Host "Detail de validation non disponible." -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "Aucun detail de validation disponible." -ForegroundColor Yellow
    }
}