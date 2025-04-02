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

from utils.image_utils import take_screenshot, find_on_screen, click_on_image
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
        
        # Créer les dossiers nécessaires s'ils n'existent pas
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
    
    def set_status_callback(self, callback):
        """Définit une fonction de rappel pour mettre à jour le statut dans l'interface"""
        self.status_callback = callback
    
    def update_status(self, message):
        """Met à jour le statut dans l'interface si une fonction de rappel est définie"""
        if self.status_callback:
            self.status_callback(message)
        logger.info(message)
    
    def focus_coinpoker_window(self):
        """Tente de mettre la fenêtre CoinPoker au premier plan"""
        try:
            # Chercher le logo CoinPoker ou la barre de titre
            coinpoker_logo = find_on_screen(f"{self.images_dir}/coinpoker_logo.png")
            
            if coinpoker_logo:
                pyautogui.click(coinpoker_logo)
                self.update_status("Fenêtre CoinPoker mise au premier plan")
                return True
            else:
                self.update_status("Impossible de trouver la fenêtre CoinPoker")
                return False
        except Exception as e:
            self.update_status(f"Erreur lors de la mise au premier plan: {str(e)}")
            return False
    
    def navigate_to_tournaments(self):
        """Navigue vers l'onglet des tournois"""
        try:
            # Cliquer sur l'onglet Tournaments
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
            # Prendre une capture d'écran pour l'analyse
            screenshot_path = take_screenshot(directory=self.screenshots_dir)
            
            # Chercher toutes les occurrences du nom du tournoi
            tournament_image = f"{self.images_dir}/{self.tournament_name.lower().replace(' ', '_')}.png"
            
            if not os.path.exists(tournament_image):
                self.update_status(f"Image de référence pour le tournoi '{self.tournament_name}' non trouvée")
                return None
                
            tournament_positions = list(pyautogui.locateAllOnScreen(tournament_image, confidence=0.8))
            
            if not tournament_positions:
                self.update_status(f"Tournoi '{self.tournament_name}' non trouvé dans la liste actuelle")
                return None
                
            self.update_status(f"Trouvé {len(tournament_positions)} occurrences du tournoi '{self.tournament_name}'")
            
            # Pour chaque occurrence du tournoi, vérifier si un bouton REGISTERING est disponible sur la même ligne
            for tournament_pos in tournament_positions:
                tournament_center = pyautogui.center(tournament_pos)
                tournament_y = tournament_center[1]
                
                self.update_status(f"Vérification de l'occurrence à la position {tournament_center}")
                
                # Vérifier s'il existe des offsets spécifiques pour ce tournoi
                offsets = load_tournament_offsets(self.tournament_name)
                
                if offsets:
                    # Utiliser les offsets préconfigurés pour vérifier si le bouton est disponible
                    expected_button_x = tournament_center[0] + offsets["x_offset"]
                    expected_button_y = tournament_center[1] + offsets["y_offset"]
                    
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
                    
                all_registering_buttons = list(pyautogui.locateAllOnScreen(registering_button_image, confidence=0.8))
                
                if all_registering_buttons:
                    # Trouver le bouton le plus proche sur la même ligne (± 20 pixels)
                    for button in all_registering_buttons:
                        button_center = pyautogui.center(button)
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
                    
                all_registering_buttons = list(pyautogui.locateAllOnScreen(registering_button_image, confidence=0.8))
                
                if all_registering_buttons:
                    self.update_status(f"Trouvé {len(all_registering_buttons)} boutons REGISTERING au total")
                    
                    # Filtrer pour trouver celui qui est sur la même ligne que le nom du tournoi
                    correct_button = None
                    closest_y_diff = float('inf')
                    
                    for button in all_registering_buttons:
                        button_center = pyautogui.center(button)
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
                        register_button = click_on_image(f"{self.images_dir}/registering_button.png")
                        
                        if register_button:
                            time.sleep(1)
                            
                            # Chercher le bouton ACCEPT si une confirmation est nécessaire
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
                    register_button = click_on_image(f"{self.images_dir}/registering_button.png")
                    
                    if register_button:
                        time.sleep(1)
                        
                        # Chercher le bouton ACCEPT si une confirmation est nécessaire
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
