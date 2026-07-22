from __future__ import annotations
from pathlib import Path
from .config import THEMES

def palette(image: str) -> list[str]:
    try:
        from PIL import Image
    except ImportError as error:
        raise RuntimeError("Install python-pillow to extract theme colors.") from error
    with Image.open(image) as source:
        source = source.convert("RGB"); source.thumbnail((160, 160))
        colors = source.quantize(colors=8, method=Image.Quantize.MEDIANCUT).convert("RGB").getcolors(160*160) or []
    colors.sort(reverse=True)
    return ["#%02x%02x%02x" % rgb for _count, rgb in colors[:6]]

def export(image: str) -> Path:
    colors = palette(image)
    while len(colors) < 6: colors.append("#808080")
    THEMES.mkdir(parents=True, exist_ok=True)
    values = {"background": colors[0], "foreground": colors[1], "accent": colors[2], "accent2": colors[3], "muted": colors[4], "urgent": colors[5]}
    (THEMES / "hyprland-colors.conf").write_text("\n".join(f"${name} = rgb({value[1:]})" for name, value in values.items()) + "\n")
    (THEMES / "waybar-colors.css").write_text(":root {\n" + "\n".join(f"  --wallshift-{name}: {value};" for name, value in values.items()) + "\n}\n")
    (THEMES / "kitty-colors.conf").write_text("\n".join((f"background {values['background']}", f"foreground {values['foreground']}", f"color4 {values['accent']}", f"color6 {values['accent2']}", f"color8 {values['muted']}", f"color1 {values['urgent']}")) + "\n")
    return THEMES
