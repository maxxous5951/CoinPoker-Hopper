"""
Utilitaires pour les captures d'écran et le traitement d'images
"""

import os
import pyautogui
import numpy as np
from datetime import datetime
import logging
import cv2
from PIL import Image, ImageGrab

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

def find_on_screen(image_path, confidence=0.8, window_manager=None):
    """
    Cherche une image à l'écran ou dans la zone de la fenêtre CoinPoker
    
    :param image_path: Chemin vers l'image à chercher
    :param confidence: Niveau de confiance (0-1)
    :param window_manager: Instance de WindowManager (si fournie, cherche uniquement dans la fenêtre)
    :return: Position (x, y) sur l'écran si trouvé, None sinon
    """
    try:
        # Si un window_manager est fourni, chercher uniquement dans la fenêtre
        if window_manager and window_manager.window_rect:
            logger.debug(f"Recherche de l'image {image_path} dans la zone de la fenêtre CoinPoker")
            
            # Capturer la zone de la fenêtre
            window_image = window_manager.capture_window_area()
            if window_image is None:
                logger.warning("Impossible de capturer la zone de la fenêtre, retour à la recherche sur tout l'écran")
                position = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
                return position
            
            # Charger l'image à rechercher
            needle = Image.open(image_path)
            
            # Convertir en OpenCV pour la recherche de template
            haystack_cv = cv2.cvtColor(np.array(window_image), cv2.COLOR_RGB2BGR)
            needle_cv = cv2.cvtColor(np.array(needle), cv2.COLOR_RGB2BGR)
            
            # Utiliser la méthode de correspondance de template de OpenCV
            result = cv2.matchTemplate(haystack_cv, needle_cv, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # Vérifier si la correspondance est suffisamment bonne
            if max_val >= confidence:
                # Calculer le centre de l'image trouvée
                needle_w, needle_h = needle.size
                center_x = max_loc[0] + needle_w // 2
                center_y = max_loc[1] + needle_h // 2
                
                # Convertir en coordonnées écran
                screen_pos = window_manager.convert_to_screen_coordinates(center_x, center_y)
                
                logger.debug(f"Image {image_path} trouvée dans la fenêtre à la position {screen_pos}")
                return screen_pos
            else:
                logger.debug(f"Image {image_path} non trouvée dans la fenêtre (confiance max: {max_val})")
                return None
        else:
            # Recherche standard sur tout l'écran
            position = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
            if position:
                logger.debug(f"Image {image_path} trouvée à la position {position}")
            return position
    except Exception as e:
        logger.error(f"Erreur lors de la recherche de l'image {image_path}: {str(e)}")
        return None

def click_on_image(image_path, confidence=0.8, click=True, window_manager=None):
    """
    Trouve et clique sur une image à l'écran
    
    :param image_path: Chemin vers l'image à chercher
    :param confidence: Niveau de confiance (0-1)
    :param click: Si True, clique sur l'image; sinon, retourne juste la position
    :param window_manager: Instance de WindowManager (si fournie, cherche uniquement dans la fenêtre)
    :return: Position (x, y) si trouvé, None sinon
    """
    position = find_on_screen(image_path, confidence, window_manager)
    
    if position and click:
        # Si un window_manager est fourni et que la fenêtre n'est pas au premier plan,
        # la mettre au premier plan avant de cliquer
        if window_manager:
            window_manager.focus_coinpoker_window()
            
        pyautogui.click(position)
        logger.info(f"Clic effectué à la position {position}")
    
    return position

def find_all_on_screen(image_path, confidence=0.8, window_manager=None):
    """
    Cherche toutes les occurrences d'une image à l'écran ou dans la zone de la fenêtre CoinPoker
    
    :param image_path: Chemin vers l'image à chercher
    :param confidence: Niveau de confiance (0-1)
    :param window_manager: Instance de WindowManager (si fournie, cherche uniquement dans la fenêtre)
    :return: Liste de positions (x, y) sur l'écran si trouvées, liste vide sinon
    """
    try:
        # Si un window_manager est fourni, chercher uniquement dans la fenêtre
        if window_manager and window_manager.window_rect:
            logger.debug(f"Recherche de toutes les occurrences de l'image {image_path} dans la zone de la fenêtre CoinPoker")
            
            # Capturer la zone de la fenêtre
            window_image = window_manager.capture_window_area()
            if window_image is None:
                logger.warning("Impossible de capturer la zone de la fenêtre, retour à la recherche sur tout l'écran")
                all_positions = list(pyautogui.locateAllOnScreen(image_path, confidence=confidence))
                return [pyautogui.center(pos) for pos in all_positions]
            
            # Charger l'image à rechercher
            needle = Image.open(image_path)
            
            # Convertir en OpenCV pour la recherche de template
            haystack_cv = cv2.cvtColor(np.array(window_image), cv2.COLOR_RGB2BGR)
            needle_cv = cv2.cvtColor(np.array(needle), cv2.COLOR_RGB2BGR)
            
            # Utiliser la méthode de correspondance de template de OpenCV
            result = cv2.matchTemplate(haystack_cv, needle_cv, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= confidence)
            
            # Obtenir toutes les positions
            positions = []
            needle_w, needle_h = needle.size
            
            # Fusionner les points proches
            threshold_dist = 10  # Distance en pixels pour considérer deux points comme identiques
            for pt in zip(*locations[::-1]):  # Inverser car OpenCV donne (y, x)
                center_x = pt[0] + needle_w // 2
                center_y = pt[1] + needle_h // 2
                
                # Vérifier si le point est proche d'un point déjà trouvé
                is_close = False
                for existing_pt in positions:
                    if ((existing_pt[0] - center_x) ** 2 + (existing_pt[1] - center_y) ** 2) < threshold_dist ** 2:
                        is_close = True
                        break
                
                if not is_close:
                    positions.append((center_x, center_y))
            
            # Convertir en coordonnées écran
            screen_positions = [window_manager.convert_to_screen_coordinates(x, y) for x, y in positions]
            
            logger.debug(f"Trouvé {len(screen_positions)} occurrences de l'image {image_path} dans la fenêtre")
            return screen_positions
        else:
            # Recherche standard sur tout l'écran
            all_positions = list(pyautogui.locateAllOnScreen(image_path, confidence=confidence))
            centers = [pyautogui.center(pos) for pos in all_positions]
            logger.debug(f"Trouvé {len(centers)} occurrences de l'image {image_path} sur l'écran")
            return centers
    except Exception as e:
        logger.error(f"Erreur lors de la recherche des occurrences de l'image {image_path}: {str(e)}")
        return []
