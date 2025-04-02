"""
Module de configuration du logging pour l'application CoinPoker Hopper
"""

import logging
import os

def setup_logging():
    """
    Configure le système de logging pour l'application
    """
    # S'assurer que le dossier logs existe
    os.makedirs("logs", exist_ok=True)
    
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/coinpoker_hopper.log"),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger("coinpoker_hopper")
