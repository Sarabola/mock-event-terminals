from tkinter import ttk
"""
Dark theme configuration for the Terminal Emulator App.
Uses dark blue and purple color scheme.
"""

# Color Palette - Dark Blue and Purple Theme
COLORS = {
    # Background colors
    "bg_primary": "#1a1a2e",      # Dark blue-black
    "bg_secondary": "#16213e",     # Dark blue
    "bg_tertiary": "#0f3460",      # Medium blue
    "bg_button": "#2d3561",       # Button background
    "bg_button_hover": "#3d4571",  # Button hover
    
    # Text colors
    "text_primary": "#e8e8e8",     # Light gray text
    "text_secondary": "#b8b8b8",   # Medium gray text
    "text_accent": "#9d4edd",      # Purple accent
    "text_button": "#ffffff",      # White button text
    
    # Border and outline colors
    "border": "#2d3561",           # Border color
    "border_focus": "#9d4edd",     # Focus border (purple)
    
    # Special colors
    "accent": "#9d4edd",           # Main accent (purple)
    "accent_light": "#c77dff",     # Light purple
    "success": "#4caf50",          # Green for success
    "warning": "#ff9800",          # Orange for warning
    "error": "#f44336",            # Red for error
}

# Font configurations
FONTS = {
    "default": ("Arial", 10),
    "button": ("Arial", 11, "bold"),
    "title": ("Arial", 16, "bold"),
    "subtitle": ("Arial", 12, "bold"),
    "label": ("Arial", 10),
}

# Widget styles
STYLES = {
    "button": {
        "bg": COLORS["bg_button"],
        "fg": COLORS["text_button"],
        "activebackground": COLORS["bg_button_hover"],
        "activeforeground": COLORS["text_button"],
        "borderwidth": 0,
        "relief": "flat",
        "font": FONTS["button"],
        "padx": 20,
        "pady": 8,
        "highlightthickness": 0,
    },
    "title_label": {
        "bg": COLORS["bg_primary"],
        "fg": COLORS["text_primary"],
        "font": FONTS["title"],
    },
    "label": {
        "bg": COLORS["bg_primary"],
        "fg": COLORS["text_secondary"],
        "font": FONTS["label"],
    },
    "frame": {
        "bg": COLORS["bg_primary"],
        "highlightthickness": 0,
    },
    "entry": {
        "bg": COLORS["bg_secondary"],
        "fg": COLORS["text_primary"],
        "insertbackground": COLORS["text_primary"],
        "borderwidth": 1,
        "relief": "solid",
        "font": FONTS["default"],
        "highlightthickness": 1,
        "highlightbackground": COLORS["border"],
        "highlightcolor": COLORS["border_focus"],
    },
    "checkbutton": {
        "bg": COLORS["bg_primary"],
        "fg": COLORS["text_primary"],
        "selectcolor": COLORS["bg_tertiary"],
        "activebackground": COLORS["bg_secondary"],
        "activeforeground": COLORS["text_primary"],
        "font": FONTS["default"],
        "highlightthickness": 0,
    },
}

def apply_theme_to_root(root):
    """Apply the dark theme to the root window."""
    root.configure(bg=COLORS["bg_primary"])
    
    # Configure ttk styles
    style = ttk.Style()
    style.theme_use('clam')

    style.configure(
        "TButton",
        background=COLORS["bg_button"],
        foreground=COLORS["text_button"],
        borderwidth=0,
        focuscolor=COLORS["border_focus"],
        font=FONTS["button"]
    )
    style.map(
        "TButton",
        background=[("active", COLORS["bg_button_hover"])],
        foreground=[("active", COLORS["text_button"])]
    )

    style.configure("TFrame", background=COLORS["bg_primary"])

    style.configure("TLabel", background=COLORS["bg_primary"], foreground=COLORS["text_primary"])

    style.configure(
        "TEntry",
        background=COLORS["bg_secondary"],
        foreground=COLORS["text_primary"],
        fieldbackground=COLORS["bg_secondary"],
        borderwidth=1,
        insertcolor=COLORS["text_primary"]
    )
    
    # Configure ttk.Checkbutton
    style.configure(
        "TCheckbutton",
        background=COLORS["bg_primary"],
        foreground=COLORS["text_primary"],
        focuscolor=COLORS["border_focus"]
    )
