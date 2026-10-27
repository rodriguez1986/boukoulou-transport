# ============================================================
# BOUKOULOU TRANSPORT V5.9 - ETAPE 93
# SECURISATION DES OPERATIONS DE COURSE
#
# Objectif :
# Remplacer la recherche directe d'une course par
# une recherche qui applique les droits de l'utilisateur.
#
# Fonctions concernees :
# - start_trip()
# - complete_trip()
#
# Securite :
# - Verification des fonctions cibles.
# - Aucune modification des donnees PostgreSQL.
# - Aucune modification des regles metier existantes.
# ============================================================

from pathlib import Path
import ast

# Fichier principal de l'API.
fichier = Path("app/main.py")

# Lire le contenu sans modifier le fichier.
contenu = fichier.read_text(encoding="utf-8")

# Rechercher les fonctions Python dans le fichier.
arbre = ast.parse(contenu)

fonctions = {
    noeud.name: noeud
    for noeud in arbre.body
    if isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef))
}

# Les deux fonctions doivent exister.
cibles = ("start_trip", "complete_trip")

for nom in cibles:
    if nom not in fonctions:
        raise RuntimeError(
            f"Fonction introuvable : {nom}. Aucune modification."
        )

# Ancien bloc de recherche directe.
ancien_bloc = """    trip = db.get(Trip, trip_id)

    if not trip:
        raise HTTPException(404, "Course introuvable")"""

# Nouveau bloc avec controle d'autorisation.
nouveau_bloc = """    # --------------------------------------------------------
    # V5.9 - ETAPE 93 : CONTROLE D'ACCES A LA COURSE
    #
    # Le chauffeur ne peut modifier que ses propres courses.
    # Une course non autorisee retourne HTTP 404.
    # --------------------------------------------------------
    trip = verifier_acces_course(db, u, trip_id)"""

# Travailler uniquement sur les lignes des deux fonctions.
lignes = contenu.splitlines(keepends=True)

# Appliquer les modifications de la fin vers le debut
# pour conserver les numeros de ligne des fonctions.
for nom in sorted(
    cibles,
    key=lambda n: fonctions[n].lineno,
    reverse=True
):
    fonction = fonctions[nom]

    debut = fonction.lineno - 1
    fin = fonction.end_lineno

    section = "".join(lignes[debut:fin])

    # Exiger exactement un bloc attendu par fonction.
    if section.count(ancien_bloc) != 1:
        raise RuntimeError(
            f"Bloc attendu absent ou ambigu dans {nom}. "
            "Aucune ecriture effectuee."
        )

    section = section.replace(
        ancien_bloc,
        nouveau_bloc,
        1
    )

    lignes[debut:fin] = section.splitlines(keepends=True)

# Reconstruire le fichier modifie.
nouveau_contenu = "".join(lignes)

# Verifier la syntaxe avant toute ecriture.
compile(nouveau_contenu, str(fichier), "exec")

# Ecrire seulement apres toutes les verifications.
fichier.write_text(
    nouveau_contenu,
    encoding="utf-8"
)

print("SUCCES : start_trip securisee.")
print("SUCCES : complete_trip securisee.")
print("Syntaxe Python validee.")