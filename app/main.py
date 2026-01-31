import json
import tkinter as tk

from windows.main_window import MainWindow

from app.config import project_settings
from app.theme import apply_theme_to_root


class TerminalEmulatorApp:
    def __init__(self, _root: tk.Tk):
        self.root = _root
        self.root.title("Terminal Emulator")
        self.root.geometry("500x600")
        apply_theme_to_root(root)
        self._create_main_window()

    def _create_main_window(self):
        self._create_settings_file_if_not_extists()
        main_window = MainWindow(master=self.root, main_window=None)
        main_window.create_main_screen()

    def _create_settings_file_if_not_extists(self):
        empty_data = {
            "network": {
                "host": "localhost",
                "port": 9091
            },
            "terminals": {
                "lunafast2nextgen": {
                    "device_id": ""
                },
                "lunafast4a": {
                    "device_id": "",
                    "enable_temp": False,
                    "card_event": False,
                    "above_normal_temp": False,
                    "abnormal_temp": False,
                    "old_event": False,
                    "temperature_enabled": False
                },
                "r20": {
                    "device_id": ""
                },
                "beward": {
                    "device_id": "",
                    "enable_temp": False,
                    "above_normal_temp": False,
                    "abnormal_temp": False,
                    "old_event": False
                }
            },
            "images": {}
        }

        if not project_settings.db_file.exists():
            with open("settings.json", "w") as file:
                json.dump(empty_data, file, indent=2)


if __name__ == "__main__":
    root = tk.Tk()
    app = TerminalEmulatorApp(root)
    root.mainloop()
