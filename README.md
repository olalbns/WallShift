# WallShift

GTK4 wallpaper manager for Hyprland. It supports **swww** and **hyprpaper**,
per-output images, automatic rotation through a systemd user timer, animated
transitions with awww/swww, and safe color-theme exports for Hyprland, Waybar, and
Kitty.

## Arch dependencies

```bash
sudo pacman -S python python-gobject gtk4 python-pillow awww hyprpaper
```

Use `awww`, `swww`, or `hyprpaper`. WallShift prioritises **awww** (the modern
successor to swww), then swww, then hyprpaper. Start the selected daemon before
applying wallpapers, for example: `awww-daemon &`. Selecting a wallpaper folder
automatically preselects its first supported image; Apply can also choose an
image from that folder when none is selected.

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
