import tkinter as tk

from app.windows.abc import Window
from app.windows.devices.lunafast2nextgen import LunaFast2NextGenWindow


class DevicesWindow(Window):
    def show_devices(self):
        self._clear_window()
        next_gen_button = tk.Button(text="Luna Fast 2 Next Gen", command=self._open_lunafast2nextgen)
        next_gen_button.pack()

        luna_fast_button = tk.Button(text="Luna Fast 4A", command=self._open_lunafast4a)
        luna_fast_button.pack()

        r20_face_button = tk.Button(text="R20", command=self._open_r20)
        r20_face_button.pack()

        beward_button = tk.Button(text="Beward", command=self._open_beward)
        beward_button.pack()

        back_button = tk.Button(text="Back", command=self.go_back)
        back_button.pack()

    def go_back(self):
        self.main_window.create_main_screen()

    def _open_lunafast2nextgen(self):
        self._clear_window()
        lunafast2 = LunaFast2NextGenWindow(self.master, self)
        lunafast2.show()

    def _open_lunafast4a(self):
        pass

    def _open_r20(self):
        pass

    def _open_beward(self):
        pass
