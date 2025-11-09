"""
ProjectService - Gestion des projets
Couche service : DB (index) + JSON (données complètes)
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select

from brainrh.database import get_session
from brainrh.models import ProjectDB
from brainrh.services.file_storage import FileStorage
from brainrh.paths import get_relative_path, ENTERPRISES_DIR


class ProjectService:
    """Service pour gestion des projets (DB + JSON)"""

    @staticmethod
    def list_projects(enterprise_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Liste tous les projets (filtrables)

        Args:
            enterprise_id: Filtrer par entreprise (optionnel)
            status: Filtrer par statut (optionnel)

        Returns:
            Liste des projets (données complètes depuis JSON)
        """
        projects = []

        with get_session() as session:
            query = select(ProjectDB)

            if enterprise_id:
                query = query.where(ProjectDB.enterprise_id == enterprise_id)

            if status:
                query = query.where(ProjectDB.status == status)

            db_projects = session.exec(query).all()

            for db_proj in db_projects:
                try:
                    json_data = FileStorage.load_json(db_proj.json_path)
                    projects.append(json_data)
                except FileNotFoundError:
                    # JSON manquant, reconstruire depuis DB
                    projects.append({
                        "id": db_proj.id,
                        "nom": db_proj.nom,
                        "enterprise_id": db_proj.enterprise_id,
                        "description": db_proj.description,
                        "status": db_proj.status,
                        "created_at": db_proj.created_at.isoformat(),
                        "last_modified": db_proj.last_modified.isoformat()
                    })

        return projects

    @staticmethod
    def get_project(project_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un projet par ID

        Args:
            project_id: ID projet

        Returns:
            Données projet (JSON complet) ou None
        """
        with get_session() as session:
            db_proj = session.get(ProjectDB, project_id)

            if not db_proj:
                return None

            try:
                return FileStorage.load_json(db_proj.json_path)
            except FileNotFoundError:
                return {
                    "id": db_proj.id,
                    "nom": db_proj.nom,
                    "enterprise_id": db_proj.enterprise_id,
                    "description": db_proj.description,
                    "status": db_proj.status,
                    "created_at": db_proj.created_at.isoformat(),
                    "last_modified": db_proj.last_modified.isoformat()
                }

    @staticmethod
    def create_project(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouveau projet (DB + JSON)

        Args:
            data: Données projet (id, nom, enterprise_id, etc.)

        Returns:
            Données projet créé
        """
        project_id = data["id"]
        enterprise_id = data.get("enterprise_id")
        now = datetime.now()

        full_data = {
            **data,
            "created_at": now.isoformat(),
            "last_modified": now.isoformat(),
            "status": data.get("status", "actif")
        }

        # enterprise_id est OBLIGATOIRE (plus de fallback projects/)
        if not enterprise_id:
            raise ValueError("enterprise_id est requis - la structure legacy projects/ n'est plus supportée")

        json_path = get_relative_path(ENTERPRISES_DIR / enterprise_id / "projects" / project_id / "projet.json")

        # 1. Sauvegarder JSON
        FileStorage.save_json(json_path, full_data)

        # 2. Insérer en DB
        with get_session() as session:
            db_proj = ProjectDB(
                id=project_id,
                nom=data["nom"],
                enterprise_id=enterprise_id,
                description=data.get("description"),
                service_demandeur=data.get("service_demandeur"),
                responsable_offre=data.get("responsable_offre"),
                contact_responsable=data.get("contact_responsable"),
                notes=data.get("notes"),
                status=data.get("status", "actif"),
                created_at=now,
                last_modified=now,
                json_path=json_path
            )
            session.add(db_proj)
            session.commit()

        return full_data

    @staticmethod
    def update_project(project_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Met à jour un projet (DB + JSON)

        Args:
            project_id: ID projet
            updates: Champs à mettre à jour

        Returns:
            Données mises à jour ou None si introuvable
        """
        with get_session() as session:
            db_proj = session.get(ProjectDB, project_id)

            if not db_proj:
                return None

            try:
                full_data = FileStorage.load_json(db_proj.json_path)
            except FileNotFoundError:
                full_data = {
                    "id": db_proj.id,
                    "nom": db_proj.nom,
                    "enterprise_id": db_proj.enterprise_id
                }

            # Appliquer MAJ
            full_data.update(updates)
            full_data["last_modified"] = datetime.now().isoformat()

            # 1. Sauvegarder JSON
            FileStorage.save_json(db_proj.json_path, full_data)

            # 2. MAJ DB
            if "nom" in updates:
                db_proj.nom = updates["nom"]
            if "description" in updates:
                db_proj.description = updates["description"]
            if "service_demandeur" in updates:
                db_proj.service_demandeur = updates["service_demandeur"]
            if "responsable_offre" in updates:
                db_proj.responsable_offre = updates["responsable_offre"]
            if "contact_responsable" in updates:
                db_proj.contact_responsable = updates["contact_responsable"]
            if "notes" in updates:
                db_proj.notes = updates["notes"]
            if "status" in updates:
                db_proj.status = updates["status"]
            db_proj.last_modified = datetime.now()

            session.add(db_proj)
            session.commit()

        return full_data

    @staticmethod
    def delete_project(project_id: str) -> bool:
        """
        Supprime un projet (DB + JSON)

        Args:
            project_id: ID projet

        Returns:
            True si supprimé, False si introuvable
        """
        with get_session() as session:
            db_proj = session.get(ProjectDB, project_id)

            if not db_proj:
                return False

            try:
                FileStorage.delete_file(db_proj.json_path)
            except FileNotFoundError:
                pass

            session.delete(db_proj)
            session.commit()

        return True
