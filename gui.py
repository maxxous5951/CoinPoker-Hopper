"""
Interface graphique pour l'application CoinPoker Tournament Hopper
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from datetime import datetime

from hopper import CoinPokerHopper
from utils.config_utils import load_tournaments, save_tournaments

logger = logging.getLogger("coinpoker_hopper")

class HopperGUI:
    def __init__(self, root):
        """
        Initialise l'interface graphique
        
        :param root: Fenêtre racine de Tkinter
        """
        self.root = root
        self.root.title("CoinPoker Tournament Hopper")
        self.root.geometry("550x480")  # Plus grand pour accueillir la nouvelle option
        self.root.resizable(True, True)
        
        self.hopper = None
        self.hopper_thread = None
        self.window_check_thread = None
        
        self.create_widgets()
        self.load_tournaments()
    
    def create_widgets(self):
        """Crée les widgets de l'interface utilisateur"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Section tournoi
        tournament_frame = ttk.LabelFrame(main_frame, text="Sélection du tournoi", padding="10")
        tournament_frame.pack(fill="x", padx=5, pady=5)
        
        # Combobox pour la sélection du tournoi
        ttk.Label(tournament_frame, text="Tournoi :").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.tournament_var = tk.StringVar()
        self.tournament_combobox = ttk.Combobox(tournament_frame, textvariable=self.tournament_var, width=30)
        self.tournament_combobox.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        # Nouveau tournoi
        ttk.Label(tournament_frame, text="Nouveau :").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.new_tournament_var = tk.StringVar()
        new_tournament_entry = ttk.Entry(tournament_frame, textvariable=self.new_tournament_var, width=30)
        new_tournament_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        # Boutons pour gérer les tournois
        buttons_frame = ttk.Frame(tournament_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=5)
        
        ttk.Button(buttons_frame, text="Ajouter", command=self.add_tournament).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Supprimer", command=self.delete_tournament).pack(side="left", padx=5)
        
        # Section contrôles
        self.controls_frame = ttk.LabelFrame(main_frame, text="Contrôles", padding="10")
        self.controls_frame.pack(fill="x", padx=5, pady=5)
        
        # Nombre de tentatives
        ttk.Label(self.controls_frame, text="Tentatives max :").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.attempts_var = tk.StringVar(value="30")
        attempts_entry = ttk.Entry(self.controls_frame, textvariable=self.attempts_var, width=10)
        attempts_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(self.controls_frame, text="(0 = illimité)").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        
        # Intervalle de vérification
        ttk.Label(self.controls_frame, text="Intervalle (s) :").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.interval_var = tk.StringVar(value="5")
        interval_entry = ttk.Entry(self.controls_frame, textvariable=self.interval_var, width=10)
        interval_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        # Options de surveillance de la fenêtre
        options_frame = ttk.Frame(self.controls_frame)
        options_frame.grid(row=2, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        
        # Mode arrière-plan (détection même sans avoir le focus)
        self.background_mode_var = tk.BooleanVar(value=True)
        background_mode_check = ttk.Checkbutton(
            options_frame, 
            text="Détecter les tournois même lorsque la fenêtre est en arrière-plan",
            variable=self.background_mode_var,
            command=self.toggle_background_mode
        )
        background_mode_check.pack(anchor="w", pady=2)
        
        # Surveillance automatique du focus
        self.window_check_var = tk.BooleanVar(value=True)
        window_check = ttk.Checkbutton(
            options_frame, 
            text="Surveiller et restaurer la fenêtre CoinPoker automatiquement",
            variable=self.window_check_var
        )
        window_check.pack(anchor="w", pady=2)
        
        # Info bulle explicative
        info_text = "Le mode arrière-plan permet de détecter les tournois même lorsque la fenêtre CoinPoker est cachée\n" \
                   "derrière d'autres fenêtres. La fenêtre sera remise au premier plan uniquement lorsqu'une\n" \
                   "action est nécessaire (clic sur le bouton d'inscription)."
        info_label = ttk.Label(options_frame, text=info_text, foreground="gray")
        info_label.pack(anchor="w", pady=5)
        
        # Boutons de contrôle
        control_buttons_frame = ttk.Frame(self.controls_frame)
        control_buttons_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        self.start_button = ttk.Button(control_buttons_frame, text="Démarrer", command=self.start_hopper)
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = ttk.Button(control_buttons_frame, text="Arrêter", command=self.stop_hopper, state="disabled")
        self.stop_button.pack(side="left", padx=5)
        
        self.setup_button = ttk.Button(control_buttons_frame, text="Configurer images", command=self.setup_images)
        self.setup_button.pack(side="left", padx=5)
        
        # Section statut
        status_frame = ttk.LabelFrame(main_frame, text="Statut", padding="10")
        status_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Zone de texte pour le statut
        self.status_text = tk.Text(status_frame, height=10, width=50, wrap="word")
        self.status_text.pack(side="left", fill="both", expand=True)
        
        # Scrollbar pour la zone de texte
        scrollbar = ttk.Scrollbar(status_frame, command=self.status_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.status_text.config(yscrollcommand=scrollbar.set)
        
        # Ajouter un message initial
        self.update_status("Prêt à démarrer. Sélectionnez un tournoi et configurez les paramètres.")
    
    def toggle_background_mode(self):
        """Active ou désactive le mode de détection en arrière-plan"""
        if hasattr(self, 'hopper') and self.hopper:
            # Mettre à jour le mode de détection sur le hopper existant
            background_mode = self.background_mode_var.get()
            self.hopper.set_background_mode(background_mode)
            self.update_status(f"Mode de détection en arrière-plan {'activé' if background_mode else 'désactivé'}")
    
    def update_status(self, message):
        """Met à jour la zone de statut avec un nouveau message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert("end", f"[{timestamp}] {message}\n")
        self.status_text.see("end")  # Défiler jusqu'à la fin
        
        # Mettre à jour l'interface
        self.root.update_idletasks()
    
    def load_tournaments(self):
        """Charge la liste des tournois depuis le fichier de configuration"""
        tournaments = load_tournaments()
        if tournaments:
            self.tournament_combobox['values'] = tournaments
            self.tournament_combobox.current(0)
    
    def add_tournament(self):
        """Ajoute un nouveau tournoi à la liste"""
        new_tournament = self.new_tournament_var.get().strip()
        
        if not new_tournament:
            messagebox.showwarning("Champ vide", "Veuillez entrer un nom de tournoi.")
            return
        
        # Obtenir la liste actuelle et ajouter le nouveau tournoi
        tournaments = list(self.tournament_combobox['values'])
        
        if new_tournament not in tournaments:
            tournaments.append(new_tournament)
            self.tournament_combobox['values'] = tournaments
            self.tournament_combobox.set(new_tournament)
            self.new_tournament_var.set("")
            save_tournaments(tournaments)
            self.update_status(f"Tournoi '{new_tournament}' ajouté à la liste.")
        else:
            messagebox.showinfo("Information", "Ce tournoi existe déjà dans la liste.")
    
    def delete_tournament(self):
        """Supprime le tournoi sélectionné de la liste"""
        selected_tournament = self.tournament_var.get().strip()
        
        if not selected_tournament:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner un tournoi à supprimer.")
            return
        
        # Confirmer la suppression
        if messagebox.askyesno("Confirmation", f"Voulez-vous vraiment supprimer le tournoi '{selected_tournament}' ?"):
            # Obtenir la liste actuelle et supprimer le tournoi
            tournaments = list(self.tournament_combobox['values'])
            
            if selected_tournament in tournaments:
                tournaments.remove(selected_tournament)
                self.tournament_combobox['values'] = tournaments
                
                if tournaments:
                    self.tournament_combobox.current(0)
                else:
                    self.tournament_var.set("")
                
                save_tournaments(tournaments)
                self.update_status(f"Tournoi '{selected_tournament}' supprimé de la liste.")
    
    def setup_images(self):
        """Lance la configuration des images de référence"""
        selected_tournament = self.tournament_var.get().strip()
        
        if not selected_tournament:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner un tournoi pour configurer les images.")
            return
        
        # Initialiser le hopper avec le tournoi sélectionné
        self.hopper = CoinPokerHopper(selected_tournament)
        self.hopper.set_status_callback(self.update_status)
        self.hopper.set_background_mode(self.background_mode_var.get())
        
        # Lancer la configuration des images
        self.hopper.setup_reference_images(self.root)
    
    def start_hopper(self):
        """Démarre le hopper dans un thread séparé"""
        selected_tournament = self.tournament_var.get().strip()
        
        if not selected_tournament:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner un tournoi.")
            return
        
        # Obtenir les paramètres
        try:
            max_attempts = int(self.attempts_var.get().strip())
            if max_attempts <= 0:
                max_attempts = None
        except ValueError:
            messagebox.showwarning("Paramètre invalide", "Le nombre de tentatives doit être un nombre entier.")
            return
        
        try:
            check_interval = float(self.interval_var.get().strip())
            if check_interval <= 0:
                messagebox.showwarning("Paramètre invalide", "L'intervalle doit être un nombre positif.")
                return
        except ValueError:
            messagebox.showwarning("Paramètre invalide", "L'intervalle doit être un nombre.")
            return
        
        # Initialiser le hopper avec le tournoi sélectionné
        self.hopper = CoinPokerHopper(selected_tournament)
        self.hopper.set_status_callback(self.update_status)
        self.hopper.check_interval = check_interval
        
        # Configurer le mode de détection en arrière-plan
        background_mode = self.background_mode_var.get()
        self.hopper.set_background_mode(background_mode)
        self.update_status(f"Mode de détection en arrière-plan {'activé' if background_mode else 'désactivé'}")
        
        # Démarrer le hopper dans un thread séparé
        self.hopper_thread = threading.Thread(target=self.hopper.run, args=(max_attempts,))
        self.hopper_thread.daemon = True
        self.hopper_thread.start()
        
        # Si l'option est activée, démarrer le thread de surveillance de la fenêtre
        if self.window_check_var.get() and not background_mode:
            self.window_check_thread = threading.Thread(target=self.hopper.check_window_focus)
            self.window_check_thread.daemon = True
            self.window_check_thread.start()
            self.update_status("Surveillance automatique de la fenêtre CoinPoker activée")
        
        # Mettre à jour l'interface
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.setup_button.config(state="disabled")
        
        self.update_status(f"Hopper démarré pour le tournoi '{selected_tournament}'.")
    
    def stop_hopper(self):
        """Arrête le hopper en cours d'exécution"""
        if self.hopper and hasattr(self.hopper, 'running') and self.hopper.running:
            self.hopper.stop()
            
            # Mettre à jour l'interface
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.setup_button.config(state="normal")
            
            self.update_status("Demande d'arrêt du hopper envoyée.")
