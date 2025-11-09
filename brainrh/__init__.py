# -*- coding: utf-8 -*-
"""
Package Brain RH
Structure propre pour gérer la base de données SQLite + JSON complet
"""

from .database import get_session, init_db, engine
from .models import EnterpriseDB, ProjectDB, CVMetaDB, InterviewSheetDB
from .services import EnterpriseService, ProjectService, FileStorage

__version__ = "1.0.0"

__all__ = [
    "get_session",
    "init_db",
    "engine",
    "EnterpriseDB",
    "ProjectDB",
    "CVMetaDB",
    "InterviewSheetDB",
    "EnterpriseService",
    "ProjectService",
    "FileStorage",
]
