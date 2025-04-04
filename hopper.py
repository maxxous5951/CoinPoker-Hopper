"""
Module principal du CoinPoker Hopper
"""

import os
import time
import json
import logging
import pyautogui
import tkinter as tk
from datetime import datetime
import cv2
import numpy as np
from PIL import Image

from window_manager import WindowManager
from utils.image_utils import take_screenshot, find_on_screen, click_on_image, find_all_on_screen
from utils.config_utils import save_tournament_offsets, load_tournament_offsets

logger = logging.getLogger("coinpoker_hopper")

class CoinPokerHopper:
    def __init__(self, tournament_name):
        """
        Initialise le hopper CoinPoker pour rechercher un tournoi spécifique
        
        :param tournament_name: Nom du tournoi à rechercher et rejoindre
        """
        self.tournament_name = tournament_name
        self.check_interval = 5  # secondes entre chaque vérification
        self.screenshots_dir = "resources/screenshots"
        self.images_dir = "resources/images"
        self.running = False
        self.status_callback = None
        
        # Initialiser le gestionnaire de fenêtres
        self.window_manager = WindowManager()
        self.background_mode = True  # Activer la détection en arrière-plan par défaut
        
        # Créer les dossiers nécessaires s'ils n'existent pas
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        
        # Tentative initiale de trouver la fenêtre CoinPoker
        if not self.window_manager.find_coinpoker_window():
            logger.warning("Fenêtre CoinPoker non trouvée lors de l'initialisation")
    
    def set_status_callback(self, callback):
        """Définit une fonction de rappel pour mettre à jour le statut dans l'interface"""
        self.status_callback = callback
    
    def update_status(self, message):
        """Met à jour le statut dans l'interface si une fonction de rappel est définie"""
        if self.status_callback:
            self.status_callback(message)
        logger.info(message)
    
    def set_background_mode(self, enabled):
        """Active ou désactive le mode de détection en arrière-plan"""
        self.background_mode = enabled
        self.update_status(f"Mode de détection en arrière-plan {'activé' if enabled else 'désactivé'}")
    
    def focus_coinpoker_window(self):
        """Tente de mettre la fenêtre CoinPoker au premier plan"""
        try:
            result = self.window_manager.focus_coinpoker_window()
            if result:
                self.update_status("Fenêtre CoinPoker mise au premier plan")
                time.sleep(0.5)  # Petit délai pour s'assurer que la fenêtre est bien active
                return True
            else:
                # Fallback : essayer l'ancienne méthode avec le logo
                logo_path = f"{self.images_dir}/coinpoker_logo.png"
                if os.path.exists(logo_path):
                    coinpoker_logo = find_on_screen(logo_path)
                    
                    if coinpoker_logo:
                        pyautogui.click(coinpoker_logo)
                        self.update_status("Fenêtre CoinPoker mise au premier plan (méthode fallback)")
                        time.sleep(0.5)
                        # Mettre à jour la position de la fenêtre après l'avoir trouvée
                        self.window_manager.find_coinpoker_window()
                        return True
                
                self.update_status("Impossible de trouver la fenêtre CoinPoker")
                return False
        except Exception as e:
            self.update_status(f"Erreur lors de la mise au premier plan: {str(e)}")
            return False
    
    def navigate_to_tournaments(self):
        """Navigue vers l'onglet des tournois"""
        try:
            # Cliquer sur l'onglet Tournaments
            if self.background_mode:
                tournaments_tab = click_on_image(
                    f"{self.images_dir}/tournaments_tab.png", 
                    window_manager=self.window_manager
                )
            else:
                tournaments_tab = click_on_image(f"{self.images_dir}/tournaments_tab.png")
            
            if tournaments_tab:
                self.update_status("Navigation vers l'onglet tournois réussie")
                time.sleep(1)  # Attendre le chargement de la page
                return True
            else:
                self.update_status("Bouton Tournaments non trouvé")
                return False
        except Exception as e:
            self.update_status(f"Erreur lors de la navigation vers les tournois: {str(e)}")
            return False
    
    def find_tournament_in_list(self):
        """
        Recherche le tournoi dans la liste visible à l'écran et vérifie que le bouton REGISTERING est disponible
        
        :return: Position (x, y) du tournoi si trouvé et inscriptible, None sinon
        """
        try:
            # Chercher toutes les occurrences du nom du tournoi
            tournament_image = f"{self.images_dir}/{self.tournament_name.lower().replace(' ', '_')}.png"
            
            if not os.path.exists(tournament_image):
                self.update_status(f"Image de référence pour le tournoi '{self.tournament_name}' non trouvée")
                return None
            
            if self.background_mode:
                # En mode arrière-plan, utiliser le window_manager pour la recherche
                tournament_positions = find_all_on_screen(
                    tournament_image, 
                    confidence=0.8, 
                    window_manager=self.window_manager
                )
            else:
                # En mode normal, rechercher sur l'écran visible
                tournament_positions = [
                    pyautogui.center(pos) for pos in list(
                        pyautogui.locateAllOnScreen(tournament_image, confidence=0.8)
                    )
                ]
            
            if not tournament_positions:
                self.update_status(f"Tournoi '{self.tournament_name}' non trouvé dans la liste actuelle")
                return None
                
            self.update_status(f"Trouvé {len(tournament_positions)} occurrences du tournoi '{self.tournament_name}'")
            
            # Pour chaque occurrence du tournoi, vérifier si un bouton REGISTERING est disponible sur la même ligne
            for tournament_center in tournament_positions:
                tournament_y = tournament_center[1]
                
                self.update_status(f"Vérification de l'occurrence à la position {tournament_center}")
                
                # Vérifier s'il existe des offsets spécifiques pour ce tournoi
                offsets = load_tournament_offsets(self.tournament_name)
                
                if offsets:
                    # Utiliser les offsets préconfigurés pour vérifier si le bouton est disponible
                    expected_button_x = tournament_center[0] + offsets["x_offset"]
                    expected_button_y = tournament_center[1] + offsets["y_offset"]
                    expected_button_position = (expected_button_x, expected_button_y)
                    
                    # En mode arrière-plan, convertir en coordonnées relatives si nécessaire
                    if self.background_mode and self.window_manager.window_rect:
                        relative_pos = self.window_manager.convert_to_window_coordinates(
                            expected_button_x, expected_button_y
                        )
                        if relative_pos:
                            rel_x, rel_y = relative_pos
                            # Prendre une petite capture autour de cette position
                            window_image = self.window_manager.capture_window_area()
                            if window_image:
                                # Extraire la région d'intérêt
                                region_x = max(0, rel_x - 50)
                                region_y = max(0, rel_y - 10)
                                region_width = 100
                                region_height = 20
                                
                                region = window_image.crop((
                                    region_x, 
                                    region_y, 
                                    min(window_image.width, region_x + region_width), 
                                    min(window_image.height, region_y + region_height)
                                ))
                                
                                # Sauvegarder pour vérification
                                region_path = f"{self.screenshots_dir}/button_check_temp.png"
                                region.save(region_path)
                                
                                # Vérifier si cette région contient un bouton REGISTERING
                                specific_button_file = f"{self.images_dir}/{self.tournament_name.lower().replace(' ', '_')}_register_button.png"
                                
                                if os.path.exists(specific_button_file):
                                    # Utiliser OpenCV pour la correspondance de template
                                    needle = Image.open(specific_button_file)
                                    haystack_cv = cv2.cvtColor(np.array(region), cv2.COLOR_RGB2BGR)
                                    needle_cv = cv2.cvtColor(np.array(needle), cv2.COLOR_RGB2BGR)
                                    
                                    result = cv2.matchTemplate(haystack_cv, needle_cv, cv2.TM_CCOEFF_NORMED)
                                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                                    
                                    if max_val >= 0.7:
                                        self.update_status(f"Bouton REGISTERING trouvé pour l'occurrence du tournoi à {tournament_center}")
                                        return tournament_center
                    
                    # Si on n'a pas pu vérifier en mode arrière-plan ou si le mode est désactivé
                    if not self.background_mode:
                        # Prendre une petite capture d'écran autour de cette position pour vérifier
                        region = (
                            expected_button_x - 50, 
                            expected_button_y - 10, 
                            100, 
                            20
                        )
                        
                        try:
                            # Vérifier si cette région contient un bouton REGISTERING
                            button_region = pyautogui.screenshot(region=region)
                            button_region.save(f"{self.screenshots_dir}/button_check_temp.png")
                            
                            # Comparer avec l'image de référence du bouton REGISTERING
                            specific_button_file = f"{self.images_dir}/{self.tournament_name.lower().replace(' ', '_')}_register_button.png"
                            
                            if os.path.exists(specific_button_file):
                                # Comparer avec le bouton spécifique
                                register_pos = pyautogui.locate(
                                    specific_button_file, 
                                    f"{self.screenshots_dir}/button_check_temp.png", 
                                    confidence=0.7
                                )
                            else:
                                # Comparer avec le bouton générique
                                register_pos = pyautogui.locate(
                                    f"{self.images_dir}/registering_button.png", 
                                    f"{self.screenshots_dir}/button_check_temp.png", 
                                    confidence=0.7
                                )
                            
                            if register_pos:
                                self.update_status(f"Bouton REGISTERING trouvé pour l'occurrence du tournoi à {tournament_center}")
                                return tournament_center
                        except:
                            pass
                
                # Méthode alternative : rechercher un bouton REGISTERING sur la même ligne
                registering_button_image = f"{self.images_dir}/registering_button.png"
                if not os.path.exists(registering_button_image):
                    self.update_status("Image de référence pour le bouton REGISTERING non trouvée")
                    return None
                
                if self.background_mode:
                    # En mode arrière-plan, utiliser le window_manager pour la recherche
                    all_registering_buttons = find_all_on_screen(
                        registering_button_image, 
                        confidence=0.8, 
                        window_manager=self.window_manager
                    )
                else:
                    # En mode normal, rechercher sur l'écran visible
                    all_registering_buttons = [
                        pyautogui.center(pos) for pos in list(
                            pyautogui.locateAllOnScreen(registering_button_image, confidence=0.8)
                        )
                    ]
                
                if all_registering_buttons:
                    # Trouver le bouton le plus proche sur la même ligne (± 20 pixels)
                    for button_center in all_registering_buttons:
                        y_diff = abs(button_center[1] - tournament_y)
                        
                        if y_diff < 20:  # Tolérance de 20 pixels verticalement
                            self.update_status(f"Bouton REGISTERING trouvé sur la même ligne pour l'occurrence du tournoi à {tournament_center}")
                            return tournament_center
            
            self.update_status(f"Aucune occurrence du tournoi '{self.tournament_name}' avec bouton REGISTERING disponible trouvée")
            return None
                
        except Exception as e:
            self.update_status(f"Erreur lors de la recherche du tournoi: {str(e)}")
            return None
    
    def register_for_tournament(self, tournament_position):
        """
        Tente de s'inscrire au tournoi
        
        :param tournament_position: Position (x, y) du tournoi dans la liste
        :return: True si réussi, False sinon
        """
        try:
            # Récupérer les offsets pour ce tournoi s'ils existent
            offsets = load_tournament_offsets(self.tournament_name)
            specific_button_file = f"{self.images_dir}/{self.tournament_name.lower().replace(' ', '_')}_register_button.png"
            
            # En mode arrière-plan, mettre la fenêtre au premier plan avant de cliquer
            if self.background_mode:
                self.focus_coinpoker_window()
            
            if offsets and os.path.exists(specific_button_file):
                # Méthode 1: Utiliser les offsets pré-configurés (méthode la plus précise)
                self.update_status("Utilisation des offsets pré-configurés pour trouver le bouton d'inscription")
                
                # Calculer la position exacte du bouton en fonction des offsets
                register_button_x = tournament_position[0] + offsets["x_offset"]
                register_button_y = tournament_position[1] + offsets["y_offset"]
                register_button_position = (register_button_x, register_button_y)
                
                self.update_status(f"Position calculée du bouton: {register_button_position}")
                
                # Cliquer sur la position calculée
                pyautogui.click(register_button_position)
                time.sleep(1)
                
                # Chercher le bouton ACCEPT si une confirmation est nécessaire
                if self.background_mode:
                    accept_button = click_on_image(f"{self.images_dir}/accept_button.png", window_manager=self.window_manager)
                else:
                    accept_button = click_on_image(f"{self.images_dir}/accept_button.png")
                
                if accept_button:
                    self.update_status(f"Inscription au tournoi '{self.tournament_name}' confirmée!")
                    return True
                else:
                    self.update_status("Pas de bouton de confirmation trouvé, l'inscription peut être déjà complète")
                    return True
                
            else:
                # Méthode 2: Rechercher spécifiquement le bouton REGISTERING sur la même ligne
                self.update_status("Pas d'offsets pré-configurés, recherche du bouton REGISTERING sur la même ligne")
                
                # Récupérer la position Y du tournoi pour s'assurer de cliquer sur le bouton REGISTERING de la même ligne
                tournament_y = tournament_position[1]
                
                # Chercher le bouton REGISTERING à droite du tournoi sur la même ligne
                self.update_status(f"Recherche du bouton REGISTERING sur la ligne Y={tournament_y}")
                
                # Chercher tous les boutons REGISTERING visibles
                registering_button_image = f"{self.images_dir}/registering_button.png"
                if not os.path.exists(registering_button_image):
                    self.update_status("Image de référence pour le bouton REGISTERING non trouvée")
                    return False
                
                if self.background_mode:
                    # En mode arrière-plan, utiliser le window_manager pour la recherche
                    all_registering_buttons = find_all_on_screen(
                        registering_button_image, 
                        confidence=0.8, 
                        window_manager=self.window_manager
                    )
                else:
                    # En mode normal, rechercher sur l'écran visible
                    all_registering_buttons = [
                        pyautogui.center(pos) for pos in list(
                            pyautogui.locateAllOnScreen(registering_button_image, confidence=0.8)
                        )
                    ]
                
                if all_registering_buttons:
                    self.update_status(f"Trouvé {len(all_registering_buttons)} boutons REGISTERING au total")
                    
                    # Filtrer pour trouver celui qui est sur la même ligne que le nom du tournoi
                    correct_button = None
                    closest_y_diff = float('inf')
                    
                    for button_center in all_registering_buttons:
                        y_diff = abs(button_center[1] - tournament_y)
                        
                        # Si ce bouton est plus proche verticalement que les précédents
                        if y_diff < closest_y_diff and y_diff < 20:  # Tolérance de 20 pixels
                            closest_y_diff = y_diff
                            correct_button = button_center
                    
                    if correct_button:
                        self.update_status(f"Bouton REGISTERING trouvé sur la même ligne à la position {correct_button}")
                        
                        # Cliquer sur le bouton correct
                        pyautogui.click(correct_button)
                        time.sleep(1)
                        
                        # Chercher le bouton ACCEPT si une confirmation est nécessaire
                        if self.background_mode:
                            accept_button = click_on_image(f"{self.images_dir}/accept_button.png", window_manager=self.window_manager)
                        else:
                            accept_button = click_on_image(f"{self.images_dir}/accept_button.png")
                        
                        if accept_button:
                            self.update_status(f"Inscription au tournoi '{self.tournament_name}' confirmée!")
                            return True
                        else:
                            self.update_status("Pas de bouton de confirmation trouvé, l'inscription peut être déjà complète")
                            return True
                    else:
                        self.update_status("Aucun bouton REGISTERING trouvé sur la même ligne que le tournoi")
                        
                        # Méthode 3: Dernière alternative - cliquer sur le tournoi puis chercher le bouton
                        self.update_status("Tentative de clic sur le tournoi puis recherche du bouton d'inscription")
                        pyautogui.click(tournament_position)
                        time.sleep(0.5)
                        
                        # Essayer à nouveau de trouver le bouton après avoir sélectionné le tournoi
                        if self.background_mode:
                            register_button = click_on_image(f"{self.images_dir}/registering_button.png", window_manager=self.window_manager)
                        else:
                            register_button = click_on_image(f"{self.images_dir}/registering_button.png")
                        
                        if register_button:
                            time.sleep(1)
                            
                            # Chercher le bouton ACCEPT si une confirmation est nécessaire
                            if self.background_mode:
                                accept_button = click_on_image(f"{self.images_dir}/accept_button.png", window_manager=self.window_manager)
                            else:
                                accept_button = click_on_image(f"{self.images_dir}/accept_button.png")
                            
                            if accept_button:
                                self.update_status(f"Inscription au tournoi '{self.tournament_name}' confirmée!")
                                return True
                            else:
                                self.update_status("Pas de bouton de confirmation trouvé, l'inscription peut être déjà complète")
                                return True
                        else:
                            self.update_status("Bouton d'inscription non trouvé après sélection du tournoi")
                            return False
                else:
                    self.update_status("Aucun bouton REGISTERING trouvé à l'écran")
                    
                    # Méthode 3: Essayer de cliquer sur le tournoi d'abord
                    self.update_status("Tentative de clic sur le tournoi puis recherche du bouton d'inscription")
                    pyautogui.click(tournament_position)
                    time.sleep(0.5)
                    
                    # Chercher le bouton après avoir sélectionné le tournoi
                    if self.background_mode:
                        register_button = click_on_image(f"{self.images_dir}/registering_button.png", window_manager=self.window_manager)
                    else:
                        register_button = click_on_image(f"{self.images_dir}/registering_button.png")
                    
                    if register_button:
                        time.sleep(1)
                        
                        # Chercher le bouton ACCEPT si une confirmation est nécessaire
                        if self.background_mode:
                            accept_button = click_on_image(f"{self.images_dir}/accept_button.png", window_manager=self.window_manager)
                        else:
                            accept_button = click_on_image(f"{self.images_dir}/accept_button.png")
                        
                        if accept_button:
                            self.update_status(f"Inscription au tournoi '{self.tournament_name}' confirmée!")
                            return True
                        else:
                            self.update_status("Pas de bouton de confirmation trouvé, l'inscription peut être déjà complète")
                            return True
                    else:
                        self.update_status("Bouton d'inscription non trouvé même après sélection du tournoi")
                        return False
        except Exception as e:
            self.update_status(f"Erreur lors de l'inscription au tournoi: {str(e)}")
            return False
    
    def scroll_tournament_list(self):
        """Fait défiler la liste des tournois vers le bas"""
        try:
            # Si en mode arrière-plan, mettre la fenêtre au premier plan avant de défiler
            if self.background_mode:
                self.focus_coinpoker_window()
            
            # Trouver la zone de la liste des tournois
            # Pour simplifier, nous utiliserons une position approximative
            
            # Cliquer dans la liste pour la mettre au premier plan
            pyautogui.click(x=400, y=500)  # Ajuster ces coordonnées selon l'interface
            
            # Faire défiler vers le bas
            pyautogui.scroll(-300)  # Valeur négative pour défiler vers le bas
            
            self.update_status("Défilement de la liste des tournois effectué")
            return True
        except Exception as e:
            self.update_status(f"Erreur lors du défilement: {str(e)}")
            return False
    
    def setup_reference_images(self, parent_window=None):
        """
        Fonction interactive pour capturer les images de référence nécessaires
        
        :param parent_window: Fenêtre parent pour les dialogues d'instruction (optionnel)
        """
        self.update_status("Configuration des images de référence...")
        
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
        
        # Fonction pour afficher les instructions dans une fenêtre modale
        def show_instruction(message, next_step):
            if parent_window:
                dialog = tk.Toplevel(parent_window)
                dialog.title("Instructions")
                dialog.geometry("550x250")
                dialog.transient(parent_window)
                dialog.grab_set()
                
                lbl = tk.Label(dialog, text=message, wraplength=530, justify="left", padx=10, pady=10)
                lbl.pack(fill="both", expand=True)
                
                btn = tk.Button(dialog, text="Prêt", command=lambda: [dialog.destroy(), next_step()])
                btn.pack(pady=10)
                
                # Centrer la fenêtre
                dialog.update_idletasks()
                width = dialog.winfo_width()
                height = dialog.winfo_height()
                x = (dialog.winfo_screenwidth() // 2) - (width // 2)
                y = (dialog.winfo_screenheight() // 2) - (height // 2)
                dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
                
                parent_window.wait_window(dialog)
            else:
                print(message)
                input("Appuyez sur Entrée quand vous êtes prêt...")
                next_step()
        
        # Définir les étapes
        def capture_logo():
            # Donner du temps à l'utilisateur pour positionner la souris
            time.sleep(2)
            logo_position = pyautogui.position()
            
            # Capture une zone autour du curseur
            logo_region = (logo_position[0] - 20, logo_position[1] - 20, 40, 40)
            logo_image = pyautogui.screenshot(region=logo_region)
            logo_image.save(f"{self.images_dir}/coinpoker_logo.png")
            
            self.update_status("Logo CoinPoker capturé")
            show_instruction("3. Positionnez votre souris sur l'onglet 'Tournaments', puis cliquez sur 'Prêt'", capture_tournaments)
        
        def capture_tournaments():
            time.sleep(2)
            tournaments_position = pyautogui.position()
            tournaments_region = (tournaments_position[0] - 50, tournaments_position[1] - 15, 100, 30)
            tournaments_image = pyautogui.screenshot(region=tournaments_region)
            tournaments_image.save(f"{self.images_dir}/tournaments_tab.png")
            
            self.update_status("Onglet Tournaments capturé")
            show_instruction(
                "4. Trouvez un tournoi avec statut 'REGISTERING', positionnez votre souris SUR LE BOUTON REGISTERING, puis cliquez sur 'Prêt'. "
                "Assurez-vous de sélectionner le bouton exact que vous souhaitez que le programme clique. "
                "Cette image servira de référence pour trouver tous les boutons REGISTERING.", 
                capture_registering
            )
        
        def capture_registering():
            time.sleep(2)
            registering_position = pyautogui.position()
            registering_region = (registering_position[0] - 50, registering_position[1] - 10, 100, 20)
            registering_image = pyautogui.screenshot(region=registering_region)
            registering_image.save(f"{self.images_dir}/registering_button.png")
            
            self.update_status("Bouton REGISTERING capturé")
            show_instruction(
                "5. Si possible, cliquez sur un tournoi pour ouvrir la fenêtre d'inscription, puis positionnez votre souris sur le bouton 'ACCEPT' et cliquez sur 'Prêt'", 
                capture_accept
            )
        
        def capture_accept():
            time.sleep(2)
            accept_position = pyautogui.position()
            accept_region = (accept_position[0] - 40, accept_position[1] - 15, 80, 30)
            accept_image = pyautogui.screenshot(region=accept_region)
            accept_image.save(f"{self.images_dir}/accept_button.png")
            
            self.update_status("Bouton ACCEPT capturé")
            
            # Capture du tournoi cible ET de sa ligne complète pour référence
            show_instruction(
                f"6. Important: Trouvez le tournoi '{self.tournament_name}' dans la liste, VÉRIFIEZ qu'il a un bouton REGISTERING disponible, "
                f"puis positionnez votre souris SUR LE NOM DU TOURNOI (pas sur le bouton), puis cliquez sur 'Prêt'. "
                f"Si plusieurs tournois portent le même nom, choisissez celui auquel vous souhaitez vous inscrire.", 
                capture_tournament
            )
        
        def capture_tournament():
            time.sleep(2)
            tournament_position = pyautogui.position()
            
            # Capturer une zone plus large autour du nom du tournoi pour une meilleure reconnaissance
            tournament_region = (tournament_position[0] - 150, tournament_position[1] - 10, 300, 20)
            tournament_image = pyautogui.screenshot(region=tournament_region)
            tournament_image.save(f"{self.images_dir}/{self.tournament_name.lower().replace(' ', '_')}.png")
            
            self.update_status(f"Tournoi '{self.tournament_name}' capturé")
            
            # Demander à l'utilisateur de localiser précisément le bouton REGISTERING sur cette ligne
            show_instruction(
                f"7. TRÈS IMPORTANT: Maintenant, positionnez votre souris sur le bouton REGISTERING qui correspond à CE MÊME tournoi "
                f"'{self.tournament_name}' (sur la même ligne), puis cliquez sur 'Prêt'. "
                f"Cette étape est cruciale pour s'assurer que le bot clique au bon endroit.", 
                lambda: capture_specific_register_button(tournament_position)
            )
        
        def capture_specific_register_button(tournament_position):
            time.sleep(2)
            register_button_position = pyautogui.position()
            
            # Enregistrer la différence horizontale entre le nom du tournoi et son bouton REGISTERING
            x_offset = register_button_position[0] - tournament_position[0]
            y_offset = register_button_position[1] - tournament_position[1]
            
            # Sauvegarder ces informations pour une utilisation future
            save_tournament_offsets(self.tournament_name, x_offset, y_offset)
            
            # Capturer l'image du bouton spécifique
            register_button_region = (register_button_position[0] - 50, register_button_position[1] - 10, 100, 20)
            register_button_image = pyautogui.screenshot(region=register_button_region)
            register_button_image.save(f"{self.images_dir}/{self.tournament_name.lower().replace(' ', '_')}_register_button.png")
            
            self.update_status(f"Bouton REGISTERING spécifique au tournoi '{self.tournament_name}' capturé")
            self.update_status(f"Offset entre le nom du tournoi et son bouton: X={x_offset}, Y={y_offset}")
            self.update_status("Configuration des images de référence terminée!")
            
            if parent_window:
                tk.messagebox.showinfo("Configuration terminée", "La configuration des images de référence est terminée avec succès!")
        
        # Démarrer le processus
        show_instruction("1. Assurez-vous que CoinPoker est ouvert et visible. Cliquez sur 'Prêt' quand vous êtes prêt...", 
                         lambda: show_instruction("2. Positionnez votre souris sur le logo CoinPoker et cliquez sur 'Prêt'", capture_logo))
    
    def run(self, max_attempts=None):
        """
        Démarre le processus de surveillance et d'inscription au tournoi
        
        :param max_attempts: Nombre maximum de tentatives (None = illimité)
        """
        self.running = True
        attempts = 0
        
        self.update_status(f"Démarrage de la surveillance pour le tournoi '{self.tournament_name}'")
        
        # Trouver et enregistrer la fenêtre CoinPoker au démarrage
        if not self.window_manager.find_coinpoker_window():
            self.update_status("Fenêtre CoinPoker non trouvée. Vérifiez que l'application est ouverte.")
            # On ne quitte pas immédiatement, on essaiera de la trouver à chaque itération
        
        while self.running and (max_attempts is None or attempts < max_attempts):
            try:
                attempts += 1
                self.update_status(f"Tentative {attempts}/{max_attempts if max_attempts else 'illimité'}")
                
                # Si nous n'avons pas encore trouvé la fenêtre, essayer à nouveau
                if not self.window_manager.window_rect and not self.window_manager.find_coinpoker_window():
                    self.update_status("Fenêtre CoinPoker non trouvée. Nouvel essai dans quelques secondes...")
                    time.sleep(self.check_interval)
                    continue
                
                # Si nous ne sommes pas en mode arrière-plan, mettre la fenêtre au premier plan
                if not self.background_mode and not self.focus_coinpoker_window():
                    self.update_status("Impossible de mettre la fenêtre CoinPoker au premier plan. Nouvel essai dans quelques secondes...")
                    time.sleep(self.check_interval)
                    continue
                
                # Naviguer vers la liste des tournois
                if not self.navigate_to_tournaments():
                    self.update_status("Navigation vers les tournois échouée. Nouvel essai dans quelques secondes...")
                    time.sleep(self.check_interval)
                    continue
                
                # Trouver le tournoi dans la liste
                tournament_position = self.find_tournament_in_list()
                
                if tournament_position:
                    self.update_status(f"Tournoi '{self.tournament_name}' trouvé à la position {tournament_position}")
                    
                    # Tenter de s'inscrire au tournoi
                    if self.register_for_tournament(tournament_position):
                        self.update_status(f"Inscription au tournoi '{self.tournament_name}' réussie!")
                        self.running = False
                        break
                    else:
                        self.update_status("Échec de l'inscription. Nouvel essai dans quelques secondes...")
                else:
                    self.update_status(f"Tournoi '{self.tournament_name}' non trouvé dans la vue actuelle.")
                    
                    # Faire défiler la liste pour chercher dans d'autres sections
                    self.scroll_tournament_list()
                
            except Exception as e:
                self.update_status(f"Erreur: {str(e)}")
            
            # Attendre avant la prochaine tentative
            if self.running:
                self.update_status(f"Prochaine vérification dans {self.check_interval} secondes...")
                time.sleep(self.check_interval)
        
        self.update_status("Surveillance terminée")
        self.running = False
    
    def stop(self):
        """Arrête le processus de surveillance"""
        self.running = False
        self.update_status("Arrêt demandé")
    
    def check_window_focus(self):
        """
        Vérifie périodiquement si la fenêtre CoinPoker est au premier plan
        et la restaure si nécessaire.
        À utiliser dans un thread séparé.
        """
        while self.running:
            if not self.background_mode and not self.window_manager.is_coinpoker_window_focused():
                self.update_status("La fenêtre CoinPoker n'est plus au premier plan, restauration...")
                self.focus_coinpoker_window()
            time.sleep(5)  # Vérifier toutes les 5 secondes
