#!/usr/bin/env python3
"""
Script de migration: ancienne structure (projets seuls) → nouvelle structure (entreprises > projets)
"""

import json
import shutil
from pathlib import Path
from enterprise_manager import EnterpriseManager
from project_manager import ProjectManager


def migrate_old_projects_to_enterprises():
    """
    Migre les anciens projets vers la nouvelle structure avec entreprises
    """
    print("=== Migration vers la structure Entreprises ===\n")

    # Chemins
    old_projects_folder = Path("projects")
    enterprises_folder = Path("enterprises")

    # Vérifier si l'ancien dossier existe
    if not old_projects_folder.exists():
        print("Aucun ancien projet à migrer (dossier 'projects' introuvable)")
        return

    # Charger l'ancien index
    old_index_file = old_projects_folder / "_index.json"
    if not old_index_file.exists():
        print("Aucun index de projets trouvé")
        return

    with open(old_index_file, 'r', encoding='utf-8') as f:
        old_index = json.load(f)

    old_projects = old_index.get("projects", [])

    if not old_projects:
        print("Aucun projet à migrer")
        return

    print(f"Trouvé {len(old_projects)} projet(s) à migrer\n")

    # Créer une entreprise "Migration" pour regrouper les anciens projets
    em = EnterpriseManager()

    # Créer l'entreprise de migration
    enterprise = em.create_enterprise(
        nom="Projets Existants",
        secteur="Migration automatique"
    )

    print(f"Entreprise créée: {enterprise['nom']} (ID: {enterprise['id']})")

    # Récupérer le dossier projects de cette entreprise
    new_projects_folder = em.get_projects_folder(enterprise['id'])

    # Copier chaque projet
    migrated_count = 0
    for old_project in old_projects:
        project_id = old_project['id']
        old_project_dir = old_projects_folder / project_id
        new_project_dir = new_projects_folder / project_id

        if old_project_dir.exists():
            # Copier le dossier complet du projet
            shutil.copytree(old_project_dir, new_project_dir, dirs_exist_ok=True)
            print(f"  Migré: {old_project['nom']}")
            migrated_count += 1

    # Mettre à jour l'index des projets dans la nouvelle structure
    new_index_file = new_projects_folder / "_index.json"
    with open(new_index_file, 'w', encoding='utf-8') as f:
        json.dump(old_index, f, ensure_ascii=False, indent=2)

    # Mettre à jour le compteur de projets de l'entreprise
    em.update_projects_count(enterprise['id'])

    print(f"\nMigration terminée: {migrated_count} projet(s) migré(s)")
    print(f"\nL'ancien dossier 'projects' est toujours présent.")
    print(f"Vous pouvez le renommer en 'projects_old' pour sauvegarde.")
    print(f"\nPour utiliser la nouvelle structure, relancez l'application.")


if __name__ == "__main__":
    migrate_old_projects_to_enterprises()
