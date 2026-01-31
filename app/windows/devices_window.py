import tkinter as tk

from app.theme import COLORS, STYLES
from app.windows.abc import Window
from app.windows.devices.lunafast2nextgen import LunaFast2NextGenWindow


class DevicesWindow(Window):
    def show_devices(self):
        self._clear_window()
        self.master.configure(bg=COLORS["bg_primary"])

        main_frame = tk.Frame(self.master, bg=COLORS["bg_primary"])
        main_frame.pack(expand=True, fill="both", padx=40, pady=40)

        title_label = tk.Label(
            main_frame, 
            text="Devices", 
            **STYLES["title_label"]
        )
        title_label.pack(pady=(0, 30))

        button_container = tk.Frame(main_frame, bg=COLORS["bg_primary"])
        button_container.pack(expand=True)

        next_gen_button = tk.Button(
            button_container, 
            text="Luna Fast 2 Next Gen", 
            command=self._open_lunafast2nextgen,
            **STYLES["button"]
        )
        next_gen_button.pack(pady=8, fill="x", ipadx=20)

        luna_fast_button = tk.Button(
            button_container, 
            text="Luna Fast 4A", 
            command=self._open_lunafast4a,
            **STYLES["button"]
        )
        luna_fast_button.pack(pady=8, fill="x", ipadx=20)

        r20_face_button = tk.Button(
            button_container, 
            text="R20", 
            command=self._open_r20,
            **STYLES["button"]
        )
        r20_face_button.pack(pady=8, fill="x", ipadx=20)

        beward_button = tk.Button(
            button_container, 
            text="Beward", 
            command=self._open_beward,
            **STYLES["button"]
        )
        beward_button.pack(pady=8, fill="x", ipadx=20)

        back_button = tk.Button(
            button_container, 
            text="Back", 
            command=self.go_back,
            **STYLES["button"]
        )
        back_button.pack(pady=8, fill="x", ipadx=20)

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
