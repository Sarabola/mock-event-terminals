from app.windows.abc import DeviceWindow, Window
from app.windows.devices.settings_window import DeviceSettingsWindow
from app.windows.devices.settings_with_temperature import DeviceWithTemperatureSettingsWindow
from app.windows.select_photo import SelectPhotosWindow
from app.windows.send_status_window import SendStatusWindow
from app.devices.lunafast4a import LunaFast4ASender
from app.db import db_helper
from app.theme import COLORS, STYLES
import tkinter as tk
import json


class LunaFast4AWindow(DeviceWindow, Window):
    TERMINAL_NAME = "lunafast4a"

    def __init__(self, master, devices_window):
        DeviceWindow.__init__(self, master, devices_window)
        Window.__init__(self, master, None)
        self.sender = LunaFast4ASender()

        self.temperature_enabled = tk.BooleanVar()
        self.card_event = tk.BooleanVar()
        self._load_settings()

    def _load_settings(self):
        """Load settings from database."""
        device_data = db_helper.get_device_by_name(self.TERMINAL_NAME)
        if device_data:
            self.temperature_enabled.set(device_data.get("temperature_enabled", False))
            self.card_event.set(device_data.get("card_event", False))

    def _save_settings(self):
        """Save current settings to database."""
        device_data = db_helper.get_device_by_name(self.TERMINAL_NAME) or {}
        device_data.update({
            "temperature_enabled": self.temperature_enabled.get(),
            "card_event": self.card_event.get()
        })
        
        with open(db_helper.db_path, "r") as f:
            data = json.load(f)
        data["terminals"][self.TERMINAL_NAME] = device_data
        with open(db_helper.db_path, "w") as f:
            json.dump(data, f, indent=2)

    def open_settings(self):
        self._clear_window()
        devices_window = DeviceWithTemperatureSettingsWindow(self.master, self, self.TERMINAL_NAME)
        devices_window.show_settings()

    def select_photos(self):
        images_window = SelectPhotosWindow(self.master, self)
        images_window.show_images()

    def send_event(self):
        self._save_settings()
        
        status_window = SendStatusWindow(self.master, self.TERMINAL_NAME)

        def send_photos_callback(selected_photos, progress_callback):
            return self.sender.make_selected_photos_request(
                selected_photos, 
                progress_callback,
                temperature_enabled=self.temperature_enabled.get(),
                card_event=self.card_event.get()
            )

        status_window.show_status(send_photos_callback)

    def _create_photos_preview(self, parent_frame):
        """Create a frame to display selected photos that will be sent."""
        photos_frame = tk.Frame(parent_frame, bg=COLORS["bg_secondary"], relief="solid", borderwidth=1)
        photos_frame.pack(fill="x", pady=(20, 0))

        preview_title = tk.Label(
            photos_frame,
            text="Selected Photos for Sending:",
            **STYLES["label"]
        )
        preview_title.pack(pady=(10, 5), padx=10, anchor="w")

        self.photos_container = tk.Frame(photos_frame, bg=COLORS["bg_secondary"])
        self.photos_container.pack(fill="x", padx=10, pady=(0, 10))

        self._update_photos_preview()

    def go_back(self):
        self._clear_window()
        self.devices_window.show_devices()
