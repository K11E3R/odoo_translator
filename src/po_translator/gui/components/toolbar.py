"""
Toolbar Component
Top toolbar with search, filters, and bulk actions
"""
import customtkinter as ctk

from ..theme import THEME


class Toolbar:
    """Toolbar component with search and filters"""
    
    def __init__(self, parent, callbacks):
        """
        Initialize toolbar
        
        Args:
            parent: Parent widget
            callbacks: Dict of callback functions
        """
        self.parent = parent
        self.callbacks = callbacks
        
        self.frame = ctk.CTkFrame(parent, fg_color=THEME.SURFACE_ALT, height=75, corner_radius=0)
        self.frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_propagate(False)
        
        self.filter_var = ctk.StringVar(value="all")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup toolbar UI"""
        container = ctk.CTkFrame(self.frame, fg_color="transparent")
        container.grid(row=0, column=0, sticky="ew", padx=25, pady=18)
        container.grid_columnconfigure(0, weight=1)

        # Search
        self.search_entry = ctk.CTkEntry(
            container,
            placeholder_text="🔍  Search translations... (Ctrl+F)",
            height=40,
            border_width=0,
            fg_color=THEME.INPUT_BG,
            text_color=THEME.TEXT_PRIMARY,
            placeholder_text_color=THEME.TEXT_PLACEHOLDER,
            font=THEME.font(size=13)
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 15))
        self.search_entry.bind("<KeyRelease>", lambda e: self.callbacks['search']())
        
        # Filters
        filter_frame = ctk.CTkFrame(container, fg_color="transparent")
        filter_frame.grid(row=0, column=1)

        for text, value in [("All", "all"), ("Translated", "translated"), ("Pending", "untranslated")]:
            ctk.CTkRadioButton(
                filter_frame,
                text=text,
                variable=self.filter_var,
                value=value,
                command=self.callbacks['apply_filter'],
                font=THEME.font(size=12),
                text_color=THEME.TEXT_SECONDARY,
                fg_color=THEME.ACCENT_PRIMARY,
                hover_color=THEME.ACCENT_PRIMARY_HOVER,
                border_color=THEME.TEXT_MUTED
            ).pack(side="left", padx=8)
        
        # Bulk actions
        bulk_frame = ctk.CTkFrame(container, fg_color="transparent")
        bulk_frame.grid(row=0, column=2, padx=(15, 0))

        ctk.CTkButton(
            bulk_frame,
            text="☑ Select All",
            command=self.callbacks['select_all'],
            height=40,
            width=110,
            fg_color=THEME.SURFACE_RAISED,
            hover_color=THEME.SURFACE_HOVER,
            text_color=THEME.TEXT_PRIMARY,
            font=THEME.font(size=12, weight="bold")
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            bulk_frame,
            text="☐ Clear",
            command=self.callbacks['clear_selection'],
            height=40,
            width=90,
            fg_color=THEME.SURFACE_RAISED,
            hover_color=THEME.SURFACE_HOVER,
            text_color=THEME.TEXT_PRIMARY,
            font=THEME.font(size=12)
        ).pack(side="left", padx=4)
    
    def get_search_query(self):
        """Get current search query"""
        return self.search_entry.get().lower()

    def get_search_text(self):
        """Get the raw search text"""
        return self.search_entry.get()

    def get_filter_value(self):
        """Get current filter value"""
        return self.filter_var.get()
    
    def clear_search(self):
        """Clear search entry"""
        self.search_entry.delete(0, 'end')
    
    def focus_search(self):
        """Focus search entry"""
        self.search_entry.focus()

