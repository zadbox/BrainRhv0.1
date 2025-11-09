# -*- coding: utf-8 -*-
"""
Configuration SQLAlchemy et gestion des sessions
Utilise SQLModel (hérite Pydantic + SQLAlchemy)
"""

from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from sqlmodel import SQLModel, Session, create_engine
from config_loader import get_config

# Charger la configuration
config = get_config()

# Lire l'URL depuis config (par défaut: sqlite:///brainrh.db)
DATABASE_URL = config.get("database", {}).get("url", "sqlite:///brainrh.db")

# Si c'est un chemin relatif SQLite, le rendre absolu
if DATABASE_URL.startswith("sqlite:///") and not DATABASE_URL.startswith("sqlite:////"):
    db_filename = DATABASE_URL.replace("sqlite:///", "")
    base_dir = Path(config.get("paths", {}).get("base_dir", "."))
    db_path = base_dir / db_filename
    DATABASE_URL = f"sqlite:///{db_path}"
else:
    # Extraire le chemin pour les logs
    db_path = Path(DATABASE_URL.replace("sqlite:///", ""))

# Créer l'engine SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Mettre True pour debug SQL
    connect_args={"check_same_thread": False}  # Nécessaire pour SQLite
)


def init_db() -> None:
    """
    Initialise la base de données (crée toutes les tables)
    À appeler au démarrage de l'application
    """
    from .models import EnterpriseDB, ProjectDB, CVMetaDB, InterviewSheetDB

    SQLModel.metadata.create_all(engine)
    print(f"[DB] Base de données initialisée: {db_path}")


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager pour obtenir une session DB avec gestion des transactions

    Usage:
        with get_session() as session:
            enterprise = session.query(EnterpriseDB).first()
            session.commit()
    """
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session_direct() -> Session:
    """
    Retourne une session directe (pour les cas où context manager n'est pas adapté)
    IMPORTANT: L'appelant doit fermer la session manuellement
    """
    return Session(engine)
