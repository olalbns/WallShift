from __future__ import annotations
import argparse, os, random, shlex, sys
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
    # A systemd user service may not have Hyprland IPC variables. Reuse the
    # outputs saved by the GUI; only query Hyprland when no prior setup exists.
    target_outputs = list(data.get("wallpapers", {})) or backend.outputs()
    for output in target_outputs: backend.apply(output, chosen, engine, data["transition"])
    data["wallpapers"] = {output: chosen for output in target_outputs}; config.save(data)

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
        self.engine = Gtk.ComboBoxText(); engines = ("auto", "awww", "swww", "hyprpaper"); [self.engine.append_text(item) for item in engines]; self.engine.set_active(engines.index(self.data["backend"]) if self.data["backend"] in engines else 0)
        self.transition = Gtk.ComboBoxText(); [self.transition.append_text(item) for item in ("fade", "wipe", "grow", "outer", "none")]; self.transition.set_active(("fade", "wipe", "grow", "outer", "none").index(self.data.get("transition", "fade")))
        for row, (label, widget) in enumerate((("Output", self.output), ("Backend", self.engine), ("Transition", self.transition))):
            form.attach(Gtk.Label(label=label, xalign=0), 0, row, 1, 1); form.attach(widget, 1, row, 1, 1)
        choose = Gtk.Button(label="Choose image…"); choose.connect("clicked", self.choose_image); form.attach(choose, 0, 3, 2, 1)
        self.preview = Gtk.Picture.new_for_filename(self.data["wallpapers"].get(self.current_output(), "")); self.preview.set_can_shrink(True); self.preview.set_content_fit(Gtk.ContentFit.CONTAIN); self.preview.set_size_request(-1, 220); root.append(self.preview)
        gallery_frame = Gtk.Frame(label="Images in selected folder")
        scroll = Gtk.ScrolledWindow(min_content_height=160, vexpand=True)
        self.gallery = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, max_children_per_line=5, row_spacing=6, column_spacing=6, margin_top=8, margin_bottom=8, margin_start=8, margin_end=8)
        scroll.set_child(self.gallery); gallery_frame.set_child(scroll); root.append(gallery_frame)
        row = Gtk.Box(spacing=8); root.append(row)
        apply_button = Gtk.Button(label="Apply to selected output"); apply_button.add_css_class("suggested-action"); apply_button.connect("clicked", self.apply); row.append(apply_button)
        export_button = Gtk.Button(label="Export theme colors"); export_button.connect("clicked", self.export); row.append(export_button)
        rotation = Gtk.Frame(label="Automatic rotation"); root.append(rotation)
        box = Gtk.Box(spacing=10, margin_top=10, margin_bottom=10, margin_start=10, margin_end=10); rotation.set_child(box)
        self.folder = Gtk.Entry(hexpand=True, placeholder_text="Wallpaper folder"); self.folder.set_text(self.data["folder"]); box.append(self.folder)
        folder_button = Gtk.Button(label="Choose folder…"); folder_button.connect("clicked", self.choose_folder); box.append(folder_button)
        self.minutes = Gtk.SpinButton.new_with_range(1, 1440, 1); self.minutes.set_value(self.data["interval_minutes"]); self.minutes.connect("value-changed", self.interval_changed); box.append(self.minutes)
        self.rotation_enabled = Gtk.Switch(active=self.data.get("rotation_enabled", False), valign=Gtk.Align.CENTER)
        self.rotation_enabled.connect("state-set", self.rotation_changed)
        box.append(Gtk.Label(label="Rotation active")); box.append(self.rotation_enabled)
        self.refresh_gallery()
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
        if response == Gtk.ResponseType.ACCEPT and (file := dialog.get_file()): self.select_image(file.get_path() or "")
        dialog.destroy()
    def select_image(self, image):
        self.image = image; self.preview.set_filename(image); self.status.set_text(Path(image).name)
    def choose_folder(self, _button):
        dialog = Gtk.FileChooserNative(title="Choose wallpaper folder", transient_for=self, action=Gtk.FileChooserAction.SELECT_FOLDER, accept_label="Select")
        dialog.connect("response", self.on_folder); dialog.show()
    def on_folder(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT and (file := dialog.get_file()):
            folder = file.get_path() or ""
            self.folder.set_text(folder)
            # A folder is immediately useful: preselect its first image so the
            # Apply button never forces the user through a second chooser.
            candidates = images(folder)
            if candidates:
                self.select_image(str(candidates[0]))
                self.refresh_gallery()
                # Folder selection enables persistence automatically; no
                # second "install timer" action is required.
                self.rotation_enabled.set_active(True)
                self.configure_timer()
                self.status.set_text(f"Selected {candidates[0].name}; rotation timer enabled.")
            else:
                self.refresh_gallery()
                self.status.set_text("No supported image found in this folder.")
        dialog.destroy()
    def refresh_gallery(self):
        while (child := self.gallery.get_first_child()) is not None: self.gallery.remove(child)
        for image in images(self.folder.get_text())[:120]:
            button = Gtk.Button(tooltip_text=image.name)
            thumbnail = Gtk.Picture.new_for_filename(str(image)); thumbnail.set_content_fit(Gtk.ContentFit.COVER); thumbnail.set_size_request(112, 76)
            button.set_child(thumbnail); button.connect("clicked", lambda _button, path=str(image): self.select_image(path))
            self.gallery.append(button)
    def settings(self):
        self.data.update({"backend": self.engine.get_active_text() or "auto", "folder": self.folder.get_text(), "interval_minutes": int(self.minutes.get_value()), "transition": self.transition.get_active_text() or "fade", "rotation_enabled": self.rotation_enabled.get_active()}); config.save(self.data)
    def apply(self, _button):
        try:
            self.settings()
            # Selecting a folder is enough: choose a random image if no single
            # image was explicitly picked. This is also convenient for rotation.
            if not self.image:
                candidates = images(self.data["folder"])
                if not candidates: raise backend.BackendError("Choose an image or a folder containing images.")
                self.image = str(random.choice(candidates)); self.preview.set_filename(self.image)
            output = self.current_output(); backend.apply(output, self.image, backend.detect(self.data["backend"]), self.data["transition"])
            self.data["wallpapers"][output] = self.image; config.save(self.data)
            if self.rotation_enabled.get_active() and self.data["folder"]: self.configure_timer()
            self.status.set_text(f"Applied to {output}.")
        except (backend.BackendError, RuntimeError) as error: self.status.set_text(f"Error: {error}")
    def export(self, _button):
        try:
            if not self.image:
                candidates = images(self.folder.get_text())
                if not candidates: raise RuntimeError("Choose an image or a folder containing images.")
                self.image = str(candidates[0]); self.preview.set_filename(self.image)
            self.status.set_text(f"Theme files exported to {themes.export(self.image)}")
        except RuntimeError as error: self.status.set_text(f"Error: {error}")
    def rotation_changed(self, _switch, enabled):
        if enabled: self.configure_timer()
        else:
            try: backend.command("systemctl", "--user", "disable", "--now", "wallshift-rotate.timer")
            except backend.BackendError: pass
        return False
    def interval_changed(self, _spin):
        if self.rotation_enabled.get_active() and self.folder.get_text(): self.configure_timer()
    def configure_timer(self):
        """Write, reload, and enable the timer without a separate user action."""
        try:
            self.settings()
            unit = Path.home()/".config/systemd/user"; unit.mkdir(parents=True, exist_ok=True)
            source_root = Path(__file__).resolve().parent.parent
            environment = f"Environment=PYTHONPATH={source_root}\n" if (source_root / "pyproject.toml").is_file() else ""
            executable = f"{shlex.quote(sys.executable)} -m wallshift.app --rotate"
            (unit/"wallshift-rotate.service").write_text(f"[Unit]\nDescription=WallShift rotation\n[Service]\nType=oneshot\n{environment}ExecStart={executable}\n")
            (unit/"wallshift-rotate.timer").write_text(f"[Unit]\nDescription=WallShift rotation\n[Timer]\nOnActiveSec=15s\nOnUnitActiveSec={int(self.minutes.get_value())}min\nPersistent=true\n[Install]\nWantedBy=timers.target\n")
            # Pass the Wayland/Hyprland session variables to the user manager.
            names = [name for name in ("WAYLAND_DISPLAY", "XDG_RUNTIME_DIR", "HYPRLAND_INSTANCE_SIGNATURE") if os.environ.get(name)]
            if names: backend.command("systemctl", "--user", "import-environment", *names)
            backend.command("systemctl", "--user", "daemon-reload"); backend.command("systemctl", "--user", "enable", "--now", "wallshift-rotate.timer")
        except backend.BackendError as error: self.status.set_text(f"Timer error: {error}")

class App(Gtk.Application):
    def __init__(self): super().__init__(application_id=APP_ID)
    def do_activate(self): (self.props.active_window or Window(self)).present()
def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--rotate", action="store_true"); args = parser.parse_args()
    if args.rotate: rotate()
    else: App().run(None)
if __name__ == "__main__": main()
