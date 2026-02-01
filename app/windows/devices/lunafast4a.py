import json
import tkinter as tk
from tkinter import messagebox

from app.config import get_logger
from app.db import db_helper
from app.devices.lunafast4a import LunaFast4ASender
from app.theme import COLORS, STYLES
from app.windows.abc import DeviceWindow, Window
from app.windows.devices.models import LunaFastData
from app.windows.devices.settings_with_temperature import \
    DeviceWithTemperatureSettingsWindow
from app.windows.select_photo import SelectPhotosWindow
from app.windows.send_status_window import SendStatusWindow


class LunaFast4AWindow(DeviceWindow, Window):
    TERMINAL_NAME = "lunafast4a"

    def __init__(self, master, devices_window):
        DeviceWindow.__init__(self, master, devices_window)
        Window.__init__(self, master, None)
        self.sender = LunaFast4ASender()

        self.card_event = tk.BooleanVar()
        self.card_number = tk.StringVar()
        self._load_settings()
        self.logger = get_logger(self.__class__.__name__)

    def show(self):
        super().show()
        self._create_card_event_frame()

    def _create_card_event_frame(self):
        """Create frame for card event settings."""
        card_frame = tk.Frame(self.master, bg=COLORS["bg_secondary"], relief="solid", borderwidth=1)
        card_frame.pack(fill="x", pady=(20, 0), padx=20)

        title_label = tk.Label(
            card_frame,
            text="Card Event Settings:",
            **STYLES["label"]
        )
        title_label.pack(pady=(10, 5), padx=10, anchor="w")

        card_checkbox = tk.Checkbutton(
            card_frame,
            text="Enable Card Event",
            variable=self.card_event,
            command=self._toggle_card_number_input,
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"],
            selectcolor=COLORS["bg_secondary"],
            font=("Arial", 10)
        )
        card_checkbox.pack(pady=5, padx=10, anchor="w")

        self.card_number_frame = tk.Frame(card_frame, bg=COLORS["bg_secondary"])
        
        card_number_label = tk.Label(
            self.card_number_frame,
            text="Card Number:",
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"],
            font=("Arial", 10)
        )
        card_number_label.pack(side="left", padx=(10, 5), pady=5)

        card_number_entry = tk.Entry(
            self.card_number_frame,
            textvariable=self.card_number,
            width=20,
            font=("Arial", 10)
        )
        card_number_entry.pack(side="left", pady=5)

        send_card_button = tk.Button(
            self.card_number_frame,
            text="Send Card",
            command=self.send_card_event,
            **STYLES["button"]
        )
        send_card_button.pack(side="left", padx=(10, 0), pady=5)

        if self.card_event.get():
            self.card_number_frame.pack(fill="x", pady=5)

    def _toggle_card_number_input(self):
        """Show or hide card number input based on card_event checkbox."""
        if self.card_event.get():
            self.card_number_frame.pack(fill="x", pady=5)
        else:
            self.card_number_frame.pack_forget()


    def _load_settings(self):
        """Load settings from database."""
        device_data = db_helper.get_device_by_name(self.TERMINAL_NAME)
        if device_data:
            self.card_event.set(device_data.get("card_event", False))
            self.card_number.set(device_data.get("card_number", ""))

    def _save_settings(self):
        """Save current settings to database."""
        device_data = db_helper.get_device_by_name(self.TERMINAL_NAME) or {}
        device_data.update({
            "card_event": self.card_event.get(),
            "card_number": self.card_number.get()
        })

        data = db_helper.get_data()
        data["terminals"][self.TERMINAL_NAME] = device_data
        with open(db_helper.db_path, "w") as f:
            json.dump(data, f, indent=2)

    def open_settings(self):
        self._clear_window()
        devices_window = DeviceWithTemperatureSettingsWindow(self.master, self, self.TERMINAL_NAME, self.sender)
        devices_window.show_settings()

    def select_photos(self):
        images_window = SelectPhotosWindow(self.master, self)
        images_window.show_images()

    def send_card_event(self):
        """Send only card event without photos."""
        self._save_settings()
        if not self.card_number.get().strip():
            messagebox.showerror("Error", "Please enter a card number")
            return
        terminal = self.get_terminal()
        self.sender.make_card_request(card=terminal.card_number)

    def send_event(self):
        self._save_settings()

        status_window = SendStatusWindow(self.master, self.TERMINAL_NAME)
        terminal = self.get_terminal()
        def send_photos_callback(selected_photos, progress_callback):
            return self.sender.make_selected_photos_request(
                faces=selected_photos,
                progress_callback=progress_callback,
                terminal_data=terminal
            )

        status_window.show_status(send_photos_callback)

    def get_terminal(self) -> LunaFastData:
        terminal_data = db_helper.get_device_by_name(self.TERMINAL_NAME)
        return LunaFastData(**terminal_data)

    def go_back(self):
        self._clear_window()
        self.devices_window.show_devices()
