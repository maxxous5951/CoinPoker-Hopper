# CoinPoker Tournament Hopper

CoinPoker Tournament Hopper est un outil automatisé qui permet de surveiller et de s'inscrire automatiquement à des tournois spécifiques sur la plateforme CoinPoker.

## Fonctionnalités

- Surveillance automatique des tournois
- Configuration d'images de référence pour une reconnaissance fiable
- Interface graphique conviviale
- Possibilité de configurer plusieurs tournois
- Paramètres personnalisables (intervalle de vérification, nombre de tentatives)

## Structure du projet

```
coinpoker-hopper/
├── main.py                    # Point d'entrée de l'application
├── logger.py                  # Configuration du logging
├── hopper.py                  # Classe CoinPokerHopper
├── gui.py                     # Interface graphique (HopperGUI)
├── utils/
│   ├── __init__.py
│   ├── image_utils.py         # Fonctions utilitaires pour les captures d'écran
│   └── config_utils.py        # Gestion de la configuration et des tournois
├── resources/
│   ├── images/                # Dossier pour les images de référence
│   └── screenshots/           # Dossier pour les captures d'écran
├── config/                    # Configurations sauvegardées
└── logs/                      # Fichiers de log
```

## Prérequis

- Python 3.6 ou supérieur
- Bibliothèques requises :
  - tkinter
  - pyautogui
  - pillow

## Installation

1. Clonez ce dépôt ou téléchargez les fichiers
2. Installez les bibliothèques requises :

```
pip install pyautogui pillow
```

## Utilisation

1. Exécutez l'application :

```
python main.py
```

2. Ajoutez un tournoi dans la section "Sélection du tournoi"
3. Cliquez sur "Configurer images" pour capturer les images de référence nécessaires
4. Suivez les instructions à l'écran pour configurer les images
5. Une fois la configuration terminée, ajustez les paramètres (tentatives max, intervalle)
6. Cliquez sur "Démarrer" pour lancer le hopper

## Configuration des images

La configuration des images est une étape cruciale pour le bon fonctionnement du hopper. L'assistant vous guidera pour capturer :

1. Le logo CoinPoker
2. L'onglet "Tournaments"
3. Le bouton "REGISTERING"
4. Le bouton "ACCEPT"
5. Le tournoi spécifique
6. Le bouton REGISTERING spécifique au tournoi

## Conseils d'utilisation

- Assurez-vous que CoinPoker est déjà ouvert et connecté avant de lancer le hopper
- Configurez les images de référence dans un environnement stable (même résolution, même thème)
- Évitez de déplacer la fenêtre CoinPoker pendant l'exécution du hopper
- Si le hopper ne fonctionne pas correctement, essayez de reconfigurer les images

## Dépannage

- **Le hopper ne trouve pas la fenêtre CoinPoker** : Assurez-vous que l'application est ouverte et visible
- **Le hopper ne trouve pas le tournoi** : Vérifiez que le tournoi est visible dans la liste et qu'il a le statut "REGISTERING"
- **Le hopper ne clique pas au bon endroit** : Reconfigurez les images de référence, en faisant particulièrement attention à l'étape 6 et 7 de la configuration
