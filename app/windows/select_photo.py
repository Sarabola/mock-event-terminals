import json

from app.config import project_settings
from app.db import db_helper
from app.windows.abc import Window, DeviceWindow
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
        
        title_label = tk.Label(self.master, text="Select Photos", font=("Arial", 14, "bold"))
        title_label.pack(pady=10)

        images_data = db_helper.get_images_data()
        self.image_vars = {}
        
        for image_name, status in images_data.items():
            var = tk.BooleanVar(value=status)
            self.image_vars[image_name] = var
            
            frame = tk.Frame(self.master)
            frame.pack(anchor=tk.W, pady=5, padx=20)
            
            checkbox = tk.Checkbutton(frame, text=image_name, variable=var)
            checkbox.pack(side=tk.LEFT)
        
        back_button = tk.Button(self.master, text="Back", command=self.go_back)
        back_button.pack(pady=20)
        save_button = tk.Button(self.master, text="Save", command=self.save_variable)
        save_button.pack()

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


    def go_back(self, ):
        self._clear_window()
        self.main_window.show()
