from __future__ import annotations
import json, os, shutil, subprocess
from pathlib import Path

class BackendError(RuntimeError): pass

def command(*args: str) -> str:
    try:
        result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=15)
        return result.stdout.strip()
    except FileNotFoundError: raise BackendError(f"Command not found: {args[0]}")
    except subprocess.CalledProcessError as error: raise BackendError(error.stderr.strip() or "Backend command failed")

def outputs() -> list[str]:
    raw = command("hyprctl", "monitors", "all", "-j")
    return [monitor["name"] for monitor in json.loads(raw) if monitor.get("name")]

def available() -> list[str]:
    found = []
    if shutil.which("swww"): found.append("swww")
    if shutil.which("hyprpaper"): found.append("hyprpaper")
    return found

def detect(preferred: str = "auto") -> str:
    choices = available()
    if preferred != "auto" and preferred in choices: return preferred
    if "swww" in choices: return "swww"
    if "hyprpaper" in choices: return "hyprpaper"
    raise BackendError("Install swww or hyprpaper first.")

def apply(output: str, image: str, backend: str, transition: str = "fade") -> None:
    image = str(Path(image).expanduser().resolve())
    if not Path(image).is_file(): raise BackendError("The selected image does not exist.")
    if backend == "swww":
        command("swww", "img", image, "--outputs", output, "--transition-type", transition)
    elif backend == "hyprpaper":
        # hyprpaper IPC is supplied through hyprctl when the daemon is running.
        command("hyprctl", "hyprpaper", "preload", image)
        command("hyprctl", "hyprpaper", "wallpaper", f"{output},{image}")
    else: raise BackendError(f"Unknown backend: {backend}")
