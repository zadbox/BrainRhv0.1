"""
Router Entreprises - CRUD entreprises clientes
"""

import sys
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from lib.models import Enterprise
from brainrh.paths import PROJECT_ROOT

# Ajouter le PROJECT_ROOT pour imports
sys.path.insert(0, str(PROJECT_ROOT))

from enterprise_manager import EnterpriseManager

router = APIRouter()

# Initialiser enterprise manager (singleton)
enterprise_manager = EnterpriseManager(enterprises_folder="enterprises")


class ContactInput(BaseModel):
    """Contact d'une entreprise"""
    nom_complet: str
    poste: Optional[str] = None
    email: str
    telephone: Optional[str] = None
    canal_prefere: Optional[str] = None  # email, telephone, slack, autre
    notes: Optional[str] = None


class EnterpriseInput(BaseModel):
    """Input pour création/modification d'entreprise"""
    nom: str
    site_web: Optional[str] = None
    secteur: Optional[str] = None
    notes: Optional[str] = None
    contacts: List[ContactInput] = []


@router.get("", response_model=List[Enterprise])
async def list_enterprises():
    """
    Liste toutes les entreprises

    **Retourne:** Liste des entreprises
    """
    enterprises_data = enterprise_manager.list_enterprises()

    # Convertir en modèles Enterprise
    enterprises = []
    for e in enterprises_data:
        enterprises.append(Enterprise(
            id=e["id"],
            nom=e["nom"],
            secteur=e.get("secteur", ""),
            created_at=e.get("created_at"),
            last_modified=e.get("last_modified"),
            projects_count=e.get("projects_count", 0)
        ))

    return enterprises


@router.post("", response_model=Enterprise, status_code=201)
async def create_enterprise(enterprise: EnterpriseInput):
    """
    Crée une nouvelle entreprise

    **Body:**
    - `nom`: Nom de l'entreprise (obligatoire)
    - `site_web`: Site web (optionnel)
    - `secteur`: Secteur d'activité (optionnel)
    - `notes`: Notes (optionnel)
    - `contacts`: Liste des contacts (optionnel)

    **Retourne:** Entreprise créée
    """
    try:
        # Convertir les contacts en dict
        contacts_data = [contact.model_dump() for contact in enterprise.contacts]

        enterprise_data = enterprise_manager.create_enterprise(
            nom=enterprise.nom,
            site_web=enterprise.site_web or "",
            secteur=enterprise.secteur or "",
            notes=enterprise.notes or "",
            contacts=contacts_data
        )

        return Enterprise(
            id=enterprise_data["id"],
            nom=enterprise_data["nom"],
            site_web=enterprise_data.get("site_web", ""),
            secteur=enterprise_data.get("secteur", ""),
            notes=enterprise_data.get("notes", ""),
            contacts=enterprise_data.get("contacts", []),
            created_at=enterprise_data.get("created_at"),
            last_modified=enterprise_data.get("last_modified"),
            projects_count=0
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la création de l'entreprise: {str(e)}"
        )


@router.get("/{enterprise_id}", response_model=Enterprise)
async def get_enterprise(enterprise_id: str):
    """
    Récupère une entreprise par son ID
    """
    enterprise_data = enterprise_manager.get_enterprise(enterprise_id)

    if not enterprise_data:
        raise HTTPException(
            status_code=404,
            detail=f"Entreprise {enterprise_id} introuvable"
        )

    return Enterprise(
        id=enterprise_data["id"],
        nom=enterprise_data["nom"],
        site_web=enterprise_data.get("site_web", ""),
        secteur=enterprise_data.get("secteur", ""),
        notes=enterprise_data.get("notes", ""),
        contacts=enterprise_data.get("contacts", []),
        created_at=enterprise_data.get("created_at"),
        last_modified=enterprise_data.get("last_modified"),
        projects_count=enterprise_data.get("projects_count", 0)
    )


@router.put("/{enterprise_id}", response_model=Enterprise)
async def update_enterprise(enterprise_id: str, enterprise: EnterpriseInput):
    """
    Modifie une entreprise existante
    """
    try:
        # Convertir les contacts en dict
        contacts_data = [contact.model_dump() for contact in enterprise.contacts]

        updates = {
            "nom": enterprise.nom,
            "site_web": enterprise.site_web or "",
            "secteur": enterprise.secteur or "",
            "notes": enterprise.notes or "",
            "contacts": contacts_data
        }

        success = enterprise_manager.update_enterprise(enterprise_id, updates)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Entreprise {enterprise_id} introuvable"
            )

        enterprise_data = enterprise_manager.get_enterprise(enterprise_id)

        return Enterprise(
            id=enterprise_data["id"],
            nom=enterprise_data["nom"],
            site_web=enterprise_data.get("site_web", ""),
            secteur=enterprise_data.get("secteur", ""),
            notes=enterprise_data.get("notes", ""),
            contacts=enterprise_data.get("contacts", []),
            created_at=enterprise_data.get("created_at"),
            last_modified=enterprise_data.get("last_modified"),
            projects_count=enterprise_data.get("projects_count", 0)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la mise à jour de l'entreprise: {str(e)}"
        )


@router.delete("/{enterprise_id}", status_code=204)
async def delete_enterprise(enterprise_id: str):
    """
    Supprime une entreprise et tous ses projets
    """
    try:
        success = enterprise_manager.delete_enterprise(enterprise_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Entreprise {enterprise_id} introuvable"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la suppression de l'entreprise: {str(e)}"
        )
