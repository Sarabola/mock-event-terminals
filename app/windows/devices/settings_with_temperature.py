import tkinter as tk
from tkinter import messagebox

from app.db import db_helper
from app.devices.abc import DeviceSender
from app.theme import COLORS, STYLES
from app.windows.abc import DeviceWindow


class DeviceWithTemperatureSettingsWindow:
    def __init__(self, master: tk.Tk, devices_window: DeviceWindow, device_name: str, device_sender: DeviceSender):
        self.master = master
        self.devices_window = devices_window
        self.device_name = device_name
        self.device_id = db_helper.get_device_id_by_name(self.device_name)
        self.device_id_var = tk.StringVar(value=self.device_id)
        self.device = device_sender

        self.enable_temp = tk.BooleanVar()
        self.above_normal_temp = tk.BooleanVar()
        self.abnormal_temp = tk.BooleanVar()
        self.old_event = tk.BooleanVar()

        self._load_settings()

    def _load_settings(self):
        """Load existing settings from database."""
        device_data = db_helper.get_device_by_name(self.device_name)
        if device_data:
            self.enable_temp.set(device_data.get("enable_temp", False))
            self.above_normal_temp.set(device_data.get("above_normal_temp", False))
            self.abnormal_temp.set(device_data.get("abnormal_temp", False))
            self.old_event.set(device_data.get("old_event", False))

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

        event_frame = tk.Frame(content_container, bg=COLORS["bg_secondary"])
        event_frame.pack(fill="x", pady=20, padx=10)

        event_time_label = tk.Label(
            event_frame,
            text="Event Timing:",
            **STYLES["label"]
        )
        event_time_label.pack(pady=5, anchor="w", padx=10)

        current_time_status = db_helper.get_device_by_name(self.device_name).get("old_event")
        self.old_event = tk.StringVar(value="old" if current_time_status is True else "current")
        event_time_frame = tk.Frame(event_frame, bg=COLORS["bg_secondary"])
        event_time_frame.pack(fill="x", padx=20, pady=5)

        current_radio = tk.Radiobutton(
            event_time_frame,
            text="Current Event",
            variable=self.old_event,
            value="current",
            **STYLES["checkbutton"]
        )
        current_radio.pack(side=tk.LEFT, padx=5)

        old_radio = tk.Radiobutton(
            event_time_frame,
            text="Old Event (Random Past Date)",
            variable=self.old_event,
            value="old",
            **STYLES["checkbutton"]
        )
        old_radio.pack(side=tk.LEFT, padx=5)

        temp_frame = tk.Frame(content_container, bg=COLORS["bg_secondary"])
        temp_frame.pack(fill="x", pady=20, padx=10)

        enable_temp_checkbox = tk.Checkbutton(
            temp_frame,
            text="Enable Temperature Detection",
            variable=self.enable_temp,
            command=self._toggle_temperature_options,
            **STYLES["checkbutton"]
        )
        enable_temp_checkbox.pack(pady=10, anchor="w", padx=10)

        self.temp_options_frame = tk.Frame(temp_frame, bg=COLORS["bg_secondary"])

        temp_state_label = tk.Label(
            self.temp_options_frame,
            text="Temperature State:",
            **STYLES["label"]
        )
        temp_state_label.pack(pady=5, anchor="w", padx=10)

        self.temp_state_var = tk.StringVar(value="normal")
        temp_state_frame = tk.Frame(self.temp_options_frame, bg=COLORS["bg_secondary"])
        temp_state_frame.pack(fill="x", padx=20, pady=5)

        normal_radio = tk.Radiobutton(
            temp_state_frame,
            text="Normal (36.1-36.9°C)",
            variable=self.temp_state_var,
            value="normal",
            **STYLES["checkbutton"]
        )
        normal_radio.pack(side=tk.LEFT, padx=5)

        above_normal_radio = tk.Radiobutton(
            temp_state_frame,
            text="Above Normal (37.0-41.3°C)",
            variable=self.temp_state_var,
            value="above_normal",
            **STYLES["checkbutton"]
        )
        above_normal_radio.pack(side=tk.LEFT, padx=5)

        abnormal_radio = tk.Radiobutton(
            temp_state_frame,
            text="Abnormal (33.0-36.0°C or 41.4-43.5°C)",
            variable=self.temp_state_var,
            value="abnormal",
            **STYLES["checkbutton"]
        )
        abnormal_radio.pack(side=tk.LEFT, padx=5)

        self._toggle_temperature_options()

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

    def _toggle_temperature_options(self):
        """Show or hide temperature options based on enable_temp checkbox."""
        if self.enable_temp.get():
            self.temp_options_frame.pack(fill="x", pady=10, padx=10)
        else:
            self.temp_options_frame.pack_forget()

    def _save_data(self):
        current = self.device_id_var.get()
        data = db_helper.get_data()
        device_updated = False

        if data["terminals"][self.device_name].get("device_id") != current:
            data["terminals"][self.device_name]["device_id"] = current
            device_updated = True
        self.device.device_id = current

        settings = {
            "enable_temp": self.enable_temp.get(),
            "above_normal_temp": self.temp_state_var.get() == "above_normal",
            "abnormal_temp": self.temp_state_var.get() == "abnormal",
            "old_event": self.old_event.get() == "old"
        }

        for key, value in settings.items():
            if data["terminals"][self.device_name].get(key) != value:
                data["terminals"][self.device_name][key] = value
                device_updated = True

        if device_updated:
            db_helper.update_data(data)
            messagebox.showinfo("Success", "Successfully updated device settings!")

        self.go_back()

    def _clear_window(self):
        for widget in self.master.winfo_children():
            widget.destroy()

    def go_back(self):
        self._clear_window()
        self.devices_window.show()
