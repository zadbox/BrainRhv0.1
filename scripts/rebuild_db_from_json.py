#!/usr/bin/env python3
"""
Script de reconstruction de la DB depuis les fichiers JSON
À utiliser après nettoyage ou test pour re-peupler brainrh.db
"""

import sys
from pathlib import Path
import json

# Ajouter le projet au PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from brainrh.database import get_session, init_db
from brainrh.services.enterprise_service import EnterpriseService
from brainrh.services.project_service import ProjectService

def rebuild_database():
    """Reconstruit la DB depuis les fichiers JSON existants"""

    print("🔧 RECONSTRUCTION DE LA BASE DE DONNÉES")
    print("=" * 50)

    # Initialiser la DB
    print("\n1. Initialisation de la base de données...")
    init_db()
    print("   ✅ Base initialisée")

    enterprises_dir = PROJECT_ROOT / "enterprises"

    if not enterprises_dir.exists():
        print("   ❌ Dossier enterprises/ introuvable")
        return

    # Scanner les entreprises
    print("\n2. Scan des entreprises...")
    enterprises_count = 0
    projects_count = 0

    for enterprise_dir in enterprises_dir.iterdir():
        if not enterprise_dir.is_dir() or enterprise_dir.name.startswith('.'):
            continue

        enterprise_json = enterprise_dir / "enterprise.json"
        if not enterprise_json.exists():
            print(f"   ⚠️  Pas de enterprise.json dans {enterprise_dir.name}, skip")
            continue

        # Lire enterprise.json
        with open(enterprise_json, 'r', encoding='utf-8') as f:
            enterprise_data = json.load(f)

        try:
            # Créer l'entreprise dans la DB
            EnterpriseService.create_enterprise(enterprise_data)
            enterprises_count += 1
            print(f"   ✅ Entreprise: {enterprise_data['nom']} ({enterprise_data['id']})")
        except Exception as e:
            print(f"   ❌ Erreur entreprise {enterprise_data['id']}: {e}")
            continue

        # Scanner les projets de cette entreprise
        projects_dir = enterprise_dir / "projects"
        if not projects_dir.exists():
            continue

        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir() or project_dir.name.startswith('.'):
                continue

            projet_json = project_dir / "projet.json"
            if not projet_json.exists():
                continue

            # Lire projet.json
            with open(projet_json, 'r', encoding='utf-8') as f:
                projet_data = json.load(f)

            # S'assurer que enterprise_id est présent
            if "enterprise_id" not in projet_data:
                projet_data["enterprise_id"] = enterprise_data["id"]

            try:
                # Créer le projet dans la DB
                ProjectService.create_project(projet_data)
                projects_count += 1
                print(f"      ✅ Projet: {projet_data['nom']} ({projet_data['id']})")
            except Exception as e:
                print(f"      ❌ Erreur projet {projet_data['id']}: {e}")

    print("\n" + "=" * 50)
    print(f"✅ RECONSTRUCTION TERMINÉE")
    print(f"   📊 {enterprises_count} entreprises")
    print(f"   📊 {projects_count} projets")
    print("=" * 50)

if __name__ == "__main__":
    rebuild_database()
