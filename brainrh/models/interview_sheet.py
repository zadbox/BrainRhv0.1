"""
Modèle InterviewSheet pour la base de données
Table interview_sheets = fiches d'entretien complètes en JSONB
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, JSON


class InterviewSheetDB(SQLModel, table=True):
    """
    Table interview_sheets
    Fiche d'entretien complète avec données structurées en JSONB
    """
    __tablename__ = "interview_sheets"

    id: str = Field(primary_key=True, description="UUID unique fiche")
    candidate_id: str = Field(index=True, description="ID candidat (CV)")
    job_id: str = Field(index=True, description="ID offre")
    matching_id: str = Field(description="ID matching dont provient la fiche")
    interviewer_id: str = Field(description="ID recruteur")
    status: str = Field(default="draft", index=True, description="Statut (draft/in_progress/completed)")
    data: dict = Field(sa_column=Column(JSON), description="Données structurées JSONB (cache)")
    json_path: str = Field(description="Chemin relatif vers JSON complet (source de vérité)")
    created_at: datetime = Field(default_factory=datetime.now, description="Date création")
    updated_at: datetime = Field(default_factory=datetime.now, description="Date dernière modification")
    completed_at: Optional[datetime] = Field(default=None, description="Date finalisation (si completed)")
    pdf_url: Optional[str] = Field(default=None, max_length=500, description="URL PDF généré")

    class Config:
        extra = "allow"
