
# ============================================================
# BOUKOULOU TRANSPORT V5.9
# ETAPE 93.4.9.7.11
#
# Correction des fonctions de maintenance.
#
# SECURITE :
# - Sauvegarde automatique de main.py.
# - Modification du code Python uniquement.
# - Aucune connexion a PostgreSQL.
# - Aucun changement de schema.
# - Aucun redemarrage Docker.
# ============================================================

from pathlib import Path
from datetime import datetime
import ast

fichier = Path("app/main.py")

contenu = fichier.read_text(encoding="utf-8")

# Verifier que le fichier actuel est syntaxiquement valide.
ast.parse(contenu)

debut = contenu.find('@app.post("/maintenance")')
fin = contenu.find('# ============================================================\n# V4.2 - CARBURANT', debut)

if debut == -1 or fin == -1:
    raise SystemExit(
        "ERREUR : limites des fonctions de maintenance introuvables."
    )

section = contenu[debut:fin]

if section.count("def create_maintenance(") != 1:
    raise SystemExit("ERREUR : create_maintenance introuvable ou dupliquee.")

if section.count("def update_maintenance(") != 1:
    raise SystemExit("ERREUR : update_maintenance introuvable ou dupliquee.")

# Sauvegarder avant toute modification.
sauvegarde = fichier.with_name(
    "main_avant_correctif_maintenance_"
    + datetime.now().strftime("%Y%m%d_%H%M%S")
    + ".bak"
)

sauvegarde.write_text(contenu, encoding="utf-8")

nouvelle_section = '''
@app.post("/maintenance")
def create_maintenance(
    x: MaintenanceIn,
    u=Depends(roles("ADMIN")),
    db: Session = Depends(get_db)
):
    # Verrouiller le vehicule pendant toute la transaction.
    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.id == x.vehicle_id)
        .with_for_update()
        .first()
    )

    if not vehicle:
        db.rollback()
        raise HTTPException(404, "Vehicule introuvable")

    if x.status not in ("PLANNED", "IN_PROGRESS", "COMPLETED"):
        db.rollback()
        raise HTTPException(422, "Statut de maintenance invalide")

    # Une maintenance en cours immobilise le vehicule.
    if x.status == "IN_PROGRESS":
        course = (
            db.query(Trip)
            .filter(
                Trip.vehicle_id == vehicle.id,
                Trip.status == "IN_PROGRESS"
            )
            .first()
        )

        if course:
            db.rollback()
            raise HTTPException(
                409,
                f"Le bus effectue deja la course #{course.id}"
            )

    data = x.model_dump()

    m = Maintenance(
        **data,
        done=(x.status == "COMPLETED")
    )

    if x.status == "COMPLETED":
        m.completed_at = datetime.now(timezone.utc)

    # PLANNED n'immobilise pas le bus.
    # IN_PROGRESS immobilise le bus.
    if x.status == "IN_PROGRESS":
        vehicle.status = "MAINTENANCE"

    # Une maintenance terminee ou planifiee ne doit pas
    # annuler une autre immobilisation.
    if x.mileage is not None and x.mileage > vehicle.mileage:
        vehicle.mileage = x.mileage

    db.add(m)
    db.commit()
    db.refresh(m)

    audit(db, u, "CREATE_MAINTENANCE", f"{vehicle.code}:{m.id}")

    return m


@app.get("/maintenance/{maintenance_id}")
def get_maintenance(
    maintenance_id: int,
    u=Depends(roles("ADMIN", "CONTROLLER")),
    db: Session = Depends(get_db)
):
    m = db.get(Maintenance, maintenance_id)

    if not m:
        raise HTTPException(404, "Maintenance introuvable")

    return m


@app.put("/maintenance/{maintenance_id}")
def update_maintenance(
    maintenance_id: int,
    x: MaintenanceUpdate,
    u=Depends(roles("ADMIN")),
    db: Session = Depends(get_db)
):
    # Identifier d'abord le vehicule de la maintenance.
    m = db.get(Maintenance, maintenance_id)

    if not m:
        db.rollback()
        raise HTTPException(404, "Maintenance introuvable")

    # Verrouiller le vehicule avant les modifications.
    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.id == m.vehicle_id)
        .with_for_update()
        .first()
    )

    if not vehicle:
        db.rollback()
        raise HTTPException(404, "Vehicule introuvable")

    # Verrouiller egalement la maintenance concernee.
    m = (
        db.query(Maintenance)
        .filter(Maintenance.id == maintenance_id)
        .with_for_update()
        .first()
    )

    data = x.model_dump(exclude_unset=True)

    # Ne pas accepter de statut inconnu.
    nouveau_statut = data.get("status", m.status)

    if nouveau_statut not in ("PLANNED", "IN_PROGRESS", "COMPLETED"):
        db.rollback()
        raise HTTPException(422, "Statut de maintenance invalide")

    # Interdire une immobilisation pendant une course.
    if nouveau_statut == "IN_PROGRESS":
        course = (
            db.query(Trip)
            .filter(
                Trip.vehicle_id == vehicle.id,
                Trip.status == "IN_PROGRESS"
            )
            .first()
        )

        if course:
            db.rollback()
            raise HTTPException(
                409,
                f"Maintenance impossible : course #{course.id} en cours"
            )

    # Appliquer les modifications apres les controles.
    for field, value in data.items():
        setattr(m, field, value)

    if m.mileage is not None and m.mileage > vehicle.mileage:
        vehicle.mileage = m.mileage

    if nouveau_statut == "COMPLETED":
        m.done = True

        if m.completed_at is None:
            m.completed_at = datetime.now(timezone.utc)

    else:
        m.done = False

    # Verifier si une autre maintenance immobilise le bus.
    # autoflush=False : inclure explicitement le nouveau
    # statut de la maintenance actuelle dans le calcul.
    autre_maintenance_active = (
        db.query(Maintenance)
        .filter(
            Maintenance.vehicle_id == vehicle.id,
            Maintenance.id != m.id,
            Maintenance.status == "IN_PROGRESS"
        )
        .first()
    )

    immobilisation_active = (
        nouveau_statut == "IN_PROGRESS"
        or autre_maintenance_active is not None
    )

    if immobilisation_active:
        vehicle.status = "MAINTENANCE"
    elif vehicle.status == "MAINTENANCE":
        vehicle.status = "ACTIVE"

    db.commit()
    db.refresh(m)

    audit(db, u, "UPDATE_MAINTENANCE", str(m.id))

    return m


'''

nouveau_contenu = (
    contenu[:debut]
    + nouvelle_section
    + contenu[fin:]
)

# Verifier la syntaxe AVANT de remplacer le fichier.
ast.parse(nouveau_contenu)

fichier.write_text(nouveau_contenu, encoding="utf-8")

print("SUCCES : fonctions de maintenance corrigees.")
print("Sauvegarde :", sauvegarde)
print("Aucune modification de PostgreSQL.")
