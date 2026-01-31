from abc import ABC, abstractmethod
import tkinter as tk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .devices_window import DevicesWindow

class DeviceWindow(ABC):

    def __init__(self, master, devices_window: "DevicesWindow"):
        self.master = master
        self.devices_window = devices_window

    def show(self):
        make_request_button = tk.Button(text="Send photos", command=self.send_event)
        make_request_button.grid(row=0, column=0)

        settings_button = tk.Button(text="Settings", command=self.open_settings)
        settings_button.grid(row=1, column=0)

        select_photos = tk.Button(text="Select photos", command=self.select_photos)
        select_photos.grid(row=2, column=0)

        back_button = tk.Button(text="Back", command=self.devices_window.show_devices)
        back_button.grid(row=3, column=0)

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