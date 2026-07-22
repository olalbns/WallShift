# WallShift

GTK4 wallpaper manager for Hyprland. It supports **swww** and **hyprpaper**,
per-output images, automatic rotation through a systemd user timer, animated
transitions with swww, and safe color-theme exports for Hyprland, Waybar, and
Kitty.

## Arch dependencies

```bash
sudo pacman -S python python-gobject gtk4 python-pillow swww hyprpaper
```

Use either `swww` or `hyprpaper`. WallShift prioritises swww when both are
available. Start the selected daemon before applying wallpapers.

## Run from source

```bash
PYTHONPATH=. python -m wallshift.app
```

## Theme exports

WallShift writes files—without altering existing configuration—to:

```text
~/.config/wallshift/themes/
```

Import `hyprland-colors.conf`, `waybar-colors.css`, or `kitty-colors.conf`
from your own configuration.
