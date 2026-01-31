import json
import tkinter as tk
from tkinter import messagebox
from typing import TYPE_CHECKING
from app.config import project_settings
from app.windows.abc import Window
from app.theme import COLORS, STYLES
from dotenv import load_dotenv
from app.db import db_helper

if TYPE_CHECKING:
    from app.windows.main_window import MainWindow

load_dotenv()


class SettingsWindow(Window):
    def __init__(self, master: tk.Tk, main_window: "MainWindow"):
        super().__init__(master, main_window)
        self.host = db_helper.get_host()
        self.port = db_helper.get_port()
        self.host_var = tk.StringVar()
        self.port_var = tk.IntVar()

    def show_settings(self):
        self._clear_window()
        self.master.title("Network settings")
        self.master.configure(bg=COLORS["bg_primary"])

        main_frame = tk.Frame(self.master, bg=COLORS["bg_primary"])
        main_frame.pack(expand=True, fill="both", padx=40, pady=40)

        title_label = tk.Label(
            main_frame,
            text="Network Settings",
            **STYLES["title_label"]
        )
        title_label.pack(pady=(0, 30))

        content_container = tk.Frame(main_frame, bg=COLORS["bg_primary"])
        content_container.pack(expand=True, fill="x")

        host_frame = tk.Frame(content_container, bg=COLORS["bg_primary"])
        host_frame.pack(pady=10, anchor="w")

        host_label = tk.Label(
            host_frame,
            text="Host:",
            **STYLES["label"]
        )
        host_label.pack(side=tk.LEFT, padx=(0, 10))

        self.host_var = tk.StringVar(value=self.host if self.host else "")
        host_entry = tk.Entry(
            host_frame,
            textvariable=self.host_var,
            **STYLES["entry"]
        )
        host_entry.pack(side=tk.LEFT)

        port_frame = tk.Frame(content_container, bg=COLORS["bg_primary"])
        port_frame.pack(pady=10, anchor="w")

        port_label = tk.Label(
            port_frame,
            text="Port:",
            **STYLES["label"]
        )
        port_label.pack(side=tk.LEFT, padx=(0, 10))

        self.port_var = tk.IntVar(value=self.port if self.port else 9091)
        port_entry = tk.Entry(
            port_frame,
            textvariable=self.port_var,
            **STYLES["entry"]
        )
        port_entry.pack(side=tk.LEFT)

        button_container = tk.Frame(main_frame, bg=COLORS["bg_primary"])
        button_container.pack(pady=20)

        save_button = tk.Button(
            button_container,
            text="Save",
            command=self._save_settings,
            **STYLES["button"]
        )
        save_button.pack(pady=8, fill="x", ipadx=20)

        back_button = tk.Button(
            button_container,
            text="Back",
            command=self.go_back,
            **STYLES["button"]
        )
        back_button.pack(pady=8, fill="x", ipadx=20)

    def _save_settings(self):
        new_host = self.host_var.get()
        new_port = self.port_var.get()

        if self.host != new_host or self.port != new_port:
            with open(project_settings.db_file, "r") as f:
                data = json.load(f)
                data["network"]["host"] = new_host
                data["network"]["port"] = new_port
                db_helper.update_data(new_data=data)
                messagebox.showinfo("Success", "Settings saved!")
        self.go_back()

    def go_back(self):
        self._clear_window()
        self.main_window.create_main_screen()

    def _clear_window(self):
        for widget in self.master.winfo_children():
            widget.destroy()
