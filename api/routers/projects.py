"""
Router Projets - CRUD projets et historique matchings
"""

import sys
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from lib.models import Project
from brainrh.paths import PROJECT_ROOT

# Ajouter le PROJECT_ROOT pour imports
sys.path.insert(0, str(PROJECT_ROOT))

from unified_project_manager import UnifiedProjectManager

router = APIRouter()

# Initialiser unified project manager (singleton)
project_manager = UnifiedProjectManager(enterprises_folder="enterprises")


class ProjectInput(BaseModel):
    """Input pour création/modification de projet"""
    nom: str
    description: Optional[str] = ""
    enterprise_id: Optional[str] = None
    service_demandeur: Optional[str] = None
    responsable_offre: Optional[str] = None
    contact_responsable: Optional[str] = None
    notes: Optional[str] = None
    status: str = "actif"


@router.get("", response_model=List[Project])
async def list_projects(
    enterprise_id: Optional[str] = Query(None, description="Filtrer par entreprise"),
    status: Optional[str] = Query(None, description="Filtrer par status (actif/archive)")
):
    """
    Liste tous les projets

    **Filtres optionnels:**
    - `enterprise_id`: Filtrer par entreprise
    - `status`: Filtrer par status (actif/archive)

    **Retourne:** Liste des projets
    """
    projects_data = project_manager.list_projects(status=status)

    # Filtrer par enterprise_id si fourni
    if enterprise_id:
        projects_data = [p for p in projects_data if p.get("enterprise_id") == enterprise_id]

    # Convertir en modèles Project
    projects = []
    for p in projects_data:
        projects.append(Project(
            id=p["id"],
            nom=p["nom"],
            enterprise_id=p.get("enterprise_id"),
            service_demandeur=p.get("service_demandeur"),
            responsable_offre=p.get("responsable_offre"),
            contact_responsable=p.get("contact_responsable"),
            notes=p.get("notes"),
            created_at=p["created_at"],
            last_modified=p["last_modified"],
            status=p["status"]
        ))

    return projects


@router.post("", response_model=Project, status_code=201)
async def create_project(project: ProjectInput):
    """
    Crée un nouveau projet

    **Body:**
    - `nom`: Nom du projet
    - `description`: Description du projet (optionnel)
    - `enterprise_id`: ID de l'entreprise (optionnel)
    - `status`: Status (actif/archive, default: actif)

    **Retourne:** Projet créé
    """
    try:
        # enterprise_id est requis dans la nouvelle structure
        if not project.enterprise_id:
            raise HTTPException(
                status_code=400,
                detail="enterprise_id est requis"
            )

        projet_data = project_manager.create_project(
            nom=project.nom,
            enterprise_id=project.enterprise_id,
            description=project.description,
            service_demandeur=project.service_demandeur,
            responsable_offre=project.responsable_offre,
            contact_responsable=project.contact_responsable,
            notes=project.notes
        )

        return Project(
            id=projet_data["id"],
            nom=projet_data["nom"],
            enterprise_id=projet_data["enterprise_id"],
            service_demandeur=projet_data.get("service_demandeur"),
            responsable_offre=projet_data.get("responsable_offre"),
            contact_responsable=projet_data.get("contact_responsable"),
            notes=projet_data.get("notes"),
            created_at=projet_data["created_at"],
            last_modified=projet_data["last_modified"],
            status=projet_data["status"]
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la création du projet: {str(e)}"
        )


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """
    Récupère un projet par son ID
    """
    projet_data = project_manager.get_project(project_id)

    if not projet_data:
        raise HTTPException(
            status_code=404,
            detail=f"Projet {project_id} introuvable"
        )

    return Project(
        id=projet_data["id"],
        nom=projet_data["nom"],
        enterprise_id=projet_data.get("enterprise_id"),
        service_demandeur=projet_data.get("service_demandeur"),
        responsable_offre=projet_data.get("responsable_offre"),
        contact_responsable=projet_data.get("contact_responsable"),
        notes=projet_data.get("notes"),
        created_at=projet_data["created_at"],
        last_modified=projet_data["last_modified"],
        status=projet_data["status"]
    )


