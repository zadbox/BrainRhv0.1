"""
Helper pour gestion des fichiers JSON
Abstraction pour lecture/écriture JSON avec chemins relatifs
"""

import json
from pathlib import Path
from typing import Dict, Any
from brainrh.paths import get_absolute_path, get_relative_path


class FileStorage:
    """
    Helper pour gestion centralisée des fichiers JSON
    Tous les chemins en DB sont relatifs, convertis en absolus ici
    """

    @staticmethod
    def load_json(relative_path: str) -> Dict[str, Any]:
        """
        Charge un fichier JSON depuis un chemin relatif

        Args:
            relative_path: Chemin relatif au PROJECT_ROOT

        Returns:
            Contenu JSON (dict)

        Raises:
            FileNotFoundError: Si le fichier n'existe pas
        """
        absolute_path = get_absolute_path(relative_path)

        if not absolute_path.exists():
            raise FileNotFoundError(f"Fichier JSON introuvable: {absolute_path}")

        with open(absolute_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def save_json(relative_path: str, data: Dict[str, Any]):
        """
        Sauvegarde des données JSON dans un fichier

        Args:
            relative_path: Chemin relatif au PROJECT_ROOT
            data: Données à sauvegarder (dict)
        """
        absolute_path = get_absolute_path(relative_path)

        # Créer le dossier parent si nécessaire
        absolute_path.parent.mkdir(parents=True, exist_ok=True)

        with open(absolute_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def file_exists(relative_path: str) -> bool:
        """
        Vérifie si un fichier existe

        Args:
            relative_path: Chemin relatif au PROJECT_ROOT

        Returns:
            True si le fichier existe
        """
        absolute_path = get_absolute_path(relative_path)
        return absolute_path.exists()

    @staticmethod
    def delete_file(relative_path: str):
        """
        Supprime un fichier

        Args:
            relative_path: Chemin relatif au PROJECT_ROOT
        """
        absolute_path = get_absolute_path(relative_path)

        if absolute_path.exists():
            absolute_path.unlink()
