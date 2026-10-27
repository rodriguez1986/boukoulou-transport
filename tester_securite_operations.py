# ============================================================
# BOUKOULOU TRANSPORT V5.9 - ETAPE 93
# TEST DE SECURITE DES OPERATIONS DE COURSE
#
# Objectif :
# Verifier que les fonctions start_trip et complete_trip
# utilisent le controle d'acces obligatoire.
#
# Ce test :
# - Ne se connecte pas a PostgreSQL.
# - Ne demarre aucune course.
# - Ne termine aucune course.
# - Ne modifie aucune donnee.
# ============================================================

import ast
from pathlib import Path

# ------------------------------------------------------------
# 1. Lire le fichier source
# ------------------------------------------------------------

fichier = Path("app/main.py")
source = fichier.read_text(encoding="utf-8")

# Construire l'arbre syntaxique Python.
arbre = ast.parse(source)

# ------------------------------------------------------------
# 2. Rechercher les deux fonctions
# ------------------------------------------------------------

fonctions = {
    noeud.name: noeud
    for noeud in arbre.body
    if isinstance(noeud, ast.FunctionDef)
}

# ------------------------------------------------------------
# 3. Verifier chaque fonction
# ------------------------------------------------------------

for nom in ("start_trip", "complete_trip"):

    if nom not in fonctions:
        raise AssertionError(
            f"ECHEC : fonction {nom} introuvable"
        )

    fonction = fonctions[nom]

    # Rechercher les appels au controle d'acces.
    appels = [
        noeud
        for noeud in ast.walk(fonction)
        if isinstance(noeud, ast.Call)
        and isinstance(noeud.func, ast.Name)
        and noeud.func.id == "verifier_acces_course"
    ]

    if len(appels) != 1:
        raise AssertionError(
            f"ECHEC : {nom} doit appeler une fois "
            "verifier_acces_course"
        )

    # Verifier que le controle d'acces est effectue
    # avant tout appel a db.commit().
    commits = [
        noeud
        for noeud in ast.walk(fonction)
        if isinstance(noeud, ast.Call)
        and isinstance(noeud.func, ast.Attribute)
        and noeud.func.attr == "commit"
    ]

    if commits and appels[0].lineno >= min(
        commit.lineno for commit in commits
    ):
        raise AssertionError(
            f"ECHEC : controle d'acces trop tardif dans {nom}"
        )

    print(f"SUCCES : {nom} appelle le controle d'acces avant commit.")

print("TEST STATIQUE TERMINE AVEC SUCCES.")