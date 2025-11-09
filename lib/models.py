# -*- coding: utf-8 -*-
"""
Pydantic models pour Brain RH
Définition des structures de données (CV, Offre, Résultats)
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


# ==================== IDENTITÉ ====================

class Identite(BaseModel):
    """Identité du candidat"""
    nom: str = ""
    prenom: str = ""
    email: str = ""
    telephone: str = ""
    adresse: str = ""
    linkedin: str = ""
    autres_reseaux: List[str] = Field(default_factory=list)


# ==================== EXPÉRIENCE ====================

class Experience(BaseModel):
    """Expérience professionnelle"""
    poste: str = ""
    entreprise: str = ""
    lieu: str = ""
    date_debut: str = ""
    date_fin: str = ""
    duree: str = ""
    missions: List[str] = Field(default_factory=list)


# ==================== CV ====================

class CV(BaseModel):
    """CV structuré"""
    cv: str  # Filename (requis)
    identite: Identite = Field(default_factory=Identite)
    titre: str = ""
    resume_professionnel: str = ""
    competences_techniques: List[str] = Field(default_factory=list)
    competences_transversales: List[str] = Field(default_factory=list)
    langues: List[str] = Field(default_factory=list)
    experiences_professionnelles: List[Experience] = Field(default_factory=list)
    formations: List[Dict[str, Any]] = Field(default_factory=list)
    certifications: List[Dict[str, Any]] = Field(default_factory=list)  # Changed to Dict for LLM output
    projets: List[Dict[str, Any]] = Field(default_factory=list)  # Changed to Dict for LLM output

    class Config:
        # Permettre les champs supplémentaires pour compatibilité avec JSONs existants
        extra = "allow"


# ==================== OFFRE ====================

class OffreSection(BaseModel):
    """Section d'une offre d'emploi"""
    titre: str = ""
    description: str = ""
    resume_professionnel: str = ""
    competences_techniques: List[str] = Field(default_factory=list)
    competences_transversales: List[str] = Field(default_factory=list)
    outils: List[str] = Field(default_factory=list)  # Ajouté pour enrichissement IA
    langages: List[str] = Field(default_factory=list)  # Ajouté pour enrichissement IA
    langues: List[str] = Field(default_factory=list)
    experiences_professionnelles: List[Dict[str, Any]] = Field(default_factory=list)
    formations: List[Dict[str, Any]] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    projets: List[str] = Field(default_factory=list)

    class Config:
        extra = "allow"


class Offre(BaseModel):
    """Offre d'emploi avec critères"""
    sections: OffreSection
    must_have: List[str] = Field(default_factory=list, description="Critères éliminatoires")
    nice_have: List[str] = Field(default_factory=list, description="Critères souhaitables")

    class Config:
        extra = "allow"


# ==================== RÉSULTATS MATCHING ====================

class Evidence(BaseModel):
    """Évidence pour justifier une affirmation dans le reranking"""
    id: str  # Ex: "E1", "E2", etc.
    type: str  # "section", "json_path", "quote"
    ref: str  # Repère humain, chemin JSON, ou citation


class EvidenceMap(BaseModel):
    """Mapping des evidences utilisées dans chaque commentaire"""
    commentaire_scoring: List[str] = Field(default_factory=list)  # IDs des evidences
    appreciation_globale: List[str] = Field(default_factory=list)  # IDs des evidences


class Gap(BaseModel):
    """Trou détecté dans le parcours professionnel"""
    period: str  # Ex: "2020-03 → 2020-09"
    duration_months: int  # Durée en mois
    between: str  # Ex: "Expérience #2 (Foo) et Expérience #3 (Bar)"
    cv_excerpt: Optional[str] = None  # Citation pertinente du CV si disponible


class Overlap(BaseModel):
    """Chevauchement détecté entre expériences"""
    overlap_period: str  # Ex: "2020-01 → 2020-06"
    overlap_days: int  # Durée du chevauchement en jours
    experiences: str  # Ex: "Expérience #1 (Foo) et Expérience #2 (Bar)"
    same_company: bool  # True si même entreprise
    cv_excerpt: Optional[str] = None  # Citation pertinente du CV si disponible


class Flags(BaseModel):
    """Drapeaux de vigilance détectés automatiquement"""
    gappes: List[Gap] = Field(default_factory=list)
    overlaps: List[Overlap] = Field(default_factory=list)


