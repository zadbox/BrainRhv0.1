#!/usr/bin/env python3
"""
Script de migration amélioré: projects/ → enterprises/{id}/projects/
Respecte les enterprise_id déjà assignés aux projets
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List


def migrate_projects_to_enterprises():
    """
    Migre les projets depuis projects/ vers enterprises/{id}/projects/
    en respectant les enterprise_id déjà assignés
    """
    print("="*60)
    print("  MIGRATION: projects/ → enterprises/{id}/projects/")
    print("="*60)

    # Chemins
    old_projects_folder = Path("projects")
    enterprises_folder = Path("enterprises")

    # Vérifier que projects/ existe
    if not old_projects_folder.exists():
        print("❌ Dossier 'projects/' introuvable")
        return False

    # Charger l'index des projets
    old_index_file = old_projects_folder / "_index.json"
    if not old_index_file.exists():
        print("❌ Fichier '_index.json' introuvable dans projects/")
        return False

    with open(old_index_file, 'r', encoding='utf-8') as f:
        old_index = json.load(f)

    projects = old_index.get("projects", [])

    if not projects:
        print("⚠️  Aucun projet à migrer")
        return True

    print(f"\n📋 {len(projects)} projet(s) à migrer\n")

    # Grouper les projets par enterprise_id
    projects_by_enterprise: Dict[str, List[Dict]] = {}
    projects_without_enterprise: List[Dict] = []

    for project in projects:
        enterprise_id = project.get("enterprise_id")
        if enterprise_id:
            if enterprise_id not in projects_by_enterprise:
                projects_by_enterprise[enterprise_id] = []
            projects_by_enterprise[enterprise_id].append(project)
        else:
            projects_without_enterprise.append(project)

    # Statistiques
    print(f"   ✅ Projets avec enterprise_id: {sum(len(p) for p in projects_by_enterprise.values())}")
    for eid, projs in projects_by_enterprise.items():
        print(f"      → {eid}: {len(projs)} projet(s)")

    if projects_without_enterprise:
        print(f"   ⚠️  Projets sans enterprise_id: {len(projects_without_enterprise)}")
        print(f"      → Seront migrés vers 'projets-existants'")

    print()

    # Vérifier que les entreprises cibles existent
    for enterprise_id in projects_by_enterprise.keys():
        enterprise_dir = enterprises_folder / enterprise_id
        if not enterprise_dir.exists():
            print(f"❌ Entreprise '{enterprise_id}' introuvable dans enterprises/")
            return False

    # Migrer les projets
    migrated_count = 0
    errors = []

    # 1. Migrer les projets avec enterprise_id
    for enterprise_id, enterprise_projects in projects_by_enterprise.items():
        print(f"🔄 Migration vers entreprise '{enterprise_id}'...")

        enterprise_dir = enterprises_folder / enterprise_id
        target_projects_folder = enterprise_dir / "projects"
        target_projects_folder.mkdir(exist_ok=True)

        # Charger ou créer l'index de projets pour cette entreprise
        target_index_file = target_projects_folder / "_index.json"
        if target_index_file.exists():
            with open(target_index_file, 'r', encoding='utf-8') as f:
                target_index = json.load(f)
        else:
            target_index = {"projects": []}

        for project in enterprise_projects:
            project_id = project['id']
            old_project_dir = old_projects_folder / project_id
            new_project_dir = target_projects_folder / project_id

            if not old_project_dir.exists():
                errors.append(f"Projet '{project_id}' introuvable dans projects/")
                continue

            try:
                # Copier le dossier du projet (avec tous ses sous-dossiers: cvs, matchings, historique, etc.)
                if new_project_dir.exists():
                    print(f"   ⚠️  Le projet '{project_id}' existe déjà, écrasement...")
                    shutil.rmtree(new_project_dir)

                shutil.copytree(old_project_dir, new_project_dir)

                # Ajouter à l'index si pas déjà présent
                if not any(p['id'] == project_id for p in target_index['projects']):
                    target_index['projects'].append(project)

                print(f"   ✅ {project['nom']} ({project_id})")
                migrated_count += 1

            except Exception as e:
                errors.append(f"Erreur lors de la migration de '{project_id}': {str(e)}")

        # Sauvegarder l'index de l'entreprise
        with open(target_index_file, 'w', encoding='utf-8') as f:
            json.dump(target_index, f, ensure_ascii=False, indent=2)

    # 2. Migrer les projets sans enterprise_id vers "projets-existants"
    if projects_without_enterprise:
        print(f"\n🔄 Migration des projets sans enterprise_id vers 'projets-existants'...")

        default_enterprise_id = "projets-existants"
        enterprise_dir = enterprises_folder / default_enterprise_id

        if not enterprise_dir.exists():
            print(f"   ⚠️  Entreprise '{default_enterprise_id}' introuvable, création...")
            enterprise_dir.mkdir(parents=True, exist_ok=True)

        target_projects_folder = enterprise_dir / "projects"
        target_projects_folder.mkdir(exist_ok=True)

        # Charger ou créer l'index
        target_index_file = target_projects_folder / "_index.json"
        if target_index_file.exists():
            with open(target_index_file, 'r', encoding='utf-8') as f:
                target_index = json.load(f)
        else:
            target_index = {"projects": []}

        for project in projects_without_enterprise:
            project_id = project['id']
            old_project_dir = old_projects_folder / project_id
            new_project_dir = target_projects_folder / project_id

            if not old_project_dir.exists():
                errors.append(f"Projet '{project_id}' introuvable dans projects/")
                continue

            try:
                if new_project_dir.exists():
                    print(f"   ⚠️  Le projet '{project_id}' existe déjà, écrasement...")
                    shutil.rmtree(new_project_dir)

                shutil.copytree(old_project_dir, new_project_dir)

                # Mettre à jour le projet pour ajouter enterprise_id
                project['enterprise_id'] = default_enterprise_id

                # Mettre à jour le fichier projet.json
                projet_file = new_project_dir / "projet.json"
                if projet_file.exists():
                    with open(projet_file, 'r', encoding='utf-8') as f:
                        projet_data = json.load(f)
                    projet_data['enterprise_id'] = default_enterprise_id
                    with open(projet_file, 'w', encoding='utf-8') as f:
                        json.dump(projet_data, f, ensure_ascii=False, indent=2)

                # Ajouter à l'index
                if not any(p['id'] == project_id for p in target_index['projects']):
                    target_index['projects'].append(project)

                print(f"   ✅ {project['nom']} ({project_id})")
                migrated_count += 1

            except Exception as e:
                errors.append(f"Erreur lors de la migration de '{project_id}': {str(e)}")

        # Sauvegarder l'index
        with open(target_index_file, 'w', encoding='utf-8') as f:
            json.dump(target_index, f, ensure_ascii=False, indent=2)

    # Résumé
    print(f"\n{'='*60}")
    print(f"  RÉSUMÉ DE LA MIGRATION")
    print(f"{'='*60}")
    print(f"✅ {migrated_count}/{len(projects)} projet(s) migré(s)")

    if errors:
        print(f"\n❌ {len(errors)} erreur(s):")
        for error in errors:
            print(f"   - {error}")
        return False

    print(f"\n✅ Migration terminée avec succès!")
    print(f"\nℹ️  Le dossier 'projects/' original est conservé pour rollback")
    print(f"   Vous pouvez le supprimer après validation complète")

    return True


if __name__ == "__main__":
    import sys
    success = migrate_projects_to_enterprises()
    sys.exit(0 if success else 1)
