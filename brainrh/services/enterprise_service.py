"""
EnterpriseService - Gestion des entreprises
Couche service : DB (index) + JSON (données complètes)
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select

from brainrh.database import get_session
from brainrh.models import EnterpriseDB
from brainrh.services.file_storage import FileStorage
from brainrh.paths import get_relative_path, ENTERPRISES_DIR


class EnterpriseService:
    """Service pour gestion des entreprises (DB + JSON)"""

    @staticmethod
    def list_enterprises() -> List[Dict[str, Any]]:
        """
        Liste toutes les entreprises (charge depuis DB puis JSON)

        Returns:
            Liste des entreprises (données complètes depuis JSON)
        """
        enterprises = []

        with get_session() as session:
            db_enterprises = session.exec(select(EnterpriseDB)).all()

            for db_ent in db_enterprises:
                # Charger JSON complet
                try:
                    json_data = FileStorage.load_json(db_ent.json_path)
                    enterprises.append(json_data)
                except FileNotFoundError:
                    # JSON manquant, reconstruire depuis DB
                    enterprises.append({
                        "id": db_ent.id,
                        "nom": db_ent.nom,
                        "secteur": db_ent.secteur,
                        "created_at": db_ent.created_at.isoformat(),
                        "last_modified": db_ent.last_modified.isoformat()
                    })

        return enterprises

    @staticmethod
    def get_enterprise(enterprise_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère une entreprise par ID

        Args:
            enterprise_id: ID entreprise

        Returns:
            Données entreprise (JSON complet) ou None
        """
        with get_session() as session:
            db_ent = session.get(EnterpriseDB, enterprise_id)

            if not db_ent:
                return None

            # Charger JSON complet
            try:
                return FileStorage.load_json(db_ent.json_path)
            except FileNotFoundError:
                # JSON manquant, reconstruire depuis DB
                return {
                    "id": db_ent.id,
                    "nom": db_ent.nom,
                    "secteur": db_ent.secteur,
                    "created_at": db_ent.created_at.isoformat(),
                    "last_modified": db_ent.last_modified.isoformat()
                }

    @staticmethod
    def create_enterprise(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle entreprise (DB + JSON)

        Args:
            data: Données entreprise (id, nom, secteur, etc.)

        Returns:
            Données entreprise créée
        """
        enterprise_id = data["id"]
        now = datetime.now()

        # Préparer données complètes
        full_data = {
            **data,
            "created_at": now.isoformat(),
            "last_modified": now.isoformat()
        }

        # Chemin JSON
        json_path = get_relative_path(ENTERPRISES_DIR / enterprise_id / "enterprise.json")

        # 1. Sauvegarder JSON
        FileStorage.save_json(json_path, full_data)

        # 2. Insérer en DB (index)
        with get_session() as session:
            db_ent = EnterpriseDB(
                id=enterprise_id,
                nom=data["nom"],
                secteur=data.get("secteur"),
                created_at=now,
                last_modified=now,
                json_path=json_path
            )
            session.add(db_ent)
            session.commit()

        return full_data

    @staticmethod
    def update_enterprise(enterprise_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Met à jour une entreprise (DB + JSON)

        Args:
            enterprise_id: ID entreprise
            updates: Champs à mettre à jour

        Returns:
            Données mises à jour ou None si introuvable
        """
        with get_session() as session:
            db_ent = session.get(EnterpriseDB, enterprise_id)

            if not db_ent:
                return None

            # Charger JSON actuel
            try:
                full_data = FileStorage.load_json(db_ent.json_path)
            except FileNotFoundError:
                full_data = {
                    "id": db_ent.id,
                    "nom": db_ent.nom,
                    "secteur": db_ent.secteur
                }

            # Appliquer mises à jour
            full_data.update(updates)
            full_data["last_modified"] = datetime.now().isoformat()

            # 1. Sauvegarder JSON
            FileStorage.save_json(db_ent.json_path, full_data)

            # 2. Mettre à jour DB (index)
            if "nom" in updates:
                db_ent.nom = updates["nom"]
            if "secteur" in updates:
                db_ent.secteur = updates["secteur"]
            db_ent.last_modified = datetime.now()

            session.add(db_ent)
            session.commit()

        return full_data

    @staticmethod
    def delete_enterprise(enterprise_id: str) -> bool:
        """
        Supprime une entreprise (DB + JSON)

        Args:
            enterprise_id: ID entreprise

        Returns:
            True si supprimé, False si introuvable
        """
        with get_session() as session:
            db_ent = session.get(EnterpriseDB, enterprise_id)

            if not db_ent:
                return False

            # 1. Supprimer JSON
            try:
                FileStorage.delete_file(db_ent.json_path)
            except FileNotFoundError:
                pass

            # 2. Supprimer DB
            session.delete(db_ent)
            session.commit()

        return True