class ResultatMatching(BaseModel):
    """Résultat de matching pour un CV"""
    cv: str  # Filename
    score_final: float = Field(ge=0.0, le=1.0, description="Score final (0-1)")
    score_base: float = Field(ge=0.0, le=1.0, description="Score de similarité base")
    bonus_nice_have_multiplicateur: float = Field(
        ge=0.0,
        le=1.0,
        description="Malus nice-have (0.95^nb_manquants)"
    )
    coefficient_qualite_experience: float = Field(
        ge=1.0,
        le=1.4,
        description="Coefficient qualité expérience (1.0-1.4)"
    )
    nice_have_manquants: List[str] = Field(default_factory=list)
    commentaire_scoring: Optional[str] = Field(
        None,
        description="Commentaire LLM sur le scoring (si re-ranking)"
    )
    appreciation_globale: Optional[str] = Field(
        None,
        description="Appréciation globale LLM (si re-ranking)"
    )
    # Nouveaux champs pour evidences et flags
    evidences: List[Evidence] = Field(default_factory=list, description="Évidences pour justifier les affirmations")
    evidence_map: Optional[EvidenceMap] = Field(None, description="Mapping des evidences par commentaire")
    flags: Optional[Flags] = Field(None, description="Drapeaux de vigilance (gappes, overlaps)")

    @validator('score_final', 'score_base')
    def clamp_score(cls, v):
        """S'assurer que les scores restent entre 0 et 1"""
        return max(0.0, min(1.0, v))

    @validator('coefficient_qualite_experience')
    def clamp_coefficient(cls, v):
        """S'assurer que le coefficient reste entre 1.0 et 1.4"""
        return max(1.0, min(1.4, v))

    class Config:
        extra = "allow"


class MatchingMetadata(BaseModel):
    """Métadonnées du matching"""
    total_cvs: int
    filtered_must_have: int
    top_reranked: int
    duree_totale_s: float
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class MatchingResponse(BaseModel):
    """Réponse complète d'un matching"""
    results: List[ResultatMatching]
    metadata: MatchingMetadata


# ==================== PARSING ====================

class CVParseResult(BaseModel):
    """Résultat du parsing d'un CV"""
    filename: str
    success: bool
    data: Optional[CV] = None
    error: Optional[str] = None
    timings: Optional[Dict[str, float]] = None


class CVParseResponse(BaseModel):
    """Réponse du parsing de CVs"""
    success_count: int
    failed_count: int
    total: int
    results: List[CVParseResult]
    timings: Optional[Dict[str, Any]] = None


# ==================== EVENTS SSE ====================

class SSEProgressEvent(BaseModel):
    """Événement de progression SSE"""
    event: str = "progress"
    step: str  # "extracting", "parsing", "must_have_filtering", etc.
    current: Optional[int] = None
    total: Optional[int] = None
    progress: Optional[float] = None  # 0.0-1.0
    message: Optional[str] = None
    filename: Optional[str] = None


class SSEResultEvent(BaseModel):
    """Événement de résultat SSE"""
    event: str = "result"
    data: Dict[str, Any]  # CV, ResultatMatching, etc.


class SSEDoneEvent(BaseModel):
    """Événement de fin SSE"""
    event: str = "done"
    summary: Dict[str, Any]


class SSEErrorEvent(BaseModel):
    """Événement d'erreur SSE"""
    event: str = "error"
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


# ==================== PROJETS & ENTREPRISES ====================

class Project(BaseModel):
    """Projet de recrutement"""
    id: str
    nom: str
    enterprise_id: Optional[str] = None
    service_demandeur: Optional[str] = None
    responsable_offre: Optional[str] = None
    contact_responsable: Optional[str] = None
    notes: Optional[str] = None
    created_at: str
    last_modified: str
    status: str = "actif"  # "actif" ou "archive"

    class Config:
        extra = "allow"


class Enterprise(BaseModel):
    """Entreprise cliente"""
    id: str
    nom: str
    secteur: Optional[str] = None
    created_at: Optional[str] = None
    last_modified: Optional[str] = None
    projects_count: int = 0

    class Config:
        extra = "allow"


# ==================== ERREURS API ====================

class APIError(BaseModel):
    """Erreur API normalisée"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    status: Optional[int] = None
