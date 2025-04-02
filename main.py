#!/usr/bin/env python3
"""
Point d'entrée principal de l'application CoinPoker Tournament Hopper
"""

import tkinter as tk
from gui import HopperGUI
import os
from logger import setup_logging

def main():
    """Fonction principale pour démarrer l'application"""
    # Configuration du logging
    setup_logging()

    # Création des dossiers requis s'ils n'existent pas
    os.makedirs("resources/images", exist_ok=True)
    os.makedirs("resources/screenshots", exist_ok=True)

    # Lancement de l'interface graphique
    root = tk.Tk()
    app = HopperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
