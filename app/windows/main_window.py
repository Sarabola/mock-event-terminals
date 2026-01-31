from tkinter import ttk

from .devices_window import DevicesWindow
from .settings_window import SettingsWindow
from .abc import Window


class MainWindow(Window):
    def create_main_screen(self):
        self._clear_window()
        self.master.title("Terminal Emulator")

        devices_button = ttk.Button(text="Devices", command=self._show_devices)
        devices_button.pack(pady=10, ipadx=20)

        settings_button = ttk.Button(text="Settings", command=self._show_settings)
        settings_button.pack(pady=10, ipadx=20)

        exit_button = ttk.Button(text="Exit", command=self.go_back)
        exit_button.pack(pady=10, ipadx=20)

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
