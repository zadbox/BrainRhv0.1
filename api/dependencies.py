"""
FastAPI Dependencies
Configuration, clients, utilitaires réutilisables
"""

import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Charger variables d'environnement
load_dotenv()


def get_openai_client() -> OpenAI:
    """
    Retourne un client OpenAI configuré

    Returns:
        Client OpenAI

    Raises:
        ValueError: Si OPENAI_API_KEY n'est pas définie
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY non trouvée dans les variables d'environnement")

    return OpenAI(api_key=api_key)


def get_projects_dir() -> Path:
    """
    Retourne le dossier racine des projets

    Returns:
        Path vers le dossier projects/
    """
    return Path("projects")


def get_project_dir(project_id: str) -> Path:
    """
    Retourne le dossier d'un projet spécifique

    Args:
        project_id: ID du projet

    Returns:
        Path vers le dossier du projet
    """
    return get_projects_dir() / project_id


def get_cvs_parsed_dir(project_id: str) -> Path:
    """
    Retourne le dossier des CVs parsés d'un projet

    Args:
        project_id: ID du projet

    Returns:
        Path vers cvs_parsed/
    """
    return get_project_dir(project_id) / "cvs_parsed"


def get_offres_dir(project_id: str) -> Path:
    """
    Retourne le dossier des offres d'un projet

    Args:
        project_id: ID du projet

    Returns:
        Path vers offres/
    """
    return get_project_dir(project_id) / "offres"


def get_historique_dir(project_id: str) -> Path:
    """
    Retourne le dossier de l'historique d'un projet

    Args:
        project_id: ID du projet

    Returns:
        Path vers historique/
    """
    return get_project_dir(project_id) / "historique"
