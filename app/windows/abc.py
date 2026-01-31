import tkinter as tk
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from app.theme import COLORS, STYLES

if TYPE_CHECKING:
    from .devices_window import DevicesWindow


class DeviceWindow(ABC):

    def __init__(self, master, devices_window: "DevicesWindow"):
        self.master = master
        self.devices_window = devices_window

    def show(self):
        self.master.configure(bg=COLORS["bg_primary"])

        main_frame = tk.Frame(self.master, bg=COLORS["bg_primary"])
        main_frame.pack(expand=True, fill="both", padx=40, pady=40)

        title_label = tk.Label(
            main_frame,
            text=self.__class__.__name__,
            **STYLES["title_label"]
        )
        title_label.pack(pady=(0, 30))

        button_container = tk.Frame(main_frame, bg=COLORS["bg_primary"])
        button_container.pack(expand=True)

        make_request_button = tk.Button(
            button_container,
            text="Send photos",
            command=self.send_event,
            **STYLES["button"]
        )
        make_request_button.pack(pady=8, fill="x", ipadx=20)

        settings_button = tk.Button(
            button_container,
            text="Settings",
            command=self.open_settings,
            **STYLES["button"]
        )
        settings_button.pack(pady=8, fill="x", ipadx=20)

        select_photos = tk.Button(
            button_container,
            text="Select photos",
            command=self.select_photos,
            **STYLES["button"]
        )
        select_photos.pack(pady=8, fill="x", ipadx=20)

        back_button = tk.Button(
            button_container,
            text="Back",
            command=self.devices_window.show_devices,
            **STYLES["button"]
        )
        back_button.pack(pady=8, fill="x", ipadx=20)
        self._create_photos_preview(main_frame)

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

    def _update_photos_preview(self):
        """Update the photos preview with current selected images."""
        if hasattr(self, 'photos_container'):
            for widget in self.photos_container.winfo_children():
                widget.destroy()

            from app.db import db_helper
            selected_photos = db_helper.get_actual_images()

            if selected_photos:
                for photo_name in selected_photos:
                    photo_label = tk.Label(
                        self.photos_container,
                        text=f"📷 {photo_name}",
                        bg=COLORS["bg_secondary"],
                        fg=COLORS["text_primary"],
                        font=("Arial", 9)
                    )
                    photo_label.pack(anchor="w", pady=2)
            else:
                no_photos_label = tk.Label(
                    self.photos_container,
                    text="No photos selected",
                    bg=COLORS["bg_secondary"],
                    fg=COLORS["text_secondary"],
                    font=("Arial", 9, "italic")
                )
                no_photos_label.pack(anchor="w", pady=2)

    @abstractmethod
    def open_settings(self):
        pass

    @abstractmethod
    def select_photos(self):
        pass

    @abstractmethod
    def send_event(self):
        pass


class Window(ABC):
    def __init__(self, master, main_window=None):
        self.master = master
        self.main_window = main_window

    def _clear_window(self):
        for widget in self.master.winfo_children():
            widget.destroy()

    @abstractmethod
    def go_back(self):
        pass
