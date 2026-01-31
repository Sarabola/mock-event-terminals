from app.db import db_helper
from app.windows.abc import DeviceWindow
import tkinter as tk
import json


class DeviceSettingsWindow:
    def __init__(self, master: tk.Tk, devices_window: DeviceWindow, device_name: str):
        self.master = master
        self.devices_window = devices_window
        self.device_id = self.get_actual_settings(device_name)
        self.device_id_var = tk.StringVar(value=self.device_id)

    def show_settings(self):
        back_button = tk.Button(self.master, text="Back", command=self.go_back)
        back_button.pack(anchor=tk.NW, pady=10, padx=10)

        device_id_frame = tk.Frame(self.master)
        device_id_frame.pack(anchor=tk.NW, pady=10, padx=10)
        device_id_label = tk.Label(device_id_frame, text="DEVICE ID:", width=10)
        device_id_label.pack(side=tk.LEFT)
        device_id_entry = tk.Entry(device_id_frame, textvariable=self.device_id_var, width=50)
        device_id_entry.pack(side=tk.LEFT)

    @staticmethod
    def get_actual_settings(device_name: str) -> str:
        terminal_data = db_helper.get_device_by_name(device_name)
        return terminal_data.get("device_id")

    def go_back(self):
        for widget in self.master.winfo_children():
            widget.destroy()
        self.devices_window.show()