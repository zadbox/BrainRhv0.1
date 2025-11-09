#!/usr/bin/env python3
"""
Unified Project Manager - Gestionnaire unifié pour la structure enterprises/{id}/projects/
Remplace project_manager.py avec support complet de la hiérarchie entreprises
IMPORTANT: Synchronise toujours avec la DB via ProjectService
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import uuid

from brainrh.services.project_service import ProjectService


class UnifiedProjectManager:
    """Gestionnaire unifié de projets dans la structure enterprises"""

    def __init__(self, enterprises_folder: str = "enterprises"):
        self.enterprises_folder = Path(enterprises_folder)
        self.project_service = ProjectService()

        # Créer le dossier si nécessaire
        self.enterprises_folder.mkdir(exist_ok=True)

    def _write_atomic(self, file_path: Path, data: Dict):
        """Écrit un fichier JSON de manière atomique"""
        tmp_file = file_path.with_suffix('.tmp')
        with open(tmp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp_file.replace(file_path)

    def _get_projects_folder(self, enterprise_id: str) -> Path:
        """Retourne le chemin du dossier projects pour une entreprise"""
        return self.enterprises_folder / enterprise_id / "projects"

    def _get_project_dir(self, project_id: str, enterprise_id: Optional[str]) -> Path:
        """
        Retourne le chemin du dossier projet

        Args:
            project_id: ID du projet
            enterprise_id: ID de l'entreprise (OBLIGATOIRE)

        Returns:
            Path du dossier projet

        Raises:
            ValueError: Si enterprise_id est None
        """
        if not enterprise_id:
            raise ValueError(f"enterprise_id est requis pour le projet {project_id} - la structure legacy projects/ n'est plus supportée")

        return self._get_projects_folder(enterprise_id) / project_id

    def _get_projects_from_db(self, enterprise_id: str, status: Optional[str] = None) -> List[Dict]:
        """Lit les projets d'une entreprise depuis la DB"""
        from sqlmodel import select
        from brainrh.database import get_session
        from brainrh.models.project import ProjectDB

        with get_session() as session:
            query = select(ProjectDB).where(ProjectDB.enterprise_id == enterprise_id)
            if status:
                query = query.where(ProjectDB.status == status)

            projects = session.exec(query).all()
            return [
                {
                    "id": p.id,
                    "nom": p.nom,
                    "enterprise_id": p.enterprise_id,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "last_modified": p.last_modified.isoformat() if p.last_modified else None,
                    "status": p.status
                }
                for p in projects
            ]

    def list_projects(self, enterprise_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
        """
        Liste tous les projets (optionnellement filtrés)

        Args:
            enterprise_id: Filtrer par entreprise (None = toutes les entreprises)
            status: Filtrer par statut ('actif', 'archive', None=tous)

        Returns:
            Liste de projets [{id, nom, enterprise_id, created_at, status, ...}]
        """
        from sqlmodel import select
        from brainrh.database import get_session
        from brainrh.models.project import ProjectDB

        with get_session() as session:
            query = select(ProjectDB)

            if enterprise_id:
                query = query.where(ProjectDB.enterprise_id == enterprise_id)

            if status:
                query = query.where(ProjectDB.status == status)

            projects = session.exec(query).all()

            all_projects = [
                {
                    "id": p.id,
                    "nom": p.nom,
                    "enterprise_id": p.enterprise_id,
                    "service_demandeur": p.service_demandeur if hasattr(p, 'service_demandeur') else None,
                    "responsable_offre": p.responsable_offre if hasattr(p, 'responsable_offre') else None,
                    "contact_responsable": p.contact_responsable if hasattr(p, 'contact_responsable') else None,
                    "notes": p.notes if hasattr(p, 'notes') else None,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "last_modified": p.last_modified.isoformat() if p.last_modified else None,
                    "status": p.status
                }
                for p in projects
            ]

        # Trier par dernière modification (plus récent en premier)
        all_projects.sort(
            key=lambda p: p.get("last_modified", p.get("created_at", "")),
            reverse=True
        )

        return all_projects

    def get_project(self, project_id: str, enterprise_id: Optional[str] = None) -> Optional[Dict]:
        """
        Récupère les détails d'un projet

        Args:
            project_id: ID du projet
            enterprise_id: ID de l'entreprise (optionnel, cherche dans toutes si None)

        Returns:
            Dictionnaire avec toutes les métadonnées, ou None si non trouvé
        """
        # Si enterprise_id fourni, chercher directement
        if enterprise_id:
            project_dir = self._get_projects_folder(enterprise_id) / project_id
            projet_file = project_dir / "projet.json"

            if projet_file.exists():
                with open(projet_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None

        # Sinon, chercher dans toutes les entreprises
        for enterprise_dir in self.enterprises_folder.iterdir():
            if not enterprise_dir.is_dir() or enterprise_dir.name.startswith('_'):
                continue

            project_dir = enterprise_dir / "projects" / project_id
            projet_file = project_dir / "projet.json"

            if projet_file.exists():
                with open(projet_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # S'assurer que enterprise_id est présent
                    if "enterprise_id" not in data:
                        data["enterprise_id"] = enterprise_dir.name
                    return data

        return None

    def create_project(self, nom: str, enterprise_id: str, description: str = "",
                      service_demandeur: Optional[str] = None, responsable_offre: Optional[str] = None,
                      contact_responsable: Optional[str] = None, notes: Optional[str] = None) -> Dict:
        """
        Crée un nouveau projet

        Args:
            nom: Nom du projet
            enterprise_id: ID de l'entreprise parente
            description: Description optionnelle
            service_demandeur: Service demandeur
            responsable_offre: Responsable de l'offre
            contact_responsable: Contact du responsable
            notes: Notes

        Returns:
            Dictionnaire du projet créé
        """
        # Vérifier que l'entreprise existe
        enterprise_dir = self.enterprises_folder / enterprise_id
        if not enterprise_dir.exists():
            raise ValueError(f"Entreprise {enterprise_id} introuvable")

        # Générer un ID unique basé sur le nom
        project_id = self._generate_project_id(nom)

        # Vérifier que l'ID n'existe pas déjà dans cette entreprise
        if self.get_project(project_id, enterprise_id):
            # Ajouter un suffix unique
            project_id = f"{project_id}-{uuid.uuid4().hex[:6]}"

        # Créer la structure du projet
        projects_folder = self._get_projects_folder(enterprise_id)
        project_dir = projects_folder / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "historique").mkdir(exist_ok=True)
        (project_dir / "matchings").mkdir(exist_ok=True)
        (project_dir / "cvs_raw").mkdir(exist_ok=True)      # CVs bruts (PDF/DOCX)
        (project_dir / "cvs_parsed").mkdir(exist_ok=True)   # CVs parsés (JSON)

        # Métadonnées du projet
        now = datetime.now().isoformat()
        projet_data = {
            "id": project_id,
            "nom": nom,
            "description": description,
            "enterprise_id": enterprise_id,
            "service_demandeur": service_demandeur or "",
            "responsable_offre": responsable_offre or "",
            "contact_responsable": contact_responsable or "",
            "notes": notes or "",
            "created_at": now,
            "last_modified": now,
            "status": "actif",
            "offre_saved": False,
            "matchings_count": 0
        }

        # Sauvegarder le projet (DB + JSON) via ProjectService
        # ProjectService écrit le JSON ET met à jour la DB
        self.project_service.create_project(projet_data)

        return projet_data

    def update_project(self, project_id: str, updates: Dict, enterprise_id: Optional[str] = None):
        """
        Met à jour un projet

        Args:
            project_id: ID du projet
            updates: Dictionnaire des champs à mettre à jour
            enterprise_id: ID de l'entreprise (optionnel)
        """
        # Récupérer le projet
        projet = self.get_project(project_id, enterprise_id)
        if not projet:
            raise ValueError(f"Projet {project_id} introuvable")

        # Déterminer l'enterprise_id
        ent_id = projet.get("enterprise_id") or enterprise_id
        if not ent_id:
            raise ValueError(f"Impossible de déterminer l'enterprise_id pour le projet {project_id}")

        # Mettre à jour via ProjectService (DB + JSON)
        # ProjectService écrit le JSON ET met à jour la DB
        updated = self.project_service.update_project(project_id, updates)

        if not updated:
            raise ValueError(f"Échec de la mise à jour du projet {project_id}")

        return updated

    def delete_project(self, project_id: str, enterprise_id: Optional[str] = None):
        """
        Archive un projet (soft delete)

        Args:
            project_id: ID du projet
            enterprise_id: ID de l'entreprise (optionnel)
        """
        self.update_project(project_id, {"status": "archive"}, enterprise_id)

    def save_offer(self, project_id: str, offre_data: Dict, enterprise_id: Optional[str] = None):
        """
        Sauvegarde l'offre parsée dans le projet

        Args:
            project_id: ID du projet
            offre_data: Données de l'offre parsée
            enterprise_id: ID de l'entreprise (optionnel)
        """
        projet = self.get_project(project_id, enterprise_id)
        if not projet:
            raise ValueError(f"Projet {project_id} introuvable")

        ent_id = projet.get("enterprise_id") or enterprise_id
        project_dir = self._get_project_dir(project_id, ent_id)
        offre_file = project_dir / "offre_parsed.json"

        self._write_atomic(offre_file, offre_data)

        # Mettre à jour le projet
        self.update_project(project_id, {"offre_saved": True}, ent_id)

    def load_offer(self, project_id: str, enterprise_id: Optional[str] = None) -> Optional[Dict]:
        """
        Charge l'offre parsée du projet

        Args:
            project_id: ID du projet
            enterprise_id: ID de l'entreprise (optionnel)

        Returns:
            Données de l'offre, ou None si pas trouvée
        """
        projet = self.get_project(project_id, enterprise_id)
        if not projet:
            return None

        ent_id = projet.get("enterprise_id") or enterprise_id
        project_dir = self._get_project_dir(project_id, ent_id)
        offre_file = project_dir / "offre_parsed.json"

        if not offre_file.exists():
            return None

        with open(offre_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_matching_result(self, project_id: str, results: Dict,
                            timestamp: Optional[str] = None,
                            enterprise_id: Optional[str] = None) -> str:
        """
        Sauvegarde les résultats d'un matching

        Args:
            project_id: ID du projet
            results: Résultats du matching (scorecard)
            timestamp: Timestamp optionnel (auto si None)
            enterprise_id: ID de l'entreprise (optionnel)

        Returns:
            Timestamp du matching sauvegardé
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        projet = self.get_project(project_id, enterprise_id)
        if not projet:
            raise ValueError(f"Projet {project_id} introuvable")

        ent_id = projet.get("enterprise_id") or enterprise_id
        project_dir = self._get_project_dir(project_id, ent_id)
        matchings_dir = project_dir / "matchings"
        matching_folder = matchings_dir / timestamp
        matching_folder.mkdir(parents=True, exist_ok=True)

        # Sauvegarder JSON
        result_file = matching_folder / "results.json"
        self._write_atomic(result_file, results)

        # Incrémenter le compteur
        matchings_count = projet.get("matchings_count", 0) + 1
        self.update_project(project_id, {
            "matchings_count": matchings_count,
            "last_matching": timestamp
        }, ent_id)

        return timestamp

    def list_matchings(self, project_id: str, enterprise_id: Optional[str] = None) -> List[Dict]:
        """
        Liste l'historique des matchings d'un projet

        Args:
            project_id: ID du projet
            enterprise_id: ID de l'entreprise (optionnel)

        Returns:
            Liste des matchings [{timestamp, candidats_count, ...}]
        """
        projet = self.get_project(project_id, enterprise_id)
        if not projet:
            return []

        ent_id = projet.get("enterprise_id") or enterprise_id
        project_dir = self._get_project_dir(project_id, ent_id)
        matchings = []

        # Lire les nouveaux matchings (dossier matchings/)
        matchings_dir = project_dir / "matchings"
        if matchings_dir.exists():
            for matching_folder in sorted(matchings_dir.iterdir(), reverse=True):
                if not matching_folder.is_dir():
                    continue

                timestamp = matching_folder.name
                results_file = matching_folder / "results.json"

                if results_file.exists():
                    try:
                        with open(results_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        # Récupérer le nombre de candidats depuis metadata ou results
                        candidats_count = 0
                        if "metadata" in data:
                            candidats_count = data["metadata"].get("top_reranked", 0)
                        elif "results" in data:
                            candidats_count = len(data.get("results", []))

                        matchings.append({
                            "timestamp": timestamp,
                            "candidats_count": candidats_count,
                            "file_path": str(results_file)
                        })
                    except Exception as e:
                        print(f"Erreur lecture {results_file}: {e}")

        # Lire les anciens matchings (dossier historique/)
        historique_dir = project_dir / "historique"
        if historique_dir.exists():
            for file in sorted(historique_dir.glob("*.json"), reverse=True):
                timestamp = file.stem

                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # Compter les candidats
                    candidats_count = 0
                    if "reranked_cvs" in data:
                        reranked = data["reranked_cvs"]
                        if isinstance(reranked, list):
                            candidats_count = len(reranked)
                        elif isinstance(reranked, dict):
                            candidats_count = len(reranked.get("ranked_cvs", []))
                    elif "scored_cvs" in data:
                        candidats_count = len(data.get("scored_cvs", []))

                    matchings.append({
                        "timestamp": timestamp,
                        "candidats_count": candidats_count,
                        "file_path": str(file)
                    })
                except Exception as e:
                    print(f"Erreur lecture {file}: {e}")

        # Trier par timestamp (plus récent en premier)
        matchings.sort(key=lambda m: m["timestamp"], reverse=True)

        return matchings

    def load_matching(self, project_id: str, timestamp: str,
                     enterprise_id: Optional[str] = None) -> Optional[Dict]:
        """
        Charge un matching spécifique

        Args:
            project_id: ID du projet
            timestamp: Timestamp du matching
            enterprise_id: ID de l'entreprise (optionnel)

        Returns:
            Résultats du matching, ou None
        """
        projet = self.get_project(project_id, enterprise_id)
        if not projet:
            return None

        ent_id = projet.get("enterprise_id") or enterprise_id
        project_dir = self._get_project_dir(project_id, ent_id)

        if not project_dir.exists():
            return None

        # Essayer nouveau format d'abord (matchings/)
        new_result_file = project_dir / "matchings" / timestamp / "results.json"
        if new_result_file.exists():
            with open(new_result_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        # Essayer ancien format (historique/)
        old_result_file = project_dir / "historique" / f"{timestamp}.json"
        if old_result_file.exists():
            with open(old_result_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        return None

    def get_project_path(self, project_id: str, enterprise_id: Optional[str] = None) -> Optional[Path]:
        """
        Retourne le chemin du dossier projet

        Args:
            project_id: ID du projet
            enterprise_id: ID de l'entreprise (optionnel)

        Returns:
            Path du dossier projet, ou None
        """
        projet = self.get_project(project_id, enterprise_id)
        if not projet:
            return None

        ent_id = projet.get("enterprise_id") or enterprise_id
        return self._get_project_dir(project_id, ent_id)

    # Méthodes privées

    def _generate_project_id(self, nom: str) -> str:
        """Génère un ID projet à partir du nom"""
        import re
        slug = nom.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = slug.strip('-')[:50]
        return slug or "projet"
