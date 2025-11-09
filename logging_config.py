import logging
import sys
from pathlib import Path

def setup_logging():
    """Configure le logging pour capturer tous les logs dans un fichier"""
    
    # Créer le dossier logs s'il n'existe pas
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / "api_debug.log"
    
    # Configuration du logger racine
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='a', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Logger spécifique pour l'API
    logger = logging.getLogger('api')
    logger.setLevel(logging.DEBUG)
    
    print(f"✅ Logging configuré - Fichier: {log_file}")
    return logger

# Configurer au démarrage
setup_logging()


