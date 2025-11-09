#!/usr/bin/env python3
"""
Gestionnaire de projets de recrutement
Gère la création, lecture, mise à jour des projets multi-recrutement
Délègue au service ProjectService pour la persistance DB+JSON
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import uuid

from brainrh.services.project_service import ProjectService


class ProjectManager:
    """Gestionnaire de projets de recrutement (wrapper autour de ProjectService)"""

    def __init__(self, projects_folder: str = "projects"):
        self.projects_folder = Path(projects_folder)
        self.service = ProjectService()

    def list_projects(self, status: Optional[str] = None, enterprise_id: Optional[str] = None) -> List[Dict]:
        """
        Liste tous les projets

        Args:
            status: Filtrer par statut ('actif', 'archive', None=tous)
            enterprise_id: Filtrer par entreprise (optionnel)

        Returns:
            Liste de projets [{id, nom, created_at, status, ...}]
        """
        # Charger depuis le service (DB → JSON)
        projects = self.service.list_projects(enterprise_id=enterprise_id, status=status)

        # Trier par dernière modification (plus récent en premier)
        projects.sort(key=lambda p: p.get("last_modified", p.get("created_at", "")), reverse=True)

        return projects

    def get_project(self, project_id: str) -> Optional[Dict]:
        """
        Récupère les détails d'un projet

        Args:
            project_id: ID du projet

        Returns:
            Dictionnaire avec toutes les métadonnées, ou None si non trouvé
        """
        # Charger depuis le service (DB → JSON)
        return self.service.get_project(project_id)

    def create_project(self, nom: str, description: str = "", enterprise_id: Optional[str] = None) -> Dict:
        """
        Crée un nouveau projet

        Args:
            nom: Nom du projet
            description: Description optionnelle
            enterprise_id: ID entreprise (optionnel, pour projets enterprise)

        Returns:
            Dictionnaire du projet créé
        """
        # Générer un ID unique basé sur le nom
        project_id = self._generate_project_id(nom)

        # Vérifier que l'ID n'existe pas déjà
        if self.service.get_project(project_id):
            # Ajouter un suffix unique
            project_id = f"{project_id}-{uuid.uuid4().hex[:6]}"

        # Créer la structure du projet (historique/)
        if enterprise_id:
            project_dir = Path("enterprises") / enterprise_id / "projects" / project_id
        else:
            project_dir = self.projects_folder / project_id

        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "historique").mkdir(exist_ok=True)

        # Métadonnées du projet
        projet_data = {
            "id": project_id,
            "nom": nom,
            "description": description,
            "enterprise_id": enterprise_id,
            "status": "actif",
            "offre_saved": False,
            "matchings_count": 0
        }

        # Créer via le service (DB + JSON)
        projet = self.service.create_project(projet_data)

        return projet

    def update_project(self, project_id: str, updates: Dict):
        """
        Met à jour un projet

        Args:
            project_id: ID du projet
            updates: Dictionnaire des champs à mettre à jour
        """
        # Mettre à jour via le service (DB + JSON)
        result = self.service.update_project(project_id, updates)
        if not result:
            raise ValueError(f"Projet {project_id} introuvable")

    def delete_project(self, project_id: str):
        """
        Archive un projet (ne supprime pas physiquement)

        Args:
            project_id: ID du projet
        """
        # Archiver via update
        self.update_project(project_id, {"status": "archive"})

    def save_offer(self, project_id: str, offre_data: Dict):
        """
        Sauvegarde l'offre parsée dans le projet

        Args:
            project_id: ID du projet
            offre_data: Données de l'offre parsée
        """
        project_dir = self.get_project_path(project_id)
        if not project_dir:
            raise ValueError(f"Projet {project_id} introuvable")

        offre_file = project_dir / "offre_parsed.json"

        with open(offre_file, 'w', encoding='utf-8') as f:
            json.dump(offre_data, f, ensure_ascii=False, indent=2)

        # Mettre à jour le projet
        self.update_project(project_id, {"offre_saved": True})

    def load_offer(self, project_id: str) -> Optional[Dict]:
        """
        Charge l'offre parsée du projet

        Args:
            project_id: ID du projet

        Returns:
            Données de l'offre, ou None si pas trouvée
        """
        project_dir = self.get_project_path(project_id)
        if not project_dir:
            return None

        offre_file = project_dir / "offre_parsed.json"

        if not offre_file.exists():
            return None

        with open(offre_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_matching_result(self, project_id: str, results: Dict, timestamp: Optional[str] = None) -> str:
        """
        Sauvegarde les résultats d'un matching

        Args:
            project_id: ID du projet
            results: Résultats du matching (scorecard)
            timestamp: Timestamp optionnel (auto si None)

        Returns:
            Timestamp du matching sauvegardé
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Utiliser get_project_path pour gérer projects/ et enterprises/*/projects/
        project_dir = self.get_project_path(project_id)
        if not project_dir:
            raise ValueError(f"Projet {project_id} introuvable")

        historique_dir = project_dir / "historique"
        historique_dir.mkdir(exist_ok=True)

        # Sauvegarder JSON
        result_file = historique_dir / f"{timestamp}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # Incrémenter le compteur
        projet = self.get_project(project_id)
        matchings_count = projet.get("matchings_count", 0) + 1
        self.update_project(project_id, {
            "matchings_count": matchings_count,
            "last_matching": timestamp
        })

        return timestamp

    def list_matchings(self, project_id: str) -> List[Dict]:
        """
        Liste l'historique des matchings d'un projet

        Args:
            project_id: ID du projet

        Returns:
            Liste des matchings [{timestamp, candidats_count, ...}]
        """
        # Utiliser get_project_path pour gérer projects/ et enterprises/*/projects/
        project_dir = self.get_project_path(project_id)
        if not project_dir:
            return []

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

                    # Compter les candidats: priorité reranked_cvs > scored_cvs
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

    def load_matching(self, project_id: str, timestamp: str) -> Optional[Dict]:
        """
        Charge un matching spécifique

        Args:
            project_id: ID du projet
            timestamp: Timestamp du matching

        Returns:
            Résultats du matching, ou None
        """
        # Utiliser get_project_path pour gérer projects/ et enterprises/*/projects/
        project_dir = self.get_project_path(project_id)
        if not project_dir:
            return None

        result_file = project_dir / "historique" / f"{timestamp}.json"

        if not result_file.exists():
            return None

        with open(result_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_project_path(self, project_id: str) -> Optional[Path]:
        """
        Retourne le chemin du dossier projet
        Cherche d'abord dans projects/, puis dans enterprises/*/projects/
        """
        # Chercher dans projects/ (ancien système)
        project_path = self.projects_folder / project_id
        if project_path.exists():
            return project_path

        # Chercher dans enterprises/*/projects/ (nouveau système)
        enterprises_folder = Path("enterprises")
        if enterprises_folder.exists():
            for enterprise_dir in enterprises_folder.iterdir():
                if not enterprise_dir.is_dir():
                    continue

                enterprise_project_path = enterprise_dir / "projects" / project_id
                if enterprise_project_path.exists():
                    return enterprise_project_path

        # Projet non trouvé
        return None

    # Méthodes privées

    def _generate_project_id(self, nom: str) -> str:
        """Génère un ID projet à partir du nom"""
        import re
        # Normaliser: minuscules, espaces -> tirets, garder alphanum
        slug = nom.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = slug.strip('-')[:50]  # Max 50 chars
        return slug or "projet"
