# -*- coding: utf-8 -*-
"""
Schemas Pydantic pour les réponses API
Compatible avec les modèles Pydantic existants (lib/models.py)
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ==================== ENTREPRISE ====================

class EnterpriseResponse(BaseModel):
    """Réponse API pour une entreprise"""
    id: str
    nom: str
    secteur: Optional[str] = None
    created_at: datetime
    last_modified: datetime
    projects_count: int = 0

    class Config:
        from_attributes = True  # Permet la conversion depuis SQLModel


class EnterpriseListResponse(BaseModel):
    """Réponse API pour une liste d'entreprises"""
    items: List[EnterpriseResponse]
    total: int
    skip: int
    limit: int


# ==================== PROJET ====================

class ProjectResponse(BaseModel):
    """Réponse API pour un projet"""
    id: str
    nom: str
    enterprise_id: Optional[str] = None
    status: str
    created_at: datetime
    last_modified: datetime

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Réponse API pour une liste de projets"""
    items: List[ProjectResponse]
    total: int
    skip: int
    limit: int


# ==================== CV ====================

class CVMetaResponse(BaseModel):
    """Réponse API pour les métadonnées d'un CV"""
    id: str
    filename: str
    project_id: str
    nom_candidat: Optional[str] = None
    email_candidat: Optional[str] = None
    titre_candidat: Optional[str] = None
    score_final: Optional[float] = None
    created_at: datetime
    last_modified: datetime

    class Config:
        from_attributes = True


class CVMetaListResponse(BaseModel):
    """Réponse API pour une liste de CVs"""
    items: List[CVMetaResponse]
    total: int
    skip: int
    limit: int


# ==================== CRÉATION ====================

class CreateEnterpriseRequest(BaseModel):
    """Requête pour créer une entreprise"""
    id: str = Field(description="ID unique de l'entreprise")
    nom: str = Field(description="Nom de l'entreprise")
    secteur: Optional[str] = Field(None, description="Secteur d'activité")


class CreateProjectRequest(BaseModel):
    """Requête pour créer un projet"""
    id: str = Field(description="ID unique du projet")
    nom: str = Field(description="Nom du projet")
    enterprise_id: Optional[str] = Field(None, description="ID de l'entreprise parente")
    status: str = Field(default="actif", description="Statut du projet")


class CreateCVRequest(BaseModel):
    """Requête pour ajouter un CV"""
    id: str = Field(description="ID unique du CV")
    filename: str = Field(description="Nom du fichier CV")
    nom_candidat: Optional[str] = Field(None, description="Nom du candidat")
    email_candidat: Optional[str] = Field(None, description="Email du candidat")
    titre_candidat: Optional[str] = Field(None, description="Titre professionnel")
    score_final: Optional[float] = Field(None, description="Score de matching")


# ==================== MISE À JOUR ====================

class UpdateEnterpriseRequest(BaseModel):
    """Requête pour mettre à jour une entreprise"""
    nom: Optional[str] = Field(None, description="Nouveau nom")
    secteur: Optional[str] = Field(None, description="Nouveau secteur")


class UpdateProjectRequest(BaseModel):
    """Requête pour mettre à jour un projet"""
    nom: Optional[str] = Field(None, description="Nouveau nom")
    status: Optional[str] = Field(None, description="Nouveau statut")


class UpdateCVRequest(BaseModel):
    """Requête pour mettre à jour un CV"""
    nom_candidat: Optional[str] = Field(None, description="Nom du candidat")
    email_candidat: Optional[str] = Field(None, description="Email du candidat")
    titre_candidat: Optional[str] = Field(None, description="Titre professionnel")
    score_final: Optional[float] = Field(None, description="Score de matching")