@router.put("/{project_id}", response_model=Project)
async def update_project(project_id: str, project: ProjectInput):
    """
    Modifie un projet existant
    """
    try:
        updates = {
            "nom": project.nom,
            "status": project.status,
            "description": project.description or "",
            "enterprise_id": project.enterprise_id,
            "service_demandeur": project.service_demandeur or "",
            "responsable_offre": project.responsable_offre or "",
            "contact_responsable": project.contact_responsable or "",
            "notes": project.notes or ""
        }

        project_manager.update_project(project_id, updates)

        projet_data = project_manager.get_project(project_id)

        return Project(
            id=projet_data["id"],
            nom=projet_data["nom"],
            enterprise_id=projet_data.get("enterprise_id"),
            service_demandeur=projet_data.get("service_demandeur"),
            responsable_offre=projet_data.get("responsable_offre"),
            contact_responsable=projet_data.get("contact_responsable"),
            notes=projet_data.get("notes"),
            created_at=projet_data["created_at"],
            last_modified=projet_data["last_modified"],
            status=projet_data["status"]
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la mise à jour du projet: {str(e)}"
        )


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str):
    """
    Archive un projet (soft delete)
    """
    try:
        project_manager.delete_project(project_id)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la suppression du projet: {str(e)}"
        )


@router.get("/{project_id}/matchings/latest")
async def get_latest_matching(project_id: str):
    """
    Récupère le timestamp du dernier matching pour un projet

    **Retourne:**
    ```json
    {
      "timestamp": "2025-10-12_06-49-01"
    }
    ```
    """
    # Vérifier que le projet existe
    if not project_manager.get_project(project_id):
        raise HTTPException(
            status_code=404,
            detail=f"Projet {project_id} introuvable"
        )

    try:
        # Récupérer le chemin du projet
        project_path = project_manager.get_project_path(project_id)

        if not project_path:
            raise HTTPException(
                status_code=404,
                detail=f"Projet {project_id} introuvable"
            )

        matchings_dir = project_path / "matchings"

        if not matchings_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Aucun matching trouvé pour le projet {project_id}"
            )

        # Lister tous les dossiers de matching
        matching_dirs = [d for d in matchings_dir.iterdir() if d.is_dir()]

        if not matching_dirs:
            raise HTTPException(
                status_code=404,
                detail=f"Aucun matching trouvé pour le projet {project_id}"
            )

        # Trier par nom (format YYYY-MM-DD_HH-MM-SS) et prendre le dernier
        latest = sorted(matching_dirs, reverse=True)[0]

        return {
            "timestamp": latest.name
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération du dernier matching: {str(e)}"
        )


@router.get("/{project_id}/history")
async def get_project_history(
    project_id: str,
    limit: int = Query(default=50, ge=1, le=200, description="Nombre max de résultats"),
    offset: int = Query(default=0, ge=0, description="Offset pour pagination")
):
    """
    Récupère l'historique des matchings d'un projet

    **Paramètres:**
    - `limit`: Nombre max de résultats (default: 50)
    - `offset`: Offset pour pagination (default: 0)

    **Retourne:**
    ```json
    {
      "total": 150,
      "items": [
        {
          "matching_id": "2025-10-11_14-30-00",
          "timestamp": "2025-10-11T14:30:00Z",
          "candidats_count": 32
        }
      ]
    }
    ```
    """
    # Vérifier que le projet existe
    if not project_manager.get_project(project_id):
        raise HTTPException(
            status_code=404,
            detail=f"Projet {project_id} introuvable"
        )

    try:
        matchings = project_manager.list_matchings(project_id)

        # Pagination
        total = len(matchings)
        items = matchings[offset:offset + limit]

        return {
            "total": total,
            "items": [
                {
                    "matching_id": m["timestamp"],
                    "timestamp": m["timestamp"],
                    "candidats_count": m["candidats_count"]
                }
                for m in items
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération de l'historique: {str(e)}"
        )
