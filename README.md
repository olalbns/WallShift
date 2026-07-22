# WallShift

Gestionnaire GTK4 de fonds d’écran pour Hyprland : fond différent par écran,
rotation automatique, transitions et export de couleurs.

## Fonctions

- Fonds d’écran distincts pour chaque sortie Hyprland ;
- backends `awww`, `swww` et `hyprpaper` ;
- galerie d’aperçus d’un dossier d’images ;
- rotation automatique avec un timer systemd utilisateur ;
- export de palettes pour Hyprland, Waybar et Kitty ;
- aucune modification automatique de vos fichiers de configuration existants.

## Installation sur Arch Linux

```bash
yay -S wallshift-git
```

Installez au moins un backend. `awww` est recommandé :

```bash
sudo pacman -S awww python-pillow
```

Les alternatives sont :

```bash
sudo pacman -S swww
# ou
sudo pacman -S hyprpaper
```

## Utilisation

Démarrez le daemon awww si vous l’utilisez :

```bash
awww-daemon &
```

Lancez ensuite :

```bash
wallshift
```

1. Sélectionnez le backend et l’écran ;
2. choisissez un dossier ou une image ;
3. cliquez sur une miniature puis sur **Apply to selected output** ;
4. activez la rotation si souhaité.

Le timer est automatiquement installé lors de la sélection d’un dossier. Pour
le vérifier :

```bash
systemctl --user status wallshift-rotate.timer
```

Les couleurs exportées sont enregistrées dans :

```text
~/.config/wallshift/themes/
```
