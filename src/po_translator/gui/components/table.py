"""
Translation Table Component
Main table displaying translation entries
"""
import customtkinter as ctk
from po_translator.utils.language import is_untranslated


class TranslationTable:
    """Translation table component"""
    
    def __init__(self, parent, callbacks):
        """
        Initialize translation table
        
        Args:
            parent: Parent widget
            callbacks: Dict of callback functions
        """
        self.parent = parent
        self.callbacks = callbacks
        self.entries = []
        self.selected_entries = set()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup table UI"""
        # Table header
        header = ctk.CTkFrame(self.parent, fg_color="#1a1a1a", height=45, corner_radius=0)
        header.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        header.grid_columnconfigure(2, weight=2)
        header.grid_columnconfigure(3, weight=2)
        header.grid_propagate(False)
        
        headers = [
            ("☐", 0, 40),
            ("", 1, 50),
            ("Source Text", 2, 0),
            ("Translation", 3, 0),
            ("Module", 4, 150),
            ("Actions", 5, 100)
        ]
        
        for text, col, width in headers:
            lbl = ctk.CTkLabel(
                header,
                text=text,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#888888",
                anchor="w"
            )
            if width:
                lbl.grid(row=0, column=col, padx=10, sticky="w")
            else:
                lbl.grid(row=0, column=col, padx=10, sticky="ew")
        
        # Scrollable table
        self.table = ctk.CTkScrollableFrame(
            self.parent,
            fg_color="#0f0f0f",
            scrollbar_button_color="#2a2a2a",
            scrollbar_button_hover_color="#3a3a3a"
        )
        self.table.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)
        self.table.grid_columnconfigure(2, weight=2)
        self.table.grid_columnconfigure(3, weight=2)
    
    def show_empty_state(self):
        """Show empty state"""
        for widget in self.table.winfo_children():
            widget.destroy()
        
        empty = ctk.CTkFrame(self.table, fg_color="transparent")
        empty.grid(row=0, column=0, columnspan=6, pady=150)
        
        ctk.CTkLabel(
            empty,
            text="📁",
            font=ctk.CTkFont(size=64)
        ).pack()
        
        ctk.CTkLabel(
            empty,
            text="No files imported yet",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff"
        ).pack(pady=(15, 5))
        
        ctk.CTkLabel(
            empty,
            text="Import .po files to get started • Ctrl+O",
            font=ctk.CTkFont(size=13),
            text_color="#666666"
        ).pack()
    
    def populate(self, entries, merger, display_limit=50):
        """
        Populate table with entries

        Args:
            entries: List of PO entries to display
            merger: POMerger instance for module lookup
            display_limit: Maximum entries to display
        """
        for widget in self.table.winfo_children():
            widget.destroy()

        self.entries = entries

        if not entries:
            self.show_empty_state()
            return

        # Create rows
        for idx, entry in enumerate(entries[:display_limit]):
            self.create_row(idx, entry, merger)
        
        if len(entries) > display_limit:
            pagination_frame = ctk.CTkFrame(self.table, fg_color="transparent")
            pagination_frame.grid(row=display_limit + 1, column=0, columnspan=6, pady=20)
            
            ctk.CTkLabel(
                pagination_frame,
                text=f"📊 Showing {display_limit} of {len(entries)} entries",
                text_color="#888888",
                font=ctk.CTkFont(size=12)
            ).pack(side="left", padx=10)
            
            ctk.CTkLabel(
                pagination_frame,
                text="💡 Tip: Use search/filters to find specific entries faster",
                text_color="#666666",
                font=ctk.CTkFont(size=11)
            ).pack(side="left", padx=10)
    
    def create_row(self, idx, entry, merger):
        """Create table row"""
        is_translated = not is_untranslated(entry.msgid, entry.msgstr)
        is_selected = id(entry) in self.selected_entries
        
        # Checkbox
        var = ctk.BooleanVar(value=is_selected)
        checkbox = ctk.CTkCheckBox(
            self.table,
            text="",
            variable=var,
            width=40,
            command=lambda: self.toggle_selection(entry, var.get())
        )
        checkbox.grid(row=idx, column=0, padx=10, pady=4)
        
        # Status icon
        status_icon = "✅" if is_translated else "⏳"
        ctk.CTkLabel(
            self.table,
            text=status_icon,
            width=50,
            font=ctk.CTkFont(size=18)
        ).grid(row=idx, column=1, padx=5, pady=4)
        
        # Source
        src_frame = ctk.CTkFrame(
            self.table,
            fg_color="#1a1a1a" if not is_selected else "#2a2a3a",
            corner_radius=6,
            cursor="hand2"
        )
        src_frame.grid(row=idx, column=2, padx=8, pady=4, sticky="ew")
        
        ctk.CTkLabel(
            src_frame,
            text=entry.msgid[:150] + ("..." if len(entry.msgid) > 150 else ""),
            anchor="w",
            font=ctk.CTkFont(size=12),
            text_color="#e0e0e0"
        ).pack(padx=12, pady=10, fill="x")
        
        # Translation
        trans_frame = ctk.CTkFrame(
            self.table,
            fg_color="#1a1a1a" if is_translated and not is_selected else "#2a1a1a" if not is_selected else "#2a2a3a",
            corner_radius=6,
            cursor="hand2"
        )
        trans_frame.grid(row=idx, column=3, padx=8, pady=4, sticky="ew")
        
        trans_text = entry.msgstr if entry.msgstr else "Not translated"
        trans_color = "#e0e0e0" if is_translated else "#888888"
        
        ctk.CTkLabel(
            trans_frame,
            text=trans_text[:150] + ("..." if len(trans_text) > 150 else ""),
            anchor="w",
            font=ctk.CTkFont(size=12),
            text_color=trans_color
        ).pack(padx=12, pady=10, fill="x")
        
        # Module
        module = merger.indexer.get_module(entry.msgid)
        ctk.CTkLabel(
            self.table,
            text=module,
            width=150,
            text_color="#10b981",
            font=ctk.CTkFont(size=11)
        ).grid(row=idx, column=4, padx=10, pady=4)
        
        # Actions
        actions_frame = ctk.CTkFrame(self.table, fg_color="transparent")
        actions_frame.grid(row=idx, column=5, padx=10, pady=4)
        
        ctk.CTkButton(
            actions_frame,
            text="✏️",
            command=lambda: self.callbacks['edit'](entry),
            width=35,
            height=35,
            fg_color="#374151",
            hover_color="#1f2937",
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=2)
        
        # Click to edit
        for frame in [src_frame, trans_frame]:
            frame.bind("<Button-1>", lambda e, ent=entry: self.callbacks['edit'](ent))
            frame.bind("<Enter>", lambda e, f=frame: f.configure(fg_color="#252525"))
            frame.bind("<Leave>", lambda e, f=frame, t=is_translated, s=is_selected: 
                      f.configure(fg_color="#2a2a3a" if s else "#1a1a1a" if t else "#2a1a1a"))
    
    def toggle_selection(self, entry, selected):
        """Toggle entry selection"""
        if selected:
            self.selected_entries.add(id(entry))
        else:
            self.selected_entries.discard(id(entry))
        
        if self.callbacks.get('selection_changed'):
            self.callbacks['selection_changed']()
    
    def select_all(self):
        """Select all entries"""
        for entry in self.entries:
            self.selected_entries.add(id(entry))
    
    def clear_selection(self):
        """Clear all selections"""
        self.selected_entries.clear()
    
    def get_selected_count(self):
        """Get number of selected entries"""
        return len(self.selected_entries)
    
    def get_selected_entries(self, all_entries):
        """Get list of selected entry objects"""
        return [e for e in all_entries if id(e) in self.selected_entries]

