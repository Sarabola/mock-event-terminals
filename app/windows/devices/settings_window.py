from app.config import project_settings
from app.db import db_helper
from app.devices.abc import DeviceSender
from app.windows.abc import DeviceWindow
from app.theme import COLORS, STYLES
import tkinter as tk
from tkinter import messagebox
import json


class DeviceSettingsWindow:
    def __init__(self, master: tk.Tk, devices_window: DeviceWindow, device_name: str, device_sender: DeviceSender):
        self.master = master
        self.devices_window = devices_window
        self.device_name = device_name
        self.device_id = self.get_actual_settings(self.device_name)
        self.device_id_var = tk.StringVar(value=self.device_id)
        self.device = device_sender

    def show_settings(self):
        self._clear_window()
        self.master.configure(bg=COLORS["bg_primary"])

        main_frame = tk.Frame(self.master, bg=COLORS["bg_primary"])
        main_frame.pack(expand=True, fill="both", padx=40, pady=40)

        title_label = tk.Label(
            main_frame,
            text="Device Settings",
            **STYLES["title_label"]
        )
        title_label.pack(pady=(0, 30))

        content_container = tk.Frame(main_frame, bg=COLORS["bg_primary"])
        content_container.pack(expand=True, fill="x")

        device_id_frame = tk.Frame(content_container, bg=COLORS["bg_primary"])
        device_id_frame.pack(pady=10, anchor="w")

        device_id_label = tk.Label(
            device_id_frame,
            text="DEVICE ID:",
            **STYLES["label"]
        )
        device_id_label.pack(side=tk.LEFT, padx=(0, 10))

        device_id_entry = tk.Entry(
            device_id_frame,
            textvariable=self.device_id_var,
            width=50,
            **STYLES["entry"]
        )
        device_id_entry.pack(side=tk.LEFT)

        button_container = tk.Frame(main_frame, bg=COLORS["bg_primary"])
        button_container.pack(pady=20)

        back_button = tk.Button(
            button_container,
            text="Back",
            command=self.go_back,
            **STYLES["button"]
        )
        back_button.pack(pady=8, fill="x", ipadx=20)
        save_button = tk.Button(
            button_container,
            text="Save",
            command=self._save_data,
            **STYLES["button"]
        )
        save_button.pack(pady=8, fill="x", ipadx=20)

    @staticmethod
    def get_actual_settings(device_name: str) -> str:
        terminal_data = db_helper.get_device_by_name(device_name)
        return terminal_data.get("device_id")

    def _save_data(self):
        current = self.device_id_var.get()
        data = db_helper.get_data()
        if data["terminals"][self.device_name].get("device_id") != current:
            data["terminals"][self.device_name]["device_id"] = current
            db_helper.update_data(data)
            messagebox.showinfo("Success", "Successfully updated device id!")
        self.device.device_id = current
        self.go_back()

    def _clear_window(self):
        for widget in self.master.winfo_children():
            widget.destroy()

    def go_back(self):
        self._clear_window()
        self.devices_window.show()
