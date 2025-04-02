"""
Module pour la gestion des fenêtres Windows
Permet de surveiller et de ramener au premier plan une fenêtre spécifique
"""

import logging
import time
import pyautogui

try:
    import pygetwindow as gw
except ImportError:
    raise ImportError("Le module pygetwindow est requis. Installez-le avec: pip install pygetwindow")

logger = logging.getLogger("coinpoker_hopper")

class WindowManager:
    def __init__(self):
        # Stocke le titre de la fenêtre CoinPoker une fois trouvée
        self.coinpoker_window_title = None
        
    def find_coinpoker_window(self):
        """
        Trouve la fenêtre CoinPoker, même si elle n'est pas au premier plan
        
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
                        logger.info(f"Fenêtre CoinPoker trouvée: '{title}'")
                        return True
            
            logger.warning("Fenêtre CoinPoker non trouvée dans la liste des fenêtres")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de la fenêtre CoinPoker: {str(e)}")
            return False
    
    def focus_coinpoker_window(self):
        """
        Met la fenêtre CoinPoker au premier plan
        
        :return: True si réussi, False sinon
        """
        # D'abord, vérifier que nous avons trouvé la fenêtre
        if not self.coinpoker_window_title and not self.find_coinpoker_window():
            return False
        
        try:
            windows = gw.getWindowsWithTitle(self.coinpoker_window_title)
            
            if not windows:
                logger.warning(f"Fenêtre '{self.coinpoker_window_title}' non trouvée")
                # Essayer de rechercher à nouveau la fenêtre
                if not self.find_coinpoker_window():
                    return False
                windows = gw.getWindowsWithTitle(self.coinpoker_window_title)
                if not windows:
                    return False
            
            window = windows[0]
            
            # Si la fenêtre est minimisée, la restaurer
            if window.isMinimized:
                window.restore()
            
            # Mettre la fenêtre au premier plan
            window.activate()
            
            # Attendre un peu pour s'assurer que la fenêtre est bien au premier plan
            time.sleep(0.5)
            
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
            active_window = gw.getActiveWindow()
            return active_window and self.coinpoker_window_title and self.coinpoker_window_title in active_window.title
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
            if not self.focus_coinpoker_window():
                # Si la mise au premier plan a échoué, essayer de trouver la fenêtre à nouveau
                if self.find_coinpoker_window():
                    return self.focus_coinpoker_window()
                return False
        return True
