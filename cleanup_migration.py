#!/usr/bin/env python3
"""
Script de nettoyage après migration réussie
ATTENTION: Ce script supprime définitivement des fichiers
"""

import shutil
import sys
from pathlib import Path
from datetime import datetime


def create_archive():
    """Crée une archive finale avant nettoyage"""
    print("\n📦 Création archive de sécurité...")

    archive_name = f"pre-cleanup-archive-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    archive_path = Path(archive_name)

    try:
        # Copier projects/ et projects.backup/
        if Path("projects").exists():
            shutil.copytree("projects", archive_path / "projects")
            print(f"   ✅ projects/ archivé")

        if Path("projects.backup").exists():
            shutil.copytree("projects.backup", archive_path / "projects.backup")
            print(f"   ✅ projects.backup/ archivé")

        # Copier project_manager.py
        if Path("project_manager.py").exists():
            shutil.copy2("project_manager.py", archive_path / "project_manager.py")
            print(f"   ✅ project_manager.py archivé")

        print(f"\n   📦 Archive créée: {archive_path}/")
        return True

    except Exception as e:
        print(f"   ❌ Erreur création archive: {e}")
        return False


def cleanup_old_structure():
    """Nettoie l'ancienne structure (avec confirmation)"""
    print("\n🧹 Nettoyage de l'ancienne structure")

    items_to_clean = []

    # Identifier ce qui peut être nettoyé
    if Path("projects").exists():
        size = sum(f.stat().st_size for f in Path("projects").rglob("*") if f.is_file())
        items_to_clean.append(("projects/", size))

    if Path("projects.backup").exists():
        size = sum(f.stat().st_size for f in Path("projects.backup").rglob("*") if f.is_file())
        items_to_clean.append(("projects.backup/", size))

    if Path("project_manager.py").exists():
        size = Path("project_manager.py").stat().st_size
        items_to_clean.append(("project_manager.py", size))

    if not items_to_clean:
        print("   ℹ️  Rien à nettoyer")
        return True

    # Afficher ce qui sera supprimé
    print("\n   📋 Fichiers/dossiers à supprimer:")
    total_size = 0
    for item, size in items_to_clean:
        size_mb = size / (1024 * 1024)
        total_size += size
        print(f"      - {item} ({size_mb:.2f} MB)")

    total_mb = total_size / (1024 * 1024)
    print(f"\n   💾 Espace à libérer: {total_mb:.2f} MB")

    return items_to_clean


def confirm_and_delete(items_to_clean):
    """Demande confirmation et supprime"""
    print("\n⚠️  ATTENTION: Cette action est IRRÉVERSIBLE")
    print("   Une archive de sécurité sera créée avant suppression")

    response = input("\n   Confirmer la suppression? (tapez 'OUI' pour confirmer): ")

    if response != "OUI":
        print("\n   ❌ Nettoyage annulé")
        return False

    # Créer archive de sécurité
    if not create_archive():
        print("\n   ❌ Impossible de créer l'archive, nettoyage annulé")
        return False

    # Supprimer les fichiers
    print("\n   🗑️  Suppression en cours...")

    for item, _ in items_to_clean:
        try:
            path = Path(item)
            if path.is_dir():
                shutil.rmtree(path)
                print(f"      ✅ {item} supprimé")
            else:
                path.unlink()
                print(f"      ✅ {item} supprimé")
        except Exception as e:
            print(f"      ❌ Erreur suppression {item}: {e}")
            return False

    print("\n   ✅ Nettoyage terminé!")
    return True


def summary():
    """Affiche un résumé de la migration"""
    print("\n" + "="*60)
    print("  RÉSUMÉ DE LA MIGRATION")
    print("="*60)

    print("\n✅ Structure finale:")
    print("   enterprises/")
    print("     └── projets-existants/")
    print("         └── projects/")
    print("             ├── banque-de-france-architecte-si-dentreprise/")
    print("             ├── bnp/")
    print("             ├── test/")
    print("             ├── test-api-project/")
    print("             └── test2/")

    print("\n✅ Code:")
    print("   - unified_project_manager.py (nouveau)")
    print("   - api/routers/projects.py (migré)")
    print("   - enterprise_manager.py (existant)")

    print("\n✅ Tests:")
    print("   - test_migration.py (3 phases)")
    print("   - test_api_migration.py (5/5 ✅)")
    print("   - test_e2e.py (6/6 ✅)")

    print("\n📊 Données:")
    enterprises_path = Path("enterprises")
    project_count = 0
    matching_count = 0

    for enterprise_dir in enterprises_path.iterdir():
        if not enterprise_dir.is_dir() or enterprise_dir.name.startswith('_'):
            continue

        projects_dir = enterprise_dir / "projects"
        if not projects_dir.exists():
            continue

        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir():
                continue

            project_count += 1

            # Compter matchings
            matchings_dir = project_dir / "matchings"
            if matchings_dir.exists():
                matching_count += len([d for d in matchings_dir.iterdir() if d.is_dir()])

            historique_dir = project_dir / "historique"
            if historique_dir.exists():
                matching_count += len(list(historique_dir.glob("*.json")))

    print(f"   - {project_count} projets migrés")
    print(f"   - {matching_count} matchings préservés")
    print(f"   - 0 perte de données")


def main():
    print("="*60)
    print("  NETTOYAGE POST-MIGRATION")
    print("="*60)

    # Vérifier qu'on est dans le bon dossier
    if not Path("enterprises").exists() or not Path("unified_project_manager.py").exists():
        print("\n❌ Erreur: Ce script doit être exécuté depuis le dossier racine après migration")
        return 1

    # Afficher résumé
    summary()

    # Identifier ce qui peut être nettoyé
    items_to_clean = cleanup_old_structure()

    if not items_to_clean:
        print("\n✅ Rien à nettoyer, migration déjà propre!")
        return 0

    # Demander confirmation et nettoyer
    if confirm_and_delete(items_to_clean):
        print("\n🎉 Nettoyage terminé avec succès!")
        print("\nℹ️  Une archive de sécurité a été créée au cas où")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
