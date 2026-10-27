# ============================================================
# BOUKOULOU TRANSPORT V5.9 - ETAPE 93.4.4
#
# Correction de l'emplacement des tests de disponibilites.
#
# - Cree une sauvegarde du script Python.
# - Deplace le bloc de tests a la fin de la session SQLite.
# - Ne modifie pas PostgreSQL.
# ============================================================

$Fichier = ".\tester_isolation_reelle_etape93.py"
$Sauvegarde = ".\tester_isolation_reelle_etape93_avant_deplacement.py"

# Sauvegarder le fichier avant toute modification.
Copy-Item $Fichier $Sauvegarde -Force

# Lire le contenu complet.
$Contenu = Get-Content $Fichier -Raw

# Identifier le debut du bloc mal place.
$Debut = $Contenu.IndexOf(
    "# BOUKOULOU TRANSPORT V5.9 - ETAPE 93.4.4"
)

# Identifier la fin du bloc.
$FinMarqueur = 'print("SUCCES : calcul des disponibilites correct.")'

$Fin = $Contenu.IndexOf($FinMarqueur, $Debut)

if ($Debut -lt 0 -or $Fin -lt 0) {
    throw "Bloc de tests introuvable. Aucune modification effectuee."
}

# Revenir au debut de la ligne du titre.
$Debut = $Contenu.LastIndexOf("`n", $Debut) + 1

# Inclure la derniere instruction du bloc.
$Fin = $Fin + $FinMarqueur.Length

# Extraire le bloc.
$Bloc = $Contenu.Substring($Debut, $Fin - $Debut)

# Retirer le bloc de son emplacement actuel.
$Contenu = $Contenu.Remove($Debut, $Fin - $Debut)

# Rechercher le message final du programme.
$MarqueurFinal = 'print("TOUS LES TESTS D' + "'" + 'ISOLATION SONT REUSSIS.")'

$Position = $Contenu.LastIndexOf($MarqueurFinal)

if ($Position -lt 0) {
    throw "Message final introuvable. Aucune modification du fichier original."
}

# Inserer le bloc avant le message final.
$Contenu = $Contenu.Insert(
    $Position,
    "`n    " + $Bloc.TrimStart() + "`n`n"
)

# Enregistrer le fichier corrige.
Set-Content -Path $Fichier -Value $Contenu -Encoding UTF8

Write-Host "Bloc de tests deplace." -ForegroundColor Green
Write-Host "Sauvegarde : $Sauvegarde"