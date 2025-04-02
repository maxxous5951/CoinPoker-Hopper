"""
Module pour la gestion des fenêtres Windows
Permet de surveiller et d'interagir avec une fenêtre spécifique, même en arrière-plan
"""

import logging
import time
import pyautogui
import os
from PIL import Image, ImageGrab

try:
    import pygetwindow as gw
except ImportError:
    raise ImportError("Le module pygetwindow est requis. Installez-le avec: pip install pygetwindow")

logger = logging.getLogger("coinpoker_hopper")

class WindowManager:
    def __init__(self):
        # Stocke le titre de la fenêtre CoinPoker une fois trouvée
        self.coinpoker_window_title = None
        # Stocke les coordonnées et dimensions de la fenêtre
        self.window_rect = None
        # Stocke une référence à la fenêtre
        self.window = None
        # Dossier pour enregistrer les captures d'écran
        self.screenshots_dir = "resources/screenshots"
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
    def find_coinpoker_window(self):
        """
        Trouve la fenêtre CoinPoker et enregistre ses coordonnées
        
        :return: True si la fenêtre est trouvée, False sinon
        """
        try:
            # Chercher la fenêtre par des mots-clés probables dans le titre
            possible_titles = ["CoinPoker", "Coin Poker", "Poker"]
            all_windows = gw.getAllTitles()
            
            for title in all_windows:
                for keyword in possible_titles:
                    if keyword.lower() in title.lower():
                        self.coinpoker_window_title = title
                        
                        # Obtenir l'objet fenêtre et ses coordonnées
                        windows = gw.getWindowsWithTitle(title)
                        if windows:
                            self.window = windows[0]
                            self.update_window_position()
                            logger.info(f"Fenêtre CoinPoker trouvée: '{title}' à {self.window_rect}")
                            return True
            
            logger.warning("Fenêtre CoinPoker non trouvée dans la liste des fenêtres")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de la fenêtre CoinPoker: {str(e)}")
            return False
    
    def update_window_position(self):
        """Met à jour les coordonnées et dimensions de la fenêtre"""
        if self.window:
            try:
                self.window_rect = (
                    self.window.left, 
                    self.window.top, 
                    self.window.width, 
                    self.window.height
                )
                return True
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour des coordonnées de la fenêtre: {str(e)}")
                return False
        return False
    
    def capture_window_area(self):
        """
        Capture la zone de l'écran où se trouve la fenêtre CoinPoker,
        même si elle n'est pas au premier plan
        
        :return: L'image capturée ou None en cas d'échec
        """
        if not self.window_rect:
            if not self.find_coinpoker_window():
                return None
        
        try:
            # Mettre à jour la position de la fenêtre
            self.update_window_position()
            
            # Capturer la région de l'écran correspondant à la fenêtre
            screenshot = ImageGrab.grab(bbox=self.window_rect)
            
            # Enregistrer la capture pour le débogage
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"{self.screenshots_dir}/window_capture_{timestamp}.png"
            screenshot.save(screenshot_path)
            
            logger.debug(f"Capture de la zone de la fenêtre enregistrée: {screenshot_path}")
            return screenshot
        except Exception as e:
            logger.error(f"Erreur lors de la capture de la fenêtre: {str(e)}")
            return None
    
    def focus_coinpoker_window(self):
        """
        Met la fenêtre CoinPoker au premier plan
        
        :return: True si réussi, False sinon
        """
        # D'abord, vérifier que nous avons trouvé la fenêtre
        if not self.window and not self.find_coinpoker_window():
            return False
        
        try:
            # Si la fenêtre est minimisée, la restaurer
            if self.window.isMinimized:
                self.window.restore()
            
            # Mettre la fenêtre au premier plan
            self.window.activate()
            
            # Attendre un peu pour s'assurer que la fenêtre est bien au premier plan
            time.sleep(0.5)
            
            # Mettre à jour les coordonnées
            self.update_window_position()
            
            logger.info(f"Fenêtre CoinPoker '{self.coinpoker_window_title}' mise au premier plan")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la mise au premier plan de la fenêtre CoinPoker: {str(e)}")
            return False
    
    def is_coinpoker_window_focused(self):
        """
        Vérifie si la fenêtre CoinPoker est actuellement au premier plan
        
        :return: True si la fenêtre est au premier plan, False sinon
        """
        try:
            if not self.window:
                return False
                
            active_window = gw.getActiveWindow()
            return active_window and active_window.title == self.coinpoker_window_title
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du focus de la fenêtre CoinPoker: {str(e)}")
            return False
    
    def ensure_coinpoker_window_focused(self):
        """
        S'assure que la fenêtre CoinPoker est au premier plan.
        Si ce n'est pas le cas, tente de la mettre au premier plan.
        
        :return: True si la fenêtre est au premier plan après l'opération, False sinon
        """
        if not self.is_coinpoker_window_focused():
            logger.info("La fenêtre CoinPoker n'est pas au premier plan, tentative de mise au premier plan...")
            return self.focus_coinpoker_window()
        return True
    
    def click_at_position(self, x, y):
        """
        Clique à une position relative à la fenêtre CoinPoker
        
        :param x: Coordonnée x relative à la fenêtre
        :param y: Coordonnée y relative à la fenêtre
        :return: True si réussi, False sinon
        """
        if not self.window_rect:
            if not self.find_coinpoker_window():
                return False
        
        try:
            # Mettre la fenêtre au premier plan avant de cliquer
            self.focus_coinpoker_window()
            
            # Calculer les coordonnées absolues
            abs_x = self.window_rect[0] + x
            abs_y = self.window_rect[1] + y
            
            # Effectuer le clic
            pyautogui.click(abs_x, abs_y)
            logger.info(f"Clic effectué à la position relative ({x}, {y}), absolue ({abs_x}, {abs_y})")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du clic: {str(e)}")
            return False
    
    def convert_to_window_coordinates(self, screen_x, screen_y):
        """
        Convertit des coordonnées écran en coordonnées relatives à la fenêtre
        
        :param screen_x: Coordonnée x sur l'écran
        :param screen_y: Coordonnée y sur l'écran
        :return: Tuple (x, y) relatif à la fenêtre
        """
        if not self.window_rect:
            return None
        
        window_x = screen_x - self.window_rect[0]
        window_y = screen_y - self.window_rect[1]
        
        return (window_x, window_y)
    
    def convert_to_screen_coordinates(self, window_x, window_y):
        """
        Convertit des coordonnées relatives à la fenêtre en coordonnées écran
        
        :param window_x: Coordonnée x relative à la fenêtre
        :param window_y: Coordonnée y relative à la fenêtre
        :return: Tuple (x, y) sur l'écran
        """
        if not self.window_rect:
            return None
        
        screen_x = self.window_rect[0] + window_x
        screen_y = self.window_rect[1] + window_y
        
        return (screen_x, screen_y)
