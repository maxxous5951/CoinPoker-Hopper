"""
Utilitaires pour les captures d'écran et le traitement d'images
"""

import os
import pyautogui
from datetime import datetime
import logging

logger = logging.getLogger("coinpoker_hopper")

def take_screenshot(directory="resources/screenshots", prefix="coinpoker"):
    """
    Prend une capture d'écran et la sauvegarde avec un horodatage
    
    :param directory: Répertoire où sauvegarder la capture
    :param prefix: Préfixe pour le nom du fichier
    :return: Chemin complet vers le fichier sauvegardé
    """
    # S'assurer que le répertoire existe
    os.makedirs(directory, exist_ok=True)
    
    # Créer un nom de fichier avec horodatage
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{directory}/{prefix}_{timestamp}.png"
    
    # Capturer l'écran et sauvegarder
    screenshot = pyautogui.screenshot()
    screenshot.save(filename)
    
    logger.info(f"Capture d'écran sauvegardée: {filename}")
    return filename

def find_on_screen(image_path, confidence=0.8):
    """
    Cherche une image à l'écran
    
    :param image_path: Chemin vers l'image à chercher
    :param confidence: Niveau de confiance (0-1)
    :return: Position (x, y) si trouvé, None sinon
    """
    try:
        position = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
        if position:
            logger.debug(f"Image {image_path} trouvée à la position {position}")
        return position
    except Exception as e:
        logger.error(f"Erreur lors de la recherche de l'image {image_path}: {str(e)}")
        return None

def click_on_image(image_path, confidence=0.8, click=True):
    """
    Trouve et clique sur une image à l'écran
    
    :param image_path: Chemin vers l'image à chercher
    :param confidence: Niveau de confiance (0-1)
    :param click: Si True, clique sur l'image; sinon, retourne juste la position
    :return: Position (x, y) si trouvé, None sinon
    """
    position = find_on_screen(image_path, confidence)
    
    if position and click:
        pyautogui.click(position)
        logger.info(f"Clic effectué à la position {position}")
    
    return position
