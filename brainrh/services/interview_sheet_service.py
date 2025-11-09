"""
InterviewSheetService - Gestion des fiches d'entretien
Couche service : DB JSONB pour données complètes
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
import uuid

from brainrh.database import get_session
from brainrh.models import InterviewSheetDB


class InterviewSheetService:
    """Service pour gestion des fiches d'entretien"""

    @staticmethod
    def create(
        candidate_id: str,
        job_id: str,
        matching_id: str,
        interviewer_id: str,
        data: Dict[str, Any],
        json_path: str
    ) -> Dict[str, Any]:
        """
        Crée une nouvelle fiche d'entretien (draft)

        Args:
            candidate_id: ID du candidat (CV)
            job_id: ID de l'offre
            matching_id: ID du matching source
            interviewer_id: ID du recruteur
            data: Données structurées de la fiche
            json_path: Chemin relatif vers le fichier JSON

        Returns:
            Données de la fiche créée
        """
        interview_sheet_id = str(uuid.uuid4())

        with get_session() as session:
            db_sheet = InterviewSheetDB(
                id=interview_sheet_id,
                candidate_id=candidate_id,
                job_id=job_id,
                matching_id=matching_id,
                interviewer_id=interviewer_id,
                status="draft",
                data=data,
                json_path=json_path,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(db_sheet)
            session.commit()
            session.refresh(db_sheet)

            return InterviewSheetService._to_dict(db_sheet)

    @staticmethod
    def get(interview_sheet_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère une fiche d'entretien par ID

        Args:
            interview_sheet_id: ID de la fiche

        Returns:
            Données de la fiche ou None
        """
        with get_session() as session:
            db_sheet = session.get(InterviewSheetDB, interview_sheet_id)

            if not db_sheet:
                return None

            return InterviewSheetService._to_dict(db_sheet)

    @staticmethod
    def update_partial(interview_sheet_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Met à jour partiellement une fiche d'entretien

        Args:
            interview_sheet_id: ID de la fiche
            updates: Dictionnaire de champs à mettre à jour

        Returns:
            Données mises à jour ou None
        """
        with get_session() as session:
            db_sheet = session.get(InterviewSheetDB, interview_sheet_id)

            if not db_sheet:
                return None

            # Mettre à jour les champs autorisés
            if "data" in updates:
                db_sheet.data = updates["data"]
            if "status" in updates:
                db_sheet.status = updates["status"]
            if "pdf_url" in updates:
                db_sheet.pdf_url = updates["pdf_url"]

            db_sheet.updated_at = datetime.now()

            session.add(db_sheet)
            session.commit()
            session.refresh(db_sheet)

            return InterviewSheetService._to_dict(db_sheet)

    @staticmethod
    def finalize(interview_sheet_id: str) -> Optional[Dict[str, Any]]:
        """
        Finalise une fiche d'entretien (passe en status completed)

        Args:
            interview_sheet_id: ID de la fiche

        Returns:
            Données finalisées ou None
        """
        with get_session() as session:
            db_sheet = session.get(InterviewSheetDB, interview_sheet_id)

            if not db_sheet:
                return None

            db_sheet.status = "completed"
            db_sheet.completed_at = datetime.now()
            db_sheet.updated_at = datetime.now()

            session.add(db_sheet)
            session.commit()
            session.refresh(db_sheet)

            return InterviewSheetService._to_dict(db_sheet)

    @staticmethod
    def find_existing(candidate_id: str, job_id: str, matching_id: str) -> Optional[Dict[str, Any]]:
        """
        Recherche une fiche d'entretien existante pour ce trio (tous statuts)

        Args:
            candidate_id: ID du candidat
            job_id: ID de l'offre
            matching_id: ID du matching

        Returns:
            Fiche existante (la plus récente) ou None
        """
        with get_session() as session:
            query = select(InterviewSheetDB).where(
                InterviewSheetDB.candidate_id == candidate_id,
                InterviewSheetDB.job_id == job_id,
                InterviewSheetDB.matching_id == matching_id
            ).order_by(InterviewSheetDB.created_at.desc())

            db_sheet = session.exec(query).first()

            if not db_sheet:
                return None

            return InterviewSheetService._to_dict(db_sheet)

    @staticmethod
    def list_by_candidate(candidate_id: str) -> List[Dict[str, Any]]:
        """
        Liste toutes les fiches d'un candidat

        Args:
            candidate_id: ID du candidat

        Returns:
            Liste des fiches
        """
        with get_session() as session:
            query = select(InterviewSheetDB).where(
                InterviewSheetDB.candidate_id == candidate_id
            )
            db_sheets = session.exec(query).all()

            return [InterviewSheetService._to_dict(sheet) for sheet in db_sheets]

    @staticmethod
    def list_all(
        job_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Liste les fiches d'entretien avec filtres optionnels

        Args:
            job_id: Filtrer par projet (optionnel)
            limit: Limiter le nombre de résultats (optionnel)

        Returns:
            Liste des fiches d'entretien
        """
        with get_session() as session:
            query = select(InterviewSheetDB).order_by(InterviewSheetDB.created_at.desc())

            # Filtres
            if job_id:
                query = query.where(InterviewSheetDB.job_id == job_id)

            if limit:
                query = query.limit(limit)

            db_sheets = session.exec(query).all()
            return [InterviewSheetService._to_dict(sheet) for sheet in db_sheets]

    @staticmethod
    def _to_dict(db_sheet: InterviewSheetDB) -> Dict[str, Any]:
        """Convertit un objet DB en dictionnaire"""
        return {
            "id": db_sheet.id,
            "candidate_id": db_sheet.candidate_id,
            "job_id": db_sheet.job_id,
            "matching_id": db_sheet.matching_id,
            "interviewer_id": db_sheet.interviewer_id,
            "status": db_sheet.status,
            "data": db_sheet.data,
            "json_path": db_sheet.json_path,
            "created_at": db_sheet.created_at.isoformat(),
            "updated_at": db_sheet.updated_at.isoformat(),
            "completed_at": db_sheet.completed_at.isoformat() if db_sheet.completed_at else None,
            "pdf_url": db_sheet.pdf_url
        }
