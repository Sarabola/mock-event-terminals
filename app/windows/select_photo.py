import json

from app.config import project_settings
from app.db import db_helper
from app.windows.abc import Window, DeviceWindow
from app.theme import COLORS, STYLES
import tkinter as tk
from tkinter import messagebox

class SelectPhotosWindow(Window):
    def __init__(self, master, device_window: DeviceWindow):
        super().__init__(master=master, main_window=device_window)

    def show_images(self):
        self.master.title("Photo settings")
        self.actualize_photo_list()
        self.get_images_statuses()

    def get_images_statuses(self):
        self._clear_window()
        self.master.configure(bg=COLORS["bg_primary"])

        main_frame = tk.Frame(self.master, bg=COLORS["bg_primary"])
        main_frame.pack(expand=True, fill="both", padx=40, pady=40)

        title_label = tk.Label(
            main_frame, 
            text="Select Photos", 
            **STYLES["title_label"]
        )
        title_label.pack(pady=(0, 30))

        content_container = tk.Frame(main_frame, bg=COLORS["bg_primary"])
        content_container.pack(expand=True, fill="both")

        canvas = tk.Canvas(content_container, bg=COLORS["bg_primary"], highlightthickness=0)
        scrollbar = tk.Scrollbar(content_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS["bg_primary"])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        images_data = db_helper.get_images_data()
        self.image_vars = {}
        
        for image_name, status in images_data.items():
            var = tk.BooleanVar(value=status)
            self.image_vars[image_name] = var
            
            frame = tk.Frame(scrollable_frame, bg=COLORS["bg_primary"])
            frame.pack(anchor=tk.W, pady=5, padx=20, fill="x")
            
            checkbox = tk.Checkbutton(
                frame, 
                text=image_name, 
                variable=var,
                **STYLES["checkbutton"]
            )
            checkbox.pack(side=tk.LEFT)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        button_container = tk.Frame(main_frame, bg=COLORS["bg_primary"])
        button_container.pack(pady=20)
        
        save_button = tk.Button(
            button_container, 
            text="Save", 
            command=self.save_variable,
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

    def actualize_photo_list(self):
        images = project_settings.images_path
        actual_data = db_helper.get_data()
        for file in images.glob("*.jpg"):
            if file.name in actual_data["images"]:
                continue
            actual_data["images"][file.name] = False
        for file in list(actual_data["images"].keys()):
            file_path = images.joinpath(file)
            if file_path.exists():
                continue
            actual_data["images"].pop(file)
        db_helper.update_data(actual_data)


    def save_variable(self):
        with open(project_settings.db_file, "r") as f:
            actual_data = json.load(f)
        
        new_images_data = {}
        for image_name, var in self.image_vars.items():
            new_images_data[image_name] = var.get()
        
        if new_images_data != actual_data.get("images"):
            actual_data["images"] = new_images_data
            db_helper.update_data(actual_data)
            messagebox.showinfo("Success", "Photos successfuly selected")
        self.go_back()


    def go_back(self):
        self._clear_window()
        self.main_window.show()
