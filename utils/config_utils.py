"""
Utilitaires pour la gestion de la configuration et des tournois
"""

import json
import os
import logging

logger = logging.getLogger("coinpoker_hopper")

CONFIG_DIR = "config"
TOURNAMENTS_FILE = f"{CONFIG_DIR}/tournaments.json"

def ensure_config_dir():
    """Crée le répertoire de configuration s'il n'existe pas"""
    os.makedirs(CONFIG_DIR, exist_ok=True)

def load_tournaments():
    """
    Charge la liste des tournois depuis le fichier de configuration
    
    :return: Liste des noms de tournois
    """
    ensure_config_dir()
    
    try:
        if os.path.exists(TOURNAMENTS_FILE):
            with open(TOURNAMENTS_FILE, "r") as f:
                tournaments = json.load(f)
                return tournaments
        else:
            return []
    except Exception as e:
        logger.error(f"Erreur lors du chargement des tournois: {str(e)}")
        return []

def save_tournaments(tournaments):
    """
    Sauvegarde la liste des tournois dans le fichier de configuration
    
    :param tournaments: Liste des noms de tournois à sauvegarder
    :return: True si réussi, False sinon
    """
    ensure_config_dir()
    
    try:
        with open(TOURNAMENTS_FILE, "w") as f:
            json.dump(tournaments, f)
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde des tournois: {str(e)}")
        return False

def save_tournament_offsets(tournament_name, x_offset, y_offset):
    """
    Sauvegarde les offsets pour un tournoi spécifique
    
    :param tournament_name: Nom du tournoi
    :param x_offset: Décalage horizontal entre le nom du tournoi et le bouton
    :param y_offset: Décalage vertical entre le nom du tournoi et le bouton
    """
    ensure_config_dir()
    
    safe_name = tournament_name.lower().replace(' ', '_')
    offsets = {
        "x_offset": x_offset,
        "y_offset": y_offset
    }
    
    try:
        with open(f"{CONFIG_DIR}/{safe_name}_offsets.json", "w") as f:
            json.dump(offsets, f)
        logger.info(f"Offsets pour le tournoi '{tournament_name}' sauvegardés")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde des offsets: {str(e)}")
        return False

def load_tournament_offsets(tournament_name):
    """
    Charge les offsets pour un tournoi spécifique
    
    :param tournament_name: Nom du tournoi
    :return: Dictionnaire contenant les offsets, ou None si non trouvé
    """
    safe_name = tournament_name.lower().replace(' ', '_')
    offset_file = f"{CONFIG_DIR}/{safe_name}_offsets.json"
    
    try:
        if os.path.exists(offset_file):
            with open(offset_file, "r") as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"Erreur lors du chargement des offsets: {str(e)}")
        return None
