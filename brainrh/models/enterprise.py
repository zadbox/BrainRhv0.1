"""
Modèle Enterprise pour la base de données
Table enterprises = index uniquement, JSON complet dans fichier
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class EnterpriseDB(SQLModel, table=True):
    """
    Table enterprises (INDEX UNIQUEMENT)
    Données complètes dans JSON pointé par json_path
    """
    __tablename__ = "enterprises"

    id: str = Field(primary_key=True, description="ID unique entreprise")
    nom: str = Field(index=True, description="Nom entreprise")
    secteur: Optional[str] = Field(default=None, description="Secteur d'activité")
    created_at: datetime = Field(default_factory=datetime.now, description="Date création")
    last_modified: datetime = Field(default_factory=datetime.now, description="Date modification")
    json_path: str = Field(description="Chemin relatif vers JSON complet")

    class Config:
        extra = "allow"
