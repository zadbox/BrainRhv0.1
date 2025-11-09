#!/usr/bin/env python3
"""
Script de normalisation des dossiers projets
Migre les projets legacy (projects/) vers la structure canonique (enterprises/)

Structure cible:
enterprises/<enterprise_id>/projects/<project_id>/
├── projet.json
├── offre_parsed.json (si existe)
├── cvs_raw/ (si existe)
├── cvs_parsed/ (si existe)
├── historique/ (si existe)
└── matchings/ (si existe)

Usage:
    python scripts/normalize_project_layout.py                # Dry-run
    python scripts/normalize_project_layout.py --apply        # Migration réelle
"""

import sys
import argparse
import shutil
from pathlib import Path
from datetime import datetime

# Ajouter le projet au PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from brainrh.database import get_session
from brainrh.models import ProjectDB


def parse_args():
    parser = argparse.ArgumentParser(description="Normalisation structure projets")
    parser.add_argument("--apply", action="store_true", help="Appliquer la migration (défaut: dry-run)")
    return parser.parse_args()


def scan_legacy_projects(projects_dir: Path) -> list:
    """
    Scanne les projets legacy dans projects/

    Returns:
        Liste de dicts avec infos projet legacy
    """
    legacy_projects = []

    if not projects_dir.exists():
        return legacy_projects

    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue

        if project_dir.name.startswith("_"):
            continue

        project_id = project_dir.name
        projet_file = project_dir / "projet.json"

        # Vérifier que le projet existe
        if not projet_file.exists():
            print(f"   ⚠️  {project_id}: pas de projet.json, ignoré")
            continue

        # Lister les fichiers/dossiers à migrer
        items_to_migrate = []
        for item in project_dir.iterdir():
            if item.name != "_index.json":  # Ignorer les index
                items_to_migrate.append(item.name)

        legacy_projects.append({
            "project_id": project_id,
            "source_dir": project_dir,
            "items": items_to_migrate
        })

    return legacy_projects


def get_target_enterprise_id(project_id: str) -> str:
    """
    Récupère l'enterprise_id depuis la DB, ou utilise 'projets-existants' par défaut

    Args:
        project_id: ID du projet

    Returns:
        enterprise_id
    """
    with get_session() as session:
        db_proj = session.get(ProjectDB, project_id)
        if db_proj and db_proj.enterprise_id:
            return db_proj.enterprise_id

    # Par défaut, utiliser 'projets-existants'
    return "projets-existants"


def normalize_project(legacy_info: dict, dry_run: bool = True) -> bool:
    """
    Normalise un projet legacy vers la structure canonique

    Args:
        legacy_info: Dict avec infos projet legacy
        dry_run: Si True, n'applique pas les changements

    Returns:
        True si succès, False sinon
    """
    project_id = legacy_info["project_id"]
    source_dir = legacy_info["source_dir"]

    # Déterminer l'enterprise_id cible
    enterprise_id = get_target_enterprise_id(project_id)
    target_dir = PROJECT_ROOT / "enterprises" / enterprise_id / "projects" / project_id

    print(f"\n   📦 Projet: {project_id}")
    print(f"      Source: {source_dir.relative_to(PROJECT_ROOT)}")
    print(f"      Cible:  {target_dir.relative_to(PROJECT_ROOT)}")
    print(f"      Enterprise: {enterprise_id}")
    print(f"      Items à migrer: {len(legacy_info['items'])}")

    # Vérifier si la cible existe déjà
    if target_dir.exists():
        print(f"      ⚠️  Cible existe déjà, fusion nécessaire")
        if not dry_run:
            # Fusionner: copier seulement ce qui n'existe pas
            for item_name in legacy_info['items']:
                source_item = source_dir / item_name
                target_item = target_dir / item_name

                if not target_item.exists():
                    if source_item.is_dir():
                        shutil.copytree(source_item, target_item)
                        print(f"         ✅ Copié dossier: {item_name}")
                    else:
                        shutil.copy2(source_item, target_item)
                        print(f"         ✅ Copié fichier: {item_name}")
                else:
                    print(f"         ⏭️  Existe déjà: {item_name}")
    else:
        if not dry_run:
            # Créer le dossier cible et déplacer
            target_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_dir), str(target_dir))
            print(f"      ✅ Déplacé vers {target_dir.relative_to(PROJECT_ROOT)}")
        else:
            print(f"      [DRY-RUN] Déplacerait vers {target_dir.relative_to(PROJECT_ROOT)}")

    return True


