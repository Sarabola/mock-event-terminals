import json
import tkinter as tk
from tkinter import messagebox
from typing import TYPE_CHECKING
from app.config import project_settings
from app.windows.abc import Window
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
        self.master.title("Network settings")

        back_button = tk.Button(self.master, text="Back", command=self.go_back)
        back_button.pack(anchor=tk.NW, pady=10, padx=10)

        host_frame = tk.Frame(self.master)
        host_frame.pack(anchor=tk.NW, pady=10, padx=10)
        host_label = tk.Label(host_frame, text="Host:", width=10)
        host_label.pack(side=tk.LEFT)
        self.host_var = tk.StringVar(value=self.host if self.host else "")
        host_entry = tk.Entry(host_frame, textvariable=self.host_var, width=30)
        host_entry.pack(side=tk.LEFT)

        port_frame = tk.Frame(self.master)
        port_frame.pack(anchor=tk.NW, pady=10, padx=10)
        port_label = tk.Label(port_frame, text="Port:", width=10)
        port_label.pack(side=tk.LEFT)
        self.port_var = tk.IntVar(value=self.port if self.port else 9091)
        port_entry = tk.Entry(port_frame, textvariable=self.port_var, width=30)
        port_entry.pack(side=tk.LEFT)

        save_button = tk.Button(text="Save", command=self._save_settings)
        save_button.pack(side=tk.BOTTOM)

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
        self.main_window.create_main_screen()
