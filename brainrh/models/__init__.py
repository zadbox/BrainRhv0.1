"""
Modèles SQLModel pour Brain RH
Architecture hybride : tables DB = index, JSON = données complètes
"""

from .enterprise import EnterpriseDB
from .project import ProjectDB
from .cv import CVMetaDB
from .interview_sheet import InterviewSheetDB

__all__ = ["EnterpriseDB", "ProjectDB", "CVMetaDB", "InterviewSheetDB"]
