"""
Translation Table Component
Main table displaying translation entries
"""
import customtkinter as ctk
from po_translator.utils.language import is_untranslated

from ..theme import THEME


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
        self.status_map = {}
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup table UI"""
        # Table header
        header = ctk.CTkFrame(self.parent, fg_color=THEME.TABLE_HEADER_BG, height=45, corner_radius=0)
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
                text_color=THEME.TEXT_SECONDARY,
                anchor="w"
            )
            if width:
                lbl.grid(row=0, column=col, padx=10, sticky="w")
            else:
                lbl.grid(row=0, column=col, padx=10, sticky="ew")
        
        # Scrollable table
        self.table = ctk.CTkScrollableFrame(
            self.parent,
            fg_color=THEME.SURFACE,
            scrollbar_button_color=THEME.SIDEBAR_SCROLLBAR,
            scrollbar_button_hover_color=THEME.SIDEBAR_SCROLLBAR_HOVER
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
            text_color=THEME.TEXT_PRIMARY
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            empty,
            text="Import .po files to get started • Ctrl+O",
            font=ctk.CTkFont(size=13),
            text_color=THEME.TEXT_MUTED
        ).pack()
    
    def populate(self, entries, merger, status_map=None, display_limit=50):
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
        self.status_map = status_map or {}

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
                text_color=THEME.TEXT_SECONDARY,
                font=ctk.CTkFont(size=12)
            ).pack(side="left", padx=10)

            ctk.CTkLabel(
                pagination_frame,
                text="💡 Tip: Use search/filters to find specific entries faster",
                text_color=THEME.TEXT_MUTED,
                font=ctk.CTkFont(size=11)
            ).pack(side="left", padx=10)
    
    def create_row(self, idx, entry, merger):
        """Create table row"""
        is_translated = not is_untranslated(entry.msgid, entry.msgstr)
        is_selected = id(entry) in self.selected_entries
        status = self.status_map.get(id(entry))
        
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
        if status and status.missing_translation:
            status_icon = "🚫"
        elif status and status.source_matches is False:
            status_icon = "🌐"
        elif status and status.translation_matches is False and not status.missing_translation:
            status_icon = "⚠️"
        else:
            status_icon = "✅" if is_translated else "⏳"
        ctk.CTkLabel(
            self.table,
            text=status_icon,
            width=50,
            font=ctk.CTkFont(size=18),
            text_color=THEME.TEXT_SECONDARY
        ).grid(row=idx, column=1, padx=5, pady=4)
        
        # Source
        row_base = THEME.TABLE_ROW_BG if idx % 2 == 0 else THEME.TABLE_ROW_ALT_BG
        base_src_color = row_base
        if status:
            if status.source_matches is False:
                base_src_color = THEME.TABLE_SOURCE_MISMATCH
            elif status.source_lang is None:
                base_src_color = THEME.SURFACE_ALT
        if is_selected:
            base_src_color = THEME.TABLE_ROW_SELECTED

        src_frame = ctk.CTkFrame(
            self.table,
            fg_color=base_src_color,
            corner_radius=6,
            cursor="hand2"
        )
        src_frame.grid(row=idx, column=2, padx=8, pady=4, sticky="ew")
        
        src_text = entry.msgid[:150] + ("..." if len(entry.msgid) > 150 else "")
        ctk.CTkLabel(
            src_frame,
            text=src_text,
            anchor="w",
            font=ctk.CTkFont(size=12),
            text_color=THEME.TEXT_PRIMARY
        ).pack(padx=12, pady=(10, 6), fill="x")

        if status:
            if status.source_lang:
                confidence = int(status.source_confidence * 100)
                label = status.source_lang.upper()
                info_color = THEME.BADGE_SOURCE if status.source_matches else THEME.BADGE_SOURCE_MISMATCH
                info_text = f"Detected {label} ({confidence}%)"
            else:
                info_color = THEME.TEXT_MUTED
                info_text = "Language unknown"
            ctk.CTkLabel(
                src_frame,
                text=info_text,
                anchor="w",
                font=ctk.CTkFont(size=10),
                text_color=info_color
            ).pack(padx=12, pady=(0, 10), fill="x")
        
        # Translation
        base_trans_color = row_base if is_translated else THEME.SURFACE_ALT
        if status:
            if status.missing_translation:
                base_trans_color = THEME.TABLE_TRANSLATION_MISSING
            elif status.translation_matches is False:
                base_trans_color = THEME.TABLE_TRANSLATION_MISMATCH
        if is_selected:
            base_trans_color = THEME.TABLE_ROW_SELECTED

        trans_frame = ctk.CTkFrame(
            self.table,
            fg_color=base_trans_color,
            corner_radius=6,
            cursor="hand2"
        )
        trans_frame.grid(row=idx, column=3, padx=8, pady=4, sticky="ew")
        
        trans_text = entry.msgstr if entry.msgstr else "Not translated"
        if status and status.missing_translation:
            trans_color = THEME.ACCENT_DANGER
        elif status and status.translation_matches is False and not status.missing_translation:
            trans_color = THEME.ACCENT_WARNING
        else:
            trans_color = THEME.TEXT_PRIMARY if is_translated else THEME.TEXT_MUTED

        ctk.CTkLabel(
            trans_frame,
            text=trans_text[:150] + ("..." if len(trans_text) > 150 else ""),
            anchor="w",
            font=ctk.CTkFont(size=12),
            text_color=trans_color
        ).pack(padx=12, pady=(10, 6), fill="x")

        if status and not status.missing_translation:
            if status.translation_lang:
                confidence = int(status.translation_confidence * 100)
                label = status.translation_lang.upper()
                info_color = THEME.BADGE_TRANSLATION if status.translation_matches else THEME.BADGE_TRANSLATION_MISMATCH
                info_text = f"Detected {label} ({confidence}%)"
            else:
                info_color = THEME.TEXT_MUTED
                info_text = "Language unknown"
            ctk.CTkLabel(
                trans_frame,
                text=info_text,
                anchor="w",
                font=ctk.CTkFont(size=10),
                text_color=info_color
            ).pack(padx=12, pady=(0, 10), fill="x")
        elif status and status.missing_translation:
            ctk.CTkLabel(
                trans_frame,
                text="Awaiting translation",
                anchor="w",
                font=ctk.CTkFont(size=10),
                text_color=THEME.ACCENT_DANGER
            ).pack(padx=12, pady=(0, 10), fill="x")
        
        # Module
        module = merger.indexer.get_module(entry.msgid)
        module_label = ctk.CTkLabel(
            self.table,
            text=module,
            width=150,
            fg_color=THEME.MODULE_CHIP_BG,
            corner_radius=12,
            text_color=THEME.MODULE_CHIP_TEXT,
            font=ctk.CTkFont(size=11)
        )
        module_label.grid(row=idx, column=4, padx=10, pady=4)
        
        # Actions
        actions_frame = ctk.CTkFrame(self.table, fg_color="transparent")
        actions_frame.grid(row=idx, column=5, padx=10, pady=4)
        
        ctk.CTkButton(
            actions_frame,
            text="✏️",
            command=lambda: self.callbacks['edit'](entry),
            width=35,
            height=35,
            fg_color=THEME.SURFACE_RAISED,
            hover_color=THEME.SURFACE_HOVER,
            text_color=THEME.TEXT_PRIMARY,
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=2)
        
        # Click to edit
        for frame, base in ((src_frame, base_src_color), (trans_frame, base_trans_color)):
            frame.bind("<Button-1>", lambda e, ent=entry: self.callbacks['edit'](ent))
            frame.bind("<Enter>", lambda e, f=frame: f.configure(fg_color=THEME.SURFACE_HOVER))
            frame.bind("<Leave>", lambda e, f=frame, b=base: f.configure(fg_color=b))
    
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

