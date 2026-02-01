import tkinter as tk
from threading import Thread
from tkinter import ttk

from app.db import db_helper
from app.theme import COLORS, STYLES


class SendStatusWindow:
    def __init__(self, master, device_name: str):
        self.master = master
        self.device_name = device_name
        self.window = None
        self.results = {}
        self.is_sending = False

    def show_status(self, results_callback):
        """Show status window and start sending process."""
        self.results_callback = results_callback
        self._create_window()

        thread = Thread(target=self._send_photos, daemon=True)
        thread.start()

    def _create_window(self):
        """Create the status window."""
        self.window = tk.Toplevel(self.master)
        self.window.title(f"Sending Photos - {self.device_name}")
        self.window.geometry("300x300")
        self.window.configure(bg=COLORS["bg_primary"])
        self.window.resizable(False, True)

        self.window.transient(self.master)
        self.window.grab_set()

        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.window.winfo_screenheight() // 2) - (700 // 2)
        self.window.geometry(f"600x700+{x}+{y}")

        main_frame = tk.Frame(self.window, bg=COLORS["bg_primary"])
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        title_label = tk.Label(
            main_frame,
            text=f"Sending photos from {self.device_name}",
            **STYLES["title_label"]
        )
        title_label.pack(pady=(0, 20))

        progress_frame = tk.Frame(main_frame, bg=COLORS["bg_primary"])
        progress_frame.pack(fill="both", expand=True)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill="x", pady=(0, 20))

        self.status_label = tk.Label(
            progress_frame,
            text="Preparing to send...",
            bg=COLORS["bg_primary"],
            fg=COLORS["text_secondary"],
            font=("Arial", 10)
        )
        self.status_label.pack(pady=(0, 10))

        results_container = tk.Frame(progress_frame, bg=COLORS["bg_secondary"])
        results_container.pack(fill="both", expand=True)

        canvas = tk.Canvas(results_container, bg=COLORS["bg_secondary"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(results_container, orient="vertical", command=canvas.yview)
        self.results_frame = tk.Frame(canvas, bg=COLORS["bg_secondary"])

        self.results_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.results_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        buttons_frame = tk.Frame(main_frame, bg=COLORS["bg_primary"])
        buttons_frame.pack(pady=(20, 0))

        self.repeat_button = tk.Button(
            buttons_frame,
            text="Repeat",
            command=self._repeat_sending,
            state="disabled",
            **STYLES["button"]
        )
        self.repeat_button.pack(side="left", padx=(0, 10))

        self.exit_button = tk.Button(
            buttons_frame,
            text="Exit",
            command=self._close_window,
            **STYLES["button"]
        )
        self.exit_button.pack(side="left")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "TProgressbar",
            background=COLORS["accent"],
            troughcolor=COLORS["bg_secondary"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["accent"],
            darkcolor=COLORS["accent"]
        )

    def _send_photos(self):
        """Send photos in separate thread and update UI."""
        self.is_sending = True

        selected_photos = db_helper.get_actual_images()
        total_photos = len(selected_photos)

        if total_photos == 0:
            self._update_status("No photos selected to send")
            self._finish_sending()
            return

        self._update_status(f"Sending {total_photos} photo(s)...")

        def progress_callback(photo_name, status, progress):
            self.window.after(0, lambda: self._update_progress(photo_name, status, progress))

        self.results_callback(selected_photos, progress_callback)
        self._finish_sending()

    def _update_progress(self, photo_name: str, status: int, progress: float):
        """Update progress bar and add photo result."""
        self.progress_var.set(progress)

        self._add_photo_result(photo_name, status)

        if status == 200:
            self._update_status(f"Sent {photo_name} successfully")
        else:
            self._update_status(f"Failed to send {photo_name} (Status: {status})")

    def _add_photo_result(self, photo_name: str, status: int):
        """Add a photo result to the results frame."""
        result_frame = tk.Frame(self.results_frame, bg=COLORS["bg_secondary"])
        result_frame.pack(fill="x", pady=2, padx=5)

        if status == 200:
            icon = "✅"
            color = COLORS["success"]
            text_color = COLORS["text_primary"]
        else:
            icon = "❌"
            color = COLORS["error"]
            text_color = COLORS["text_secondary"]

        status_label = tk.Label(
            result_frame,
            text=f"{icon} {photo_name}",
            bg=COLORS["bg_secondary"],
            fg=text_color,
            font=("Arial", 10)
        )
        status_label.pack(side="left")

        status_code_label = tk.Label(
            result_frame,
            text=f"Status: {status}",
            bg=COLORS["bg_secondary"],
            fg=color,
            font=("Arial", 9)
        )
        status_code_label.pack(side="right")

    def _update_status(self, message: str):
        """Update status label."""
        self.window.after(0, lambda: self.status_label.config(text=message))

    def _finish_sending(self):
        """Finish sending process and enable close button."""
        self.is_sending = False
        self.window.after(0, self._enable_close_button)

    def _repeat_sending(self):
        """Repeat the sending process without clearing the window."""
        # Reset progress and status
        self.progress_var.set(0)
        self.status_label.config(text="Preparing to send...")

        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        self.results = {}

        self.repeat_button.config(state="disabled")

        thread = Thread(target=self._send_photos, daemon=True)
        thread.start()

    def _enable_close_button(self):
        """Enable repeat button and update final status."""
        self.progress_var.set(100)

        successful = sum(1 for status in self.results.values() if status == 200)
        total = len(self.results)

        if total > 0:
            final_status = f"Completed: {successful}/{total} photos sent successfully"
        else:
            final_status = "No photos were sent"

        self.status_label.config(text=final_status)
        self.repeat_button.config(state="normal")

    def _close_window(self):
        """Close the status window."""
        if self.window:
            self.window.destroy()
