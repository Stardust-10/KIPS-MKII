import subprocess
import signal
from datetime import datetime

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class CameraApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Camera")

        self.set_default_size(360, 140)
        self.set_resizable(False)
        self.set_border_width(12)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_decorated(True)

        self.preview_proc = None

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(box)

        self.status_label = Gtk.Label(label="Starting preview...")
        box.pack_start(self.status_label, False, False, 0)

        self.capture_button = Gtk.Button(label="Take Picture")
        self.capture_button.connect("clicked", self.take_picture)
        box.pack_start(self.capture_button, True, True, 0)

        self.stop_button = Gtk.Button(label="Close Camera")
        self.stop_button.connect("clicked", self.close_camera)
        box.pack_start(self.stop_button, True, True, 0)

        self.connect("destroy", self.on_destroy)

        self.start_preview()

    def start_preview(self):
        if self.preview_proc is not None and self.preview_proc.poll() is None:
            return

        try:
            self.preview_proc = subprocess.Popen([
                "rpicam-hello",
                "-t", "0",
                "--hflip",
                "--vflip",
            ])
            self.status_label.set_text("Preview running")
        except Exception as e:
            self.status_label.set_text(f"Preview failed: {e}")
            print(f"Failed to start preview: {e}")

    def stop_preview(self):
        if self.preview_proc is not None:
            try:
                if self.preview_proc.poll() is None:
                    self.preview_proc.send_signal(signal.SIGINT)
                    self.preview_proc.wait(timeout=3)
            except Exception as e:
                print(f"Error stopping preview: {e}")
            self.preview_proc = None

    def take_picture(self, button=None):
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"/home/kips/KIPS-MKII/KIPS-MKII/gui_shit/shot_{timestamp}.jpg"

        self.status_label.set_text("Capturing...")

        was_running = self.preview_proc is not None and self.preview_proc.poll() is None
        if was_running:
            self.stop_preview()

        try:
            subprocess.run([
                "rpicam-jpeg",
                "-o", filename,
                "-n",
                "--hflip",
                "--vflip",
            ], check=True)

            self.status_label.set_text(f"Saved: {filename}")
            print(f"Photo saved as {filename}")

        except Exception as e:
            self.status_label.set_text("Capture failed")
            print(f"Failed to capture photo: {e}")

        if was_running:
            self.start_preview()

    def close_camera(self, button=None):
        self.stop_preview()
        self.destroy()

    def on_destroy(self, widget):
        self.stop_preview()
        Gtk.main_quit()


if __name__ == "__main__":
    win = CameraApp()
    win.show_all()
    Gtk.main()
