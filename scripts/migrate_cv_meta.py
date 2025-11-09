#!/usr/bin/env python3
"""
Script d'indexation des CV parsés dans la table cv_meta

Parcourt les dossiers cvs_parsed/ et indexe les métadonnées dans cv_meta.

Usage:
    python scripts/migrate_cv_meta.py                # Dry-run
    python scripts/migrate_cv_meta.py --apply        # Indexation réelle
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Ajouter le projet au PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from brainrh.database import get_session
from brainrh.models import CVMetaDB


def parse_args():
    parser = argparse.ArgumentParser(description="Indexation CV dans cv_meta")
    parser.add_argument("--apply", action="store_true", help="Appliquer l'indexation (défaut: dry-run)")
    return parser.parse_args()


def scan_parsed_cvs() -> List[Dict]:
    """
    Scanne tous les CV parsés dans enterprises/ et projects/

    Returns:
        Liste de dicts avec métadonnées CV
    """
    cv_files = []

    # 1. Scanner enterprises/*/projects/*/cvs_parsed/
    enterprises_dir = PROJECT_ROOT / "enterprises"
    if enterprises_dir.exists():
        for ent_dir in enterprises_dir.iterdir():
            if not ent_dir.is_dir():
                continue

            projects_dir = ent_dir / "projects"
            if not projects_dir.exists():
                continue

            for project_dir in projects_dir.iterdir():
                if not project_dir.is_dir():
                    continue

                cvs_parsed_dir = project_dir / "cvs_parsed"
                if cvs_parsed_dir.exists():
                    cv_files.extend(scan_cvs_in_dir(cvs_parsed_dir, project_dir.name))

    # 2. Scanner projects/ legacy
    projects_legacy_dir = PROJECT_ROOT / "projects"
    if projects_legacy_dir.exists():
        for project_dir in projects_legacy_dir.iterdir():
            if not project_dir.is_dir():
                continue

            if project_dir.name.startswith("_"):
                continue

            cvs_parsed_dir = project_dir / "cvs_parsed"
            if cvs_parsed_dir.exists():
                cv_files.extend(scan_cvs_in_dir(cvs_parsed_dir, project_dir.name))

    return cv_files


def scan_cvs_in_dir(cvs_dir: Path, project_id: str) -> List[Dict]:
    """
    Scanne les CV dans un dossier cvs_parsed/

    Args:
        cvs_dir: Chemin vers cvs_parsed/
        project_id: ID du projet

    Returns:
        Liste de dicts avec métadonnées
    """
    cv_files = []

    for cv_file in cvs_dir.glob("*.json"):
        metadata = extract_cv_metadata(cv_file, project_id)
        if metadata:
            cv_files.append(metadata)

    return cv_files


def extract_cv_metadata(cv_file: Path, project_id: str) -> Optional[Dict]:
    """
    Extrait les métadonnées d'un CV parsé

    Args:
        cv_file: Chemin vers le JSON CV
        project_id: ID du projet

    Returns:
        Dict avec métadonnées ou None si erreur
    """
    try:
        # Lire le JSON
        with open(cv_file, 'r', encoding='utf-8') as f:
            cv_data = json.load(f)

        # Chemins relatifs depuis PROJECT_ROOT
        json_path = str(cv_file.relative_to(PROJECT_ROOT))

        # Chercher le PDF/DOCX source (même nom, différente extension)
        file_path = None
        cvs_raw_dir = cv_file.parent.parent / "cvs_raw"
        if cvs_raw_dir.exists():
            stem = cv_file.stem
            for ext in ['.pdf', '.docx', '.doc']:
                source_file = cvs_raw_dir / f"{stem}{ext}"
                if source_file.exists():
                    file_path = str(source_file.relative_to(PROJECT_ROOT))
                    break

        # Extraire parsed_at (stat du fichier)
        parsed_at = datetime.fromtimestamp(cv_file.stat().st_mtime)

        # Extraire candidat_nom et candidat_titre si présents
        identite = cv_data.get("identite", {})
        candidat_nom = (
            cv_data.get("nom") or
            cv_data.get("candidat", {}).get("nom") or
            identite.get("nom")
        )
        if identite.get("prenom"):
            candidat_nom = f"{identite.get('nom')} {identite.get('prenom')}" if candidat_nom else identite.get("prenom")

        candidat_titre = cv_data.get("titre") or cv_data.get("candidat", {}).get("titre")

        return {
            "filename": cv_file.name,
            "project_id": project_id,
            "json_path": json_path,
            "file_path": file_path,
            "parsed_at": parsed_at,
            "candidat_nom": candidat_nom,
            "candidat_titre": candidat_titre
        }

    except Exception as e:
        print(f"      ⚠️  Erreur lecture {cv_file.name}: {e}")
        return None


def detect_anomalies(cv_files: List[Dict]) -> List[str]:
    """
    Détecte les anomalies dans les CV scannés

    Args:
        cv_files: Liste des métadonnées CV

    Returns:
        Liste des warnings
    """
    warnings = []

    # 1. Fichiers source manquants
    missing_sources = [cv for cv in cv_files if not cv["file_path"]]
    if missing_sources:
        warnings.append(f"⚠️  {len(missing_sources)} CV sans fichier source (PDF/DOCX)")

    # 2. Doublons (même filename dans même projet)
    seen = {}
    for cv in cv_files:
        key = (cv["project_id"], cv["filename"])
        if key in seen:
            warnings.append(f"⚠️  Doublon: {cv['filename']} dans projet {cv['project_id']}")
        else:
            seen[key] = cv

    # 3. CV sans nom candidat
    missing_nom = [cv for cv in cv_files if not cv["candidat_nom"]]
    if missing_nom:
        warnings.append(f"⚠️  {len(missing_nom)} CV sans nom candidat")

    return warnings


def index_cv(cv_meta: Dict, dry_run: bool = True) -> bool:
    """
    Indexe un CV dans cv_meta

    Args:
        cv_meta: Métadonnées du CV
        dry_run: Si True, n'applique pas

    Returns:
        True si succès
    """
    if dry_run:
        return True

    try:
        with get_session() as session:
            # Vérifier si existe déjà
            from sqlmodel import select
            existing = session.exec(
                select(CVMetaDB).where(
                    CVMetaDB.project_id == cv_meta["project_id"],
                    CVMetaDB.filename == cv_meta["filename"]
                )
            ).first()

            if existing:
                # Mise à jour
                existing.json_path = cv_meta["json_path"]
                existing.file_path = cv_meta["file_path"]
                existing.parsed_at = cv_meta["parsed_at"]
                existing.candidat_nom = cv_meta["candidat_nom"]
                existing.candidat_titre = cv_meta["candidat_titre"]
                existing.last_modified = datetime.now()
                print(f"         ✅ Mis à jour: {cv_meta['filename']}")
            else:
                # Insertion
                cv_db = CVMetaDB(
                    filename=cv_meta["filename"],
                    project_id=cv_meta["project_id"],
                    json_path=cv_meta["json_path"],
                    file_path=cv_meta["file_path"],
                    parsed_at=cv_meta["parsed_at"],
                    candidat_nom=cv_meta["candidat_nom"],
                    candidat_titre=cv_meta["candidat_titre"]
                )
                session.add(cv_db)
                print(f"         ✅ Inséré: {cv_meta['filename']}")

            session.commit()
            return True

    except Exception as e:
        print(f"         ❌ Erreur: {e}")
        return False


def clean_orphan_records(cv_files: List[Dict], dry_run: bool = True):
    """
    Supprime les enregistrements cv_meta dont le fichier n'existe plus

    Args:
        cv_files: Liste des CV scannés
        dry_run: Si True, n'applique pas
    """
    if dry_run:
        return

    with get_session() as session:
        # Récupérer tous les CV en DB
        from sqlmodel import select
        all_cv_db = session.exec(select(CVMetaDB)).all()

        # Construire un set des (project_id, filename) existants
        existing_keys = {(cv["project_id"], cv["filename"]) for cv in cv_files}

        # Supprimer les orphelins
        orphan_count = 0
        for cv_db in all_cv_db:
            key = (cv_db.project_id, cv_db.filename)
            if key not in existing_keys:
                session.delete(cv_db)
                orphan_count += 1
                print(f"   ✅ Supprimé orphelin: {cv_db.filename} (projet {cv_db.project_id})")

        if orphan_count > 0:
            session.commit()
            print(f"\n   {orphan_count} enregistrement(s) orphelin(s) supprimé(s)")


def main():
    args = parse_args()
    dry_run = not args.apply

    print("=" * 60)
    print("📇 INDEXATION CV DANS cv_meta")
    print("=" * 60)

    if dry_run:
        print("\n🔍 MODE: DRY-RUN (aucune modification)")
        print("   Pour appliquer: python scripts/migrate_cv_meta.py --apply")
    else:
        print("\n⚠️  MODE: APPLY (modifications réelles)")
        response = input("\n   Continuer? (yes/no): ")
        if response.lower() != "yes":
            print("   Annulé.")
            return

    # Scanner tous les CV
    print("\n📂 Scan des CV parsés...")
    cv_files = scan_parsed_cvs()

    print(f"\n📊 CV parsés trouvés: {len(cv_files)}")

    if not cv_files:
        print("\n✅ Aucun CV à indexer!")
        return

    # Répartition par projet
    projects = {}
    for cv in cv_files:
        project_id = cv["project_id"]
        projects[project_id] = projects.get(project_id, 0) + 1

    print("\n📦 Répartition par projet:")
    for project_id, count in sorted(projects.items()):
        print(f"   • {project_id}: {count} CV")

    # Détecter anomalies
    warnings = detect_anomalies(cv_files)
    if warnings:
        print("\n⚠️  Anomalies détectées:")
        for warning in warnings:
            print(f"   {warning}")

    # Indexer
    if dry_run:
        print("\n[DRY-RUN] Les CV suivants seraient indexés:")
        for cv in cv_files[:5]:  # Montrer les 5 premiers
            print(f"   • {cv['filename']} (projet: {cv['project_id']})")
        if len(cv_files) > 5:
            print(f"   ... et {len(cv_files) - 5} autres")
    else:
        print("\n📥 Indexation en cours...")
        indexed_count = 0
        for cv in cv_files:
            if index_cv(cv, dry_run):
                indexed_count += 1

        # Nettoyer les orphelins
        print("\n🧹 Nettoyage des orphelins...")
        clean_orphan_records(cv_files, dry_run)

    # Résumé
    print("\n" + "=" * 60)
    if dry_run:
        print(f"📊 DRY-RUN TERMINÉ")
        print(f"   {len(cv_files)} CV seraient indexés")
        print(f"   {len(projects)} projet(s) concerné(s)")
        print(f"\n   Pour appliquer: python scripts/migrate_cv_meta.py --apply")
    else:
        print(f"✅ INDEXATION TERMINÉE")
        print(f"   {indexed_count} CV indexés dans cv_meta")
        print(f"   {len(projects)} projet(s) concerné(s)")
    print("=" * 60)


if __name__ == "__main__":
    main()
