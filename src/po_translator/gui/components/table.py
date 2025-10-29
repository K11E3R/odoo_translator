"""
Translation Table Component
Main table displaying translation entries with pagination controls
"""
import math

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
        self.visible_entries = []
        self.selected_entries = set()
        self.status_map = {}
        self.header_select_var = ctk.BooleanVar(value=False)
        self._updating_header = False
        self._updating_page_controls = False
        self.page = 1
        self.page_size = 50
        self.total_pages = 1

        self.setup_ui()

    def setup_ui(self):
        """Setup table UI"""
        # Table header
        header = ctk.CTkFrame(
            self.parent,
            fg_color=THEME.TABLE_HEADER_BG,
            height=52,
            corner_radius=0,
        )
        header.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        header.grid_columnconfigure(2, weight=2)
        header.grid_columnconfigure(3, weight=2)
        header.grid_propagate(False)

        header_checkbox = ctk.CTkCheckBox(
            header,
            text="",
            variable=self.header_select_var,
            command=self.on_header_toggle,
            width=32,
            height=32,
            fg_color=THEME.ACCENT_PRIMARY,
            hover_color=THEME.ACCENT_PRIMARY_HOVER,
        )
        header_checkbox.grid(row=0, column=0, padx=(16, 8))

        headers = [
            ("", 1, 50),
            ("Source Text", 2, 0),
            ("Translation", 3, 0),
            ("Module", 4, 150),
            ("Actions", 5, 120),
        ]

        for text, col, width in headers:
            lbl = ctk.CTkLabel(
                header,
                text=text,
                font=THEME.font(size=13, weight="bold"),
                text_color=THEME.TEXT_SECONDARY,
                anchor="w",
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

        # Pagination controls
        self.pagination_frame = ctk.CTkFrame(
            self.parent,
            fg_color=THEME.SURFACE,
            corner_radius=0,
        )
        self.pagination_frame.grid(row=3, column=0, sticky="ew", padx=0, pady=(6, 12))
        self.pagination_frame.grid_columnconfigure(3, weight=1)
        self.pagination_frame.grid_columnconfigure(5, weight=0)

        self.prev_button = ctk.CTkButton(
            self.pagination_frame,
            text="⟨ Prev",
            width=110,
            height=38,
            fg_color=THEME.SURFACE_RAISED,
            hover_color=THEME.SURFACE_HOVER,
            text_color=THEME.TEXT_PRIMARY,
            font=THEME.font(size=12, weight="bold"),
            command=lambda: self.on_page_change(self.page - 1),
        )
        self.prev_button.grid(row=0, column=0, padx=(16, 6), pady=8)

        self.next_button = ctk.CTkButton(
            self.pagination_frame,
            text="Next ⟩",
            width=110,
            height=38,
            fg_color=THEME.SURFACE_RAISED,
            hover_color=THEME.SURFACE_HOVER,
            text_color=THEME.TEXT_PRIMARY,
            font=THEME.font(size=12, weight="bold"),
            command=lambda: self.on_page_change(self.page + 1),
        )
        self.next_button.grid(row=0, column=1, padx=6, pady=8)

        self.page_label = ctk.CTkLabel(
            self.pagination_frame,
            text="Page 1 of 1",
            font=THEME.font(size=12, weight="bold"),
            text_color=THEME.TEXT_PRIMARY,
        )
        self.page_label.grid(row=0, column=2, padx=(12, 6), pady=8, sticky="w")

        self.range_label = ctk.CTkLabel(
            self.pagination_frame,
            text="No entries to display",
            font=THEME.font(size=11),
            text_color=THEME.TEXT_MUTED,
        )
        self.range_label.grid(row=0, column=3, padx=(6, 6), pady=8, sticky="w")

        self.per_page_label = ctk.CTkLabel(
            self.pagination_frame,
            text="Items per page",
            font=THEME.font(size=11, weight="bold"),
            text_color=THEME.TEXT_SECONDARY,
        )
        self.per_page_label.grid(row=0, column=4, padx=(6, 6), pady=8, sticky="e")

        self.page_size_var = ctk.StringVar(value="50")
        self.page_size_menu = ctk.CTkOptionMenu(
            self.pagination_frame,
            values=["25", "50", "100", "200", "All"],
            command=self.on_page_size_change,
            width=110,
            fg_color=THEME.ACCENT_PRIMARY,
            button_color=THEME.ACCENT_PRIMARY,
            button_hover_color=THEME.ACCENT_PRIMARY_HOVER,
            dropdown_fg_color=THEME.SURFACE_RAISED,
            dropdown_text_color=THEME.TEXT_PRIMARY,
            variable=self.page_size_var,
            font=THEME.font(size=11, weight="bold"),
        )
        self.page_size_menu.grid(row=0, column=5, padx=(0, 12), pady=8)

        self.clear_selection_button = ctk.CTkButton(
            self.pagination_frame,
            text="Clear Selection",
            width=140,
            height=38,
            fg_color=THEME.ACCENT_SECONDARY,
            hover_color=THEME.ACCENT_SECONDARY_HOVER,
            text_color="white",
            font=THEME.font(size=12, weight="bold"),
            command=lambda: self.callbacks.get('clear_selection', lambda: None)(),
        )
        self.clear_selection_button.grid(row=0, column=6, padx=(6, 16), pady=8, sticky="e")
        self.clear_selection_button.configure(state="disabled")

    def show_empty_state(self):
        """Show empty state"""
        for widget in self.table.winfo_children():
            widget.destroy()
        
        empty = ctk.CTkFrame(self.table, fg_color="transparent")
        empty.grid(row=0, column=0, columnspan=6, pady=150)
        
        ctk.CTkLabel(
            empty,
            text="📁",
            font=THEME.font(size=64)
        ).pack()

        ctk.CTkLabel(
            empty,
            text="No files imported yet",
            font=THEME.font(size=18, weight="bold"),
            text_color=THEME.TEXT_PRIMARY
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            empty,
            text="Import .po files to get started • Ctrl+O",
            font=THEME.font(size=13),
            text_color=THEME.TEXT_MUTED
        ).pack()
    
    def populate(self, entries, merger, status_map=None, page=1, page_size=50):
        """
        Populate table with entries

        Args:
            entries: List of PO entries to display
            merger: POMerger instance for module lookup
            page: The page to display (1-indexed)
            page_size: Number of entries per page (0/None to show all)
        """
        for widget in self.table.winfo_children():
            widget.destroy()

        self.entries = entries
        self.status_map = status_map or {}
        self.page = max(1, page)
        self.page_size = page_size or 0

        total_entries = len(entries)

        if self.page_size:
            self.total_pages = max(1, math.ceil(total_entries / self.page_size)) if total_entries else 1
            start = (self.page - 1) * self.page_size
            end = min(start + self.page_size, total_entries)
        else:
            self.total_pages = 1 if total_entries else 1
            start = 0
            end = total_entries

        if total_entries and start >= total_entries:
            if self.page_size > 0:
                start = max(0, (self.total_pages - 1) * self.page_size)
            else:
                start = 0
            end = total_entries

        self.visible_entries = entries[start:end]

        if not entries:
            self.header_select_var.set(False)
            self.show_empty_state()
            self.update_pagination_bar(0, 0, 0)
            self.update_selection_controls()
            return

        # Create rows
        for idx, entry in enumerate(self.visible_entries):
            self.create_row(idx, entry, merger)

        self.update_pagination_bar(start, end, total_entries)
        self.update_selection_controls()

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
            width=28,
            command=lambda: self.toggle_selection(entry, var.get()),
            fg_color=THEME.ACCENT_PRIMARY,
            hover_color=THEME.ACCENT_PRIMARY_HOVER,
        )
        checkbox.grid(row=idx, column=0, padx=14, pady=6)
        
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
            font=THEME.font(size=18),
            text_color=THEME.TEXT_SECONDARY,
        ).grid(row=idx, column=1, padx=5, pady=6)
        
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
            corner_radius=10,
            cursor="hand2",
        )
        src_frame.grid(row=idx, column=2, padx=10, pady=6, sticky="ew")
        
        src_text = entry.msgid[:150] + ("..." if len(entry.msgid) > 150 else "")
        ctk.CTkLabel(
            src_frame,
            text=src_text,
            anchor="w",
            font=THEME.font(size=12),
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
                font=THEME.font(size=10),
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
            corner_radius=10,
            cursor="hand2",
        )
        trans_frame.grid(row=idx, column=3, padx=10, pady=6, sticky="ew")
        
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
            font=THEME.font(size=12),
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
                font=THEME.font(size=10),
                text_color=info_color
            ).pack(padx=12, pady=(0, 10), fill="x")
        elif status and status.missing_translation:
            ctk.CTkLabel(
                trans_frame,
                text="Awaiting translation",
                anchor="w",
                font=THEME.font(size=10),
                text_color=THEME.ACCENT_DANGER
            ).pack(padx=12, pady=(0, 10), fill="x")
        
        # Module
        module = merger.indexer.get_module(entry.msgid)
        module_label = ctk.CTkLabel(
            self.table,
            text=module,
            width=150,
            fg_color=THEME.MODULE_CHIP_BG,
            corner_radius=16,
            text_color=THEME.MODULE_CHIP_TEXT,
            font=THEME.font(size=11, weight="bold"),
        )
        module_label.grid(row=idx, column=4, padx=10, pady=6)
        
        # Actions
        actions_frame = ctk.CTkFrame(self.table, fg_color="transparent")
        actions_frame.grid(row=idx, column=5, padx=10, pady=6)

        ctk.CTkButton(
            actions_frame,
            text="✏️",
            command=lambda: self.callbacks['edit'](entry),
            width=35,
            height=35,
            fg_color=THEME.SURFACE_RAISED,
            hover_color=THEME.SURFACE_HOVER,
            text_color=THEME.TEXT_PRIMARY,
            font=THEME.font(size=14),
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

        self.update_selection_controls()

        if self.callbacks.get('selection_changed'):
            self.callbacks['selection_changed']()

    def select_all(self):
        """Select all entries"""
        for entry in self.entries:
            self.selected_entries.add(id(entry))
        self.update_selection_controls()

    def clear_selection(self):
        """Clear all selections"""
        self.selected_entries.clear()
        self.update_selection_controls()

    def get_selected_count(self):
        """Get number of selected entries"""
        return len(self.selected_entries)

    def get_selected_entries(self, all_entries):
        """Get list of selected entry objects"""
        return [e for e in all_entries if id(e) in self.selected_entries]

    def update_selection_controls(self):
        """Refresh selection-dependent controls."""

        self.update_header_checkbox()
        if hasattr(self, "clear_selection_button"):
            state = "normal" if self.selected_entries else "disabled"
            self.clear_selection_button.configure(state=state)

    def update_header_checkbox(self):
        """Synchronise the header checkbox with the selection state."""

        if self._updating_header:
            return

        total = len(self.entries)
        desired = bool(total and len(self.selected_entries) == total)

        self._updating_header = True
        try:
            if self.header_select_var.get() != desired:
                self.header_select_var.set(desired)
            if total == 0:
                self.header_select_var.set(False)
        finally:
            self._updating_header = False

    def on_header_toggle(self):
        """Handle the master checkbox toggling all rows."""

        if self._updating_header:
            return

        if self.header_select_var.get():
            if self.callbacks.get('select_all'):
                self.callbacks['select_all']()
        else:
            if self.callbacks.get('clear_selection'):
                self.callbacks['clear_selection']()

    def on_page_change(self, new_page):
        """Request a page change through the controller."""

        if not self.callbacks.get('change_page'):
            return
        if new_page == self.page:
            return
        if new_page < 1:
            new_page = 1
        if self.total_pages and new_page > self.total_pages:
            new_page = self.total_pages
        self.callbacks['change_page'](new_page)

    def on_page_size_change(self, value: str):
        """Handle a change of the items-per-page option."""

        if self._updating_page_controls:
            return

        value = value.strip().lower()
        if value == "all":
            new_size = 0
        else:
            try:
                new_size = int(value)
            except ValueError:
                return

        if self.callbacks.get('change_page_size'):
            self.callbacks['change_page_size'](new_size)

    def update_pagination_bar(self, start: int, end: int, total: int):
        """Update pagination controls with the latest state."""

        if total <= 0:
            display_page = 0
            total_pages = 0
            range_text = "No entries to display"
            self.prev_button.configure(state="disabled")
            self.next_button.configure(state="disabled")
        else:
            display_page = min(self.page, self.total_pages)
            total_pages = self.total_pages
            start_display = start + 1
            end_display = max(start_display, end)
            if not self.page_size:
                range_text = f"Showing all {total} entries"
            else:
                range_text = f"Showing {start_display}-{end_display} of {total} entries"

            prev_state = "normal" if display_page > 1 else "disabled"
            next_state = "normal" if display_page < total_pages else "disabled"
            self.prev_button.configure(state=prev_state)
            self.next_button.configure(state=next_state)

        page_text = f"Page {display_page} of {total_pages}"
        self.page_label.configure(text=page_text)
        self.range_label.configure(text=range_text)

        new_value = "All" if not self.page_size else str(self.page_size)
        if self.page_size_var.get() != new_value:
            self._updating_page_controls = True
            self.page_size_var.set(new_value)
            self._updating_page_controls = False


