from __future__ import annotations
import argparse, random
from pathlib import Path
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib
from . import backend, config, themes

APP_ID = "io.github.olalbns.wallshift"
IMAGE_FILTER = ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp")

def images(folder: str) -> list[Path]:
    directory = Path(folder).expanduser()
    return sorted([entry for entry in directory.iterdir() if entry.is_file() and entry.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}]) if directory.is_dir() else []

def rotate() -> None:
    data = config.load(); candidates = images(data["folder"])
    if not candidates: return
    chosen = str(random.choice(candidates)); engine = backend.detect(data["backend"])
    for output in backend.outputs(): backend.apply(output, chosen, engine, data["transition"])
    data["wallpapers"] = {output: chosen for output in backend.outputs()}; config.save(data)

class Window(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="WallShift")
        self.data = config.load(); self.image = ""
        self.set_default_size(650, 600)
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=18, margin_bottom=18, margin_start=18, margin_end=18)
        self.set_child(root)
        title = Gtk.Label(label="WallShift", xalign=0); title.add_css_class("title-1"); root.append(title)
        subtitle = Gtk.Label(label="Wallpapers, rotation, transitions, and exported color themes", xalign=0); subtitle.add_css_class("dim-label"); root.append(subtitle)
        form = Gtk.Grid(column_spacing=12, row_spacing=10); root.append(form)
        self.output = Gtk.ComboBoxText(); self.reload_outputs()
        self.engine = Gtk.ComboBoxText(); [self.engine.append_text(item) for item in ("auto", "swww", "hyprpaper")]; self.engine.set_active(("auto", "swww", "hyprpaper").index(self.data["backend"]))
        self.transition = Gtk.ComboBoxText(); [self.transition.append_text(item) for item in ("fade", "wipe", "grow", "outer", "none")]; self.transition.set_active(("fade", "wipe", "grow", "outer", "none").index(self.data.get("transition", "fade")))
        for row, (label, widget) in enumerate((("Output", self.output), ("Backend", self.engine), ("Transition", self.transition))):
            form.attach(Gtk.Label(label=label, xalign=0), 0, row, 1, 1); form.attach(widget, 1, row, 1, 1)
        choose = Gtk.Button(label="Choose image…"); choose.connect("clicked", self.choose_image); form.attach(choose, 0, 3, 2, 1)
        self.preview = Gtk.Picture.new_for_filename(self.data["wallpapers"].get(self.current_output(), "")); self.preview.set_can_shrink(True); self.preview.set_content_fit(Gtk.ContentFit.CONTAIN); self.preview.set_size_request(-1, 260); root.append(self.preview)
        row = Gtk.Box(spacing=8); root.append(row)
        apply_button = Gtk.Button(label="Apply to selected output"); apply_button.add_css_class("suggested-action"); apply_button.connect("clicked", self.apply); row.append(apply_button)
        export_button = Gtk.Button(label="Export theme colors"); export_button.connect("clicked", self.export); row.append(export_button)
        rotation = Gtk.Frame(label="Automatic rotation"); root.append(rotation)
        box = Gtk.Box(spacing=10, margin_top=10, margin_bottom=10, margin_start=10, margin_end=10); rotation.set_child(box)
        self.folder = Gtk.Entry(hexpand=True, placeholder_text="Wallpaper folder"); self.folder.set_text(self.data["folder"]); box.append(self.folder)
        folder_button = Gtk.Button(label="Choose folder…"); folder_button.connect("clicked", self.choose_folder); box.append(folder_button)
        self.minutes = Gtk.SpinButton.new_with_range(1, 1440, 1); self.minutes.set_value(self.data["interval_minutes"]); box.append(self.minutes)
        timer_button = Gtk.Button(label="Install systemd timer"); timer_button.connect("clicked", self.install_timer); box.append(timer_button)
        self.status = Gtk.Label(label="Ready.", xalign=0, wrap=True); self.status.add_css_class("dim-label"); root.append(self.status)
    def current_output(self): return self.output.get_active_text() or ""
    def reload_outputs(self):
        try: names = backend.outputs()
        except Exception: names = []
        for name in names: self.output.append_text(name)
        if names: self.output.set_active(0)
    def choose_image(self, _button):
        dialog = Gtk.FileChooserNative(title="Choose wallpaper", transient_for=self, action=Gtk.FileChooserAction.OPEN, accept_label="Select")
        filters = Gtk.FileFilter(); filters.set_name("Images"); filters.add_mime_type("image/*"); dialog.add_filter(filters)
        dialog.connect("response", self.on_image); dialog.show()
    def on_image(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT and (file := dialog.get_file()):
            self.image = file.get_path() or ""; self.preview.set_filename(self.image); self.status.set_text(self.image)
        dialog.destroy()
    def choose_folder(self, _button):
        dialog = Gtk.FileChooserNative(title="Choose wallpaper folder", transient_for=self, action=Gtk.FileChooserAction.SELECT_FOLDER, accept_label="Select")
        dialog.connect("response", self.on_folder); dialog.show()
    def on_folder(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT and (file := dialog.get_file()): self.folder.set_text(file.get_path() or "")
        dialog.destroy()
    def settings(self):
        self.data.update({"backend": self.engine.get_active_text() or "auto", "folder": self.folder.get_text(), "interval_minutes": int(self.minutes.get_value()), "transition": self.transition.get_active_text() or "fade"}); config.save(self.data)
    def apply(self, _button):
        try:
            if not self.image: raise backend.BackendError("Choose an image first.")
            self.settings(); output = self.current_output(); backend.apply(output, self.image, backend.detect(self.data["backend"]), self.data["transition"])
            self.data["wallpapers"][output] = self.image; config.save(self.data); self.status.set_text(f"Applied to {output}.")
        except (backend.BackendError, RuntimeError) as error: self.status.set_text(f"Error: {error}")
    def export(self, _button):
        try:
            if not self.image: raise RuntimeError("Choose an image first.")
            self.status.set_text(f"Theme files exported to {themes.export(self.image)}")
        except RuntimeError as error: self.status.set_text(f"Error: {error}")
    def install_timer(self, _button):
        try:
            self.settings(); unit = Path.home()/".config/systemd/user"; unit.mkdir(parents=True, exist_ok=True)
            (unit/"wallshift-rotate.service").write_text("[Service]\nType=oneshot\nExecStart=/usr/bin/wallshift --rotate\n")
            (unit/"wallshift-rotate.timer").write_text(f"[Unit]\nDescription=WallShift rotation\n[Timer]\nOnBootSec=2min\nOnUnitActiveSec={int(self.minutes.get_value())}min\n[Install]\nWantedBy=timers.target\n")
            backend.command("systemctl", "--user", "daemon-reload"); backend.command("systemctl", "--user", "enable", "--now", "wallshift-rotate.timer")
            self.status.set_text("Rotation timer installed.")
        except backend.BackendError as error: self.status.set_text(f"Error: {error}")
class App(Gtk.Application):
    def __init__(self): super().__init__(application_id=APP_ID)
    def do_activate(self): (self.props.active_window or Window(self)).present()
def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--rotate", action="store_true"); args = parser.parse_args()
    if args.rotate: rotate()
    else: App().run(None)
if __name__ == "__main__": main()
