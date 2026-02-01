import json
import tkinter as tk

from app.config import project_settings
from app.db import db_helper
from app.theme import apply_theme_to_root
from app.windows.main_window import MainWindow


class TerminalEmulatorApp:
    def __init__(self, _root: tk.Tk):
        self.root = _root
        self.root.title("Terminal Emulator")
        self.root.geometry("500x600")
        apply_theme_to_root(root)
        self._create_main_window()

    def _create_main_window(self):
        db_helper.initialize_db()
        main_window = MainWindow(master=self.root, main_window=None)
        main_window.create_main_screen()



if __name__ == "__main__":
    root = tk.Tk()
    app = TerminalEmulatorApp(root)
    root.mainloop()
