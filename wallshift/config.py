from __future__ import annotations
import json
from pathlib import Path

ROOT = Path.home() / ".config" / "wallshift"
CONFIG = ROOT / "config.json"
THEMES = ROOT / "themes"
DEFAULT = {"backend": "auto", "wallpapers": {}, "folder": "", "interval_minutes": 30,
           "transition": "fade", "rotation_enabled": False}

def load() -> dict:
    try:
        return DEFAULT | json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT.copy()

def save(data: dict) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
