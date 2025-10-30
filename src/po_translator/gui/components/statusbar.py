"""
StatusBar Component
Bottom status bar with progress tracking
"""
import customtkinter as ctk

from ..theme import THEME


class StatusBar:
    """Status bar component with progress indicator"""
    
    def __init__(self, parent):
        """
        Initialize status bar
        
        Args:
            parent: Parent widget
        """
        self.parent = parent
        
        self.frame = ctk.CTkFrame(parent, height=50, corner_radius=0, fg_color=THEME.SURFACE_ALT)
        self.frame.grid(row=1, column=1, sticky="ew")
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_propagate(False)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup status bar UI"""
        container = ctk.CTkFrame(self.frame, fg_color="transparent")
        container.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        container.grid_columnconfigure(0, weight=1)
        
        self.status = ctk.CTkLabel(
            container,
            text="Ready to import files",
            anchor="w",
            font=THEME.font(size=12),
            text_color=THEME.TEXT_SECONDARY
        )
        self.status.grid(row=0, column=0, sticky="w")
        
        self.progress_label = ctk.CTkLabel(
            container,
            text="",
            anchor="e",
            font=THEME.font(size=11),
            text_color=THEME.TEXT_MUTED
        )
        self.progress_label.grid(row=0, column=1, padx=(10, 10))
        self.progress_label.grid_remove()
        
        self.progress = ctk.CTkProgressBar(
            container,
            width=300,
            height=8,
            progress_color=THEME.ACCENT_PRIMARY,
            fg_color=THEME.SURFACE
        )
        self.progress.grid(row=0, column=2)
        self.progress.set(0)
        self.progress.grid_remove()
    
    def set_status(self, message, show_progress=False, progress_text=""):
        """
        Set status message
        
        Args:
            message: Status message
            show_progress: Whether to show progress bar
            progress_text: Progress percentage text
        """
        self.status.configure(text=message)
        
        if show_progress:
            self.progress.grid()
            self.progress_label.grid()
            self.progress_label.configure(text=progress_text)
            if not progress_text:
                self.progress.set(0)
        else:
            self.progress.grid_remove()
            self.progress_label.grid_remove()
    
    def set_progress(self, value):
        """
        Set progress bar value
        
        Args:
            value: Progress value (0.0 to 1.0)
        """
        self.progress.set(value)

