"""
Gestion des chemins du projet
Calcul du PROJECT_ROOT pour éliminer les hacks sys.path
"""

from pathlib import Path

# PROJECT_ROOT = racine du projet (où se trouve config.yaml)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Chemins principaux
CONFIG_FILE = PROJECT_ROOT / "config.yaml"
ENV_FILE = PROJECT_ROOT / ".env"
DATABASE_FILE = PROJECT_ROOT / "brainrh.db"

# Dossiers de données
# PROJECTS_DIR (LEGACY - supprimé) = PROJECT_ROOT / "projects"
ENTERPRISES_DIR = PROJECT_ROOT / "enterprises"
# CV_JSON_DIR (LEGACY - supprimé) = PROJECT_ROOT / "cv_json"
CACHE_DIR = PROJECT_ROOT / "cache"
LOGS_DIR = PROJECT_ROOT / "logs"
OUTPUT_DIR = PROJECT_ROOT / "output"


def get_relative_path(absolute_path: Path) -> str:
    """
    Convertit un chemin absolu en chemin relatif au PROJECT_ROOT

    Args:
        absolute_path: Chemin absolu

    Returns:
        Chemin relatif sous forme de string
    """
    try:
        return str(absolute_path.relative_to(PROJECT_ROOT))
    except ValueError:
        # Si le chemin n'est pas sous PROJECT_ROOT, retourner tel quel
        return str(absolute_path)


def get_absolute_path(relative_path: str) -> Path:
    """
    Convertit un chemin relatif (depuis json_path) en chemin absolu

    Args:
        relative_path: Chemin relatif au PROJECT_ROOT

    Returns:
        Chemin absolu (Path)
    """
    return PROJECT_ROOT / relative_path
