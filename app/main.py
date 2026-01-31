import tkinter as tk
from app.theme import apply_theme_to_root, COLORS
from windows.main_window import MainWindow

class TerminalEmulatorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Terminal Emulator")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        apply_theme_to_root(root)
        self._create_main_window()

    def _create_main_window(self):
        main_window = MainWindow(master=self.root, main_window=None)
        main_window.create_main_screen()

if __name__ == "__main__":
    root = tk.Tk()
    app = TerminalEmulatorApp(root)
    root.mainloop()