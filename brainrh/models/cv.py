"""
Modèle CV Meta pour la base de données (OPTIONNEL)
Table cv_meta = index uniquement, JSON complet dans fichier
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class CVMetaDB(SQLModel, table=True):
    """
    Table cv_meta (INDEX UNIQUEMENT - OPTIONNEL)
    Permet recherche rapide des CVs parsés
    Données complètes dans JSON pointé par json_path
    """
    __tablename__ = "cv_meta"

    filename: str = Field(primary_key=True, description="Nom fichier CV")
    project_id: str = Field(
        primary_key=True,
        foreign_key="projects.id",
        index=True,
        description="ID projet associé"
    )
    parsed_at: Optional[datetime] = Field(default_factory=datetime.now, description="Date parsing")
    json_path: str = Field(description="Chemin relatif vers JSON complet")
    file_path: Optional[str] = Field(default=None, description="Chemin relatif vers fichier source (PDF/DOCX)")
    candidat_nom: Optional[str] = Field(default=None, index=True, description="Nom candidat")
    candidat_titre: Optional[str] = Field(default=None, description="Titre professionnel")
    last_modified: Optional[datetime] = Field(default_factory=datetime.now, description="Dernière modification")

    class Config:
        extra = "allow"