def update_json_file(project_id: str, enterprise_id: str, dry_run: bool = True):
    """
    Met à jour le fichier projet.json pour ajouter enterprise_id

    Args:
        project_id: ID du projet
        enterprise_id: Enterprise ID à ajouter
        dry_run: Si True, n'applique pas
    """
    projet_path = PROJECT_ROOT / "enterprises" / enterprise_id / "projects" / project_id / "projet.json"

    if not projet_path.exists():
        print(f"      ⚠️  Fichier projet.json introuvable: {projet_path}")
        return

    if dry_run:
        print(f"      [DRY-RUN] Ajouterait enterprise_id={enterprise_id} dans projet.json")
        return

    try:
        import json
        # Lire le JSON
        with open(projet_path, 'r', encoding='utf-8') as f:
            projet_data = json.load(f)

        # Ajouter/mettre à jour enterprise_id
        if projet_data.get("enterprise_id") != enterprise_id:
            projet_data["enterprise_id"] = enterprise_id
            projet_data["last_modified"] = datetime.now().isoformat()

            # Écrire le JSON mis à jour
            with open(projet_path, 'w', encoding='utf-8') as f:
                json.dump(projet_data, f, ensure_ascii=False, indent=2)

            print(f"      ✅ projet.json mis à jour avec enterprise_id={enterprise_id}")
        else:
            print(f"      ⏭️  enterprise_id déjà présent dans projet.json")

    except Exception as e:
        print(f"      ❌ Erreur mise à jour JSON: {e}")


def update_database(project_id: str, enterprise_id: str, dry_run: bool = True):
    """
    Met à jour la DB pour refléter le nouveau chemin

    Args:
        project_id: ID du projet
        enterprise_id: Nouvel enterprise_id
        dry_run: Si True, n'applique pas
    """
    new_json_path = f"enterprises/{enterprise_id}/projects/{project_id}/projet.json"

    if dry_run:
        print(f"      [DRY-RUN] Mettrait à jour DB: enterprise_id={enterprise_id}, json_path={new_json_path}")
    else:
        with get_session() as session:
            db_proj = session.get(ProjectDB, project_id)
            if db_proj:
                if not db_proj.enterprise_id:
                    db_proj.enterprise_id = enterprise_id
                db_proj.json_path = new_json_path
                db_proj.last_modified = datetime.now()
                session.add(db_proj)
                session.commit()
                print(f"      ✅ DB mise à jour: enterprise_id={enterprise_id}")


def clean_empty_legacy_dirs(projects_dir: Path, dry_run: bool = True):
    """
    Supprime les dossiers legacy vides après migration

    Args:
        projects_dir: Dossier projects/ legacy
        dry_run: Si True, n'applique pas
    """
    if not projects_dir.exists():
        return

    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue

        if project_dir.name.startswith("_"):
            continue

        # Vérifier si vide (ignorer .DS_Store, etc.)
        items = [item for item in project_dir.iterdir() if not item.name.startswith(".")]

        if not items:
            if dry_run:
                print(f"   [DRY-RUN] Supprimerait dossier vide: {project_dir.name}")
            else:
                shutil.rmtree(project_dir)
                print(f"   ✅ Supprimé dossier vide: {project_dir.name}")


def main():
    args = parse_args()
    dry_run = not args.apply

    print("=" * 60)
    print("🗂️  NORMALISATION STRUCTURE PROJETS")
    print("=" * 60)

    if dry_run:
        print("\n🔍 MODE: DRY-RUN (aucune modification)")
        print("   Pour appliquer: python scripts/normalize_project_layout.py --apply")
    else:
        print("\n⚠️  MODE: APPLY (modifications réelles)")
        response = input("\n   Continuer? (yes/no): ")
        if response.lower() != "yes":
            print("   Annulé.")
            return

    # Scanner les projets legacy
    projects_dir = PROJECT_ROOT / "projects"
    legacy_projects = scan_legacy_projects(projects_dir)

    print(f"\n📂 Projets legacy trouvés: {len(legacy_projects)}")

    if not legacy_projects:
        print("\n✅ Aucun projet legacy à migrer!")
        print("   Tous les projets sont déjà dans la structure canonique.")
        return

    # Migrer chaque projet
    migrated_count = 0
    for legacy_info in legacy_projects:
        try:
            if normalize_project(legacy_info, dry_run):
                project_id = legacy_info["project_id"]
                enterprise_id = get_target_enterprise_id(project_id)
                update_json_file(project_id, enterprise_id, dry_run)
                update_database(project_id, enterprise_id, dry_run)
                migrated_count += 1
        except Exception as e:
            print(f"      ❌ Erreur: {e}")

    # Nettoyer les dossiers vides
    if not dry_run:
        print("\n🧹 Nettoyage dossiers vides...")
        clean_empty_legacy_dirs(projects_dir, dry_run)

    # Résumé
    print("\n" + "=" * 60)
    if dry_run:
        print(f"📊 DRY-RUN TERMINÉ")
        print(f"   {migrated_count} projet(s) seraient migrés")
        print(f"\n   Pour appliquer: python scripts/normalize_project_layout.py --apply")
    else:
        print(f"✅ NORMALISATION TERMINÉE")
        print(f"   {migrated_count} projet(s) migrés vers structure canonique")
        print(f"\n   Structure cible: enterprises/<enterprise_id>/projects/<project_id>/")
    print("=" * 60)


if __name__ == "__main__":
    main()
