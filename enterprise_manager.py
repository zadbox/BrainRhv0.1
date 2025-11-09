#!/usr/bin/env python3
"""
Gestionnaire d'entreprises clientes
Gère la création, lecture, mise à jour des entreprises
Délègue au service EnterpriseService pour la persistance DB+JSON
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import re

from brainrh.services.enterprise_service import EnterpriseService


class EnterpriseManager:
    """Gestionnaire d'entreprises clientes (wrapper autour d'EnterpriseService)"""

    def __init__(self, enterprises_folder: str = "enterprises"):
        self.enterprises_folder = Path(enterprises_folder)
        self.service = EnterpriseService()

    def _generate_enterprise_id(self, nom: str) -> str:
        """Génère un ID unique à partir du nom"""
        # Nettoyer le nom: minuscules, remplacer espaces par tirets
        id_base = re.sub(r'[^\w\s-]', '', nom.lower())
        id_base = re.sub(r'[-\s]+', '-', id_base).strip('-')
        return id_base

    def list_enterprises(self) -> List[Dict]:
        """
        Liste toutes les entreprises

        Returns:
            Liste d'entreprises [{id, nom, secteur, logo, created_at, ...}]
        """
        # Charger depuis le service (DB → JSON)
        enterprises = self.service.list_enterprises()

        # Recalculer le nombre de projets pour chaque entreprise via DB
        from sqlmodel import select
        from brainrh.database import get_session
        from brainrh.models.project import ProjectDB

        with get_session() as session:
            for enterprise in enterprises:
                count = session.exec(
                    select(ProjectDB).where(ProjectDB.enterprise_id == enterprise["id"])
                ).all()
                enterprise["projects_count"] = len([p for p in count if p.status == "actif"])

        # Trier par dernière modification (plus récent en premier)
        enterprises.sort(key=lambda e: e.get("last_modified", e.get("created_at", "")), reverse=True)

        return enterprises

    def get_enterprise(self, enterprise_id: str) -> Optional[Dict]:
        """
        Récupère les détails d'une entreprise

        Args:
            enterprise_id: ID de l'entreprise

        Returns:
            Dictionnaire avec toutes les métadonnées, ou None si non trouvé
        """
        # Charger depuis le service (DB → JSON)
        enterprise = self.service.get_enterprise(enterprise_id)

        if not enterprise:
            return None

        # Recalculer le nombre de projets via DB
        from sqlmodel import select
        from brainrh.database import get_session
        from brainrh.models.project import ProjectDB

        with get_session() as session:
            count = session.exec(
                select(ProjectDB).where(ProjectDB.enterprise_id == enterprise_id)
            ).all()
            enterprise["projects_count"] = len([p for p in count if p.status == "actif"])

        return enterprise

    def create_enterprise(self, nom: str, site_web: str = "", secteur: str = "", notes: str = "", contacts: List[Dict] = None, logo_path: str = "") -> Dict:
        """
        Crée une nouvelle entreprise

        Args:
            nom: Nom de l'entreprise
            site_web: Site web
            secteur: Secteur d'activité
            notes: Notes
            contacts: Liste des contacts
            logo_path: Chemin vers le logo (optionnel)

        Returns:
            Dictionnaire de l'entreprise créée
        """
        if contacts is None:
            contacts = []

        # Générer un ID unique basé sur le nom
        enterprise_id = self._generate_enterprise_id(nom)

        # Vérifier que l'ID n'existe pas déjà
        if self.service.get_enterprise(enterprise_id):
            # Ajouter un suffix unique
            import uuid
            enterprise_id = f"{enterprise_id}-{uuid.uuid4().hex[:6]}"

        # Créer le dossier projects pour cette entreprise
        projects_dir = self.enterprises_folder / enterprise_id / "projects"
        projects_dir.mkdir(parents=True, exist_ok=True)

        # Préparer les données
        data = {
            "id": enterprise_id,
            "nom": nom,
            "site_web": site_web,
            "secteur": secteur,
            "notes": notes,
            "contacts": contacts,
            "logo": logo_path,
            "projects_count": 0
        }

        # Créer via le service (DB + JSON)
        enterprise = self.service.create_enterprise(data)

        return enterprise

    def update_enterprise(self, enterprise_id: str, updates: Dict) -> bool:
        """
        Met à jour une entreprise

        Args:
            enterprise_id: ID de l'entreprise
            updates: Dictionnaire des champs à mettre à jour

        Returns:
            True si succès, False sinon
        """
        # Mettre à jour via le service (DB + JSON)
        result = self.service.update_enterprise(enterprise_id, updates)
        return result is not None

    def delete_enterprise(self, enterprise_id: str) -> bool:
        """
        Supprime une entreprise et tous ses projets

        Args:
            enterprise_id: ID de l'entreprise

        Returns:
            True si succès, False sinon
        """
        # Supprimer via le service (DB + JSON)
        success = self.service.delete_enterprise(enterprise_id)

        if success:
            # Supprimer le dossier projects associé
            enterprise_dir = self.enterprises_folder / enterprise_id
            if enterprise_dir.exists():
                import shutil
                shutil.rmtree(enterprise_dir)

        return success

    def get_projects_folder(self, enterprise_id: str) -> Optional[Path]:
        """
        Retourne le chemin du dossier projects pour une entreprise

        Args:
            enterprise_id: ID de l'entreprise

        Returns:
            Path du dossier projects, ou None si l'entreprise n'existe pas
        """
        enterprise_dir = self.enterprises_folder / enterprise_id
        if not enterprise_dir.exists():
            return None

        projects_dir = enterprise_dir / "projects"
        projects_dir.mkdir(exist_ok=True)
        return projects_dir

    def update_projects_count(self, enterprise_id: str):
        """
        Met à jour le compteur de projets pour une entreprise

        Args:
            enterprise_id: ID de l'entreprise
        """
        # Compter les projets via DB
        from sqlmodel import select
        from brainrh.database import get_session
        from brainrh.models.project import ProjectDB

        with get_session() as session:
            count = session.exec(
                select(ProjectDB).where(ProjectDB.enterprise_id == enterprise_id)
            ).all()
            projects_count = len([p for p in count if p.status == "actif"])

        # Mettre à jour l'entreprise
        self.update_enterprise(enterprise_id, {"projects_count": projects_count})
