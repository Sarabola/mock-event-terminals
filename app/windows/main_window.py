import tkinter as tk

from app.theme import COLORS, STYLES

from .abc import Window
from .devices_window import DevicesWindow
from .settings_window import SettingsWindow


class MainWindow(Window):
    def create_main_screen(self):
        self._clear_window()
        self.master.title("Terminal Emulator")
        self.master.configure(bg=COLORS["bg_primary"])

        main_frame = tk.Frame(self.master, bg=COLORS["bg_primary"])
        main_frame.pack(expand=True, fill="both", padx=40, pady=40)

        title_label = tk.Label(
            main_frame,
            text="Terminal Emulator",
            **STYLES["title_label"]
        )
        title_label.pack(pady=(0, 40))

        button_container = tk.Frame(main_frame, bg=COLORS["bg_primary"])
        button_container.pack(expand=True)

        devices_button = tk.Button(
            button_container,
            text="Devices",
            command=self._show_devices,
            **STYLES["button"]
        )
        devices_button.pack(pady=8, fill="x", ipadx=20)

        settings_button = tk.Button(
            button_container,
            text="Settings",
            command=self._show_settings,
            **STYLES["button"]
        )
        settings_button.pack(pady=8, fill="x", ipadx=20)

        exit_button = tk.Button(
            button_container,
            text="Exit",
            command=self.go_back,
            **STYLES["button"]
        )
        exit_button.pack(pady=8, fill="x", ipadx=20)

    def _show_settings(self):
        self._clear_window()
        settings = SettingsWindow(self.master, self)
        settings.show_settings()

    def _show_devices(self):
        self._clear_window()
        devices = DevicesWindow(self.master, self)
        devices.show_devices()

    def go_back(self):
        self.master.destroy()
