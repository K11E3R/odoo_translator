"""
Sidebar Component
Left sidebar with file operations, translation controls, and statistics
"""
import customtkinter as ctk


class Sidebar:
    """Sidebar component with controls and statistics"""
    
    def __init__(self, parent, callbacks):
        """
        Initialize sidebar
        
        Args:
            parent: Parent widget
            callbacks: Dict of callback functions
        """
        self.parent = parent
        self.callbacks = callbacks
        self.translation_enabled = False
        self.has_selection = False
        self.btn_delete = None

        # Scrollable sidebar frame
        self.frame = ctk.CTkScrollableFrame(
            parent,
            width=320,
            corner_radius=0,
            fg_color="#1e1e1e",
            scrollbar_button_color="#2a2a2a",
            scrollbar_button_hover_color="#3a3a3a"
        )
        self.frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        # Note: CTkScrollableFrame doesn't support grid_propagate
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup sidebar UI"""
        self.create_header()
        self.create_separator(1)
        self.create_file_section()
        self.create_translation_section()
        self.create_actions_section()
        self.create_stats_section()
        self.create_footer()
    
    def create_header(self):
        """Create header with better spacing"""
        header = ctk.CTkFrame(self.frame, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(32, 24), sticky="ew")
        
        ctk.CTkLabel(
            header,
            text="⚡ PO Translator",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#ffffff"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header,
            text="Professional Odoo Translation Tool",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        ).pack(anchor="w", pady=(8, 0))
    
    def create_separator(self, row):
        """Create separator line"""
        ctk.CTkFrame(self.frame, height=1, fg_color="#333333").grid(
            row=row, column=0, sticky="ew", padx=20, pady=(0, 20)
        )
    
    def create_file_section(self):
        """Create file operations section"""
        self.create_section_label("FILE OPERATIONS", 2)
        
        self.btn_import = self.create_button(
            "📁  Import Files", self.callbacks['import_files'], 3, "#2563eb"
        )
        
        self.btn_save = self.create_button(
            "💾  Save", self.callbacks['save_file'], 4, "#059669", disabled=True
        )
        
        self.btn_export = self.create_button(
            "📤  Export", self.callbacks['show_export_dialog'], 5, "#7c3aed", disabled=True
        )
    
    def create_translation_section(self):
        """Create translation section"""
        self.create_section_label("AI TRANSLATION", 6)
        
        self.api_key_entry = ctk.CTkEntry(
            self.frame,
            placeholder_text="Enter Gemini API Key",
            show="•",
            height=40,
            border_width=0,
            fg_color="#2a2a2a"
        )
        self.api_key_entry.grid(row=7, column=0, padx=20, pady=(0, 8), sticky="ew")
        
        self.create_button(
            "🔑  Save API Key", self.callbacks['save_api_key'], 8, "#374151", height=35
        )
        
        # Language selection
        lang_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        lang_frame.grid(row=9, column=0, padx=20, pady=(10, 8), sticky="ew")
        lang_frame.grid_columnconfigure(0, weight=1)
        lang_frame.grid_columnconfigure(1, weight=1)
        
        # Source language
        ctk.CTkLabel(
            lang_frame,
            text="Source:",
            font=ctk.CTkFont(size=10),
            text_color="#888888",
            anchor="w"
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))
        
        self.source_lang_var = ctk.StringVar(value="English")
        self.source_lang_menu = ctk.CTkOptionMenu(
            lang_frame,
            variable=self.source_lang_var,
            values=["English", "French", "Spanish", "German", "Italian", "Portuguese", "Dutch", "Arabic"],
            command=self.callbacks.get('language_changed'),
            height=32,
            fg_color="#2a2a2a",
            button_color="#374151",
            font=ctk.CTkFont(size=11)
        )
        self.source_lang_menu.grid(row=1, column=0, sticky="ew", padx=(0, 5))
        
        # Target language
        ctk.CTkLabel(
            lang_frame,
            text="Target:",
            font=ctk.CTkFont(size=10),
            text_color="#888888",
            anchor="w"
        ).grid(row=0, column=1, sticky="w", pady=(0, 4))
        
        self.target_lang_var = ctk.StringVar(value="French")
        self.target_lang_menu = ctk.CTkOptionMenu(
            lang_frame,
            variable=self.target_lang_var,
            values=["English", "French", "Spanish", "German", "Italian", "Portuguese", "Dutch", "Arabic"],
            command=self.callbacks.get('language_changed'),
            height=32,
            fg_color="#2a2a2a",
            button_color="#374151",
            font=ctk.CTkFont(size=11)
        )
        self.target_lang_menu.grid(row=1, column=1, sticky="ew", padx=(5, 0))
        
        # Auto-detect checkbox (disabled by default for speed)
        self.auto_detect_var = ctk.BooleanVar(value=True)
        self.auto_detect_check = ctk.CTkCheckBox(
            self.frame,
            text="Auto-detect & correct language",
            variable=self.auto_detect_var,
            command=self.callbacks.get('language_changed'),
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        )
        self.auto_detect_check.grid(row=10, column=0, padx=20, pady=(0, 8), sticky="w")
        
        self.btn_translate = ctk.CTkButton(
            self.frame,
            text="🌐  Translate All",
            command=self.callbacks['translate_all'],
            height=55,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            corner_radius=8,
            state="disabled"
        )
        self.btn_translate.grid(row=11, column=0, padx=20, pady=(15, 8), sticky="ew")
        
        self.btn_translate_selected = ctk.CTkButton(
            self.frame,
            text="✓  Translate Selected",
            command=self.callbacks['translate_selected'],
            height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#0891b2",
            hover_color="#0e7490",
            corner_radius=8,
            state="disabled"
        )
        self.btn_translate_selected.grid(row=12, column=0, padx=20, pady=(0, 0), sticky="ew")
    
    def create_actions_section(self):
        """Create actions section"""
        self.create_section_label("ACTIONS", 13)
        
        actions_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        actions_frame.grid(row=14, column=0, padx=20, pady=(0, 8), sticky="ew")
        actions_frame.grid_columnconfigure(0, weight=1)
        actions_frame.grid_columnconfigure(1, weight=1)
        
        self.btn_undo = ctk.CTkButton(
            actions_frame,
            text="↶ Undo",
            command=self.callbacks['undo'],
            height=38,
            fg_color="#374151",
            hover_color="#1f2937",
            state="disabled"
        )
        self.btn_undo.grid(row=0, column=0, padx=(0, 4), sticky="ew")
        
        self.btn_redo = ctk.CTkButton(
            actions_frame,
            text="↷ Redo",
            command=self.callbacks['redo'],
            height=38,
            fg_color="#374151",
            hover_color="#1f2937",
            state="disabled"
        )
        self.btn_redo.grid(row=0, column=1, padx=(4, 0), sticky="ew")

        self.btn_delete = ctk.CTkButton(
            actions_frame,
            text="🗑️ Delete Selected",
            command=self.callbacks['delete_selected'],
            height=38,
            fg_color="#991b1b",
            hover_color="#7f1d1d",
            state="disabled"
        )
        self.btn_delete.grid(row=1, column=0, columnspan=2, pady=(8, 0), sticky="ew")

        self.create_button(
            "📊  Statistics", self.callbacks['show_statistics'], 15, "#6366f1", height=38
        )
    
    def create_stats_section(self):
        """Create statistics section"""
        self.create_section_label("STATISTICS", 16)
        
        stats_frame = ctk.CTkFrame(self.frame, fg_color="#2a2a2a", corner_radius=8)
        stats_frame.grid(row=17, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        self.lbl_total = self.create_stat_label(stats_frame, "Total Entries", "0", 0)
        self.lbl_translated = self.create_stat_label(stats_frame, "✅ Translated", "0", 1, "#10b981")
        self.lbl_untranslated = self.create_stat_label(stats_frame, "⏳ Pending", "0", 2, "#f59e0b")
        self.lbl_selected = self.create_stat_label(stats_frame, "☑ Selected", "0", 3, "#3b82f6")
    
    def create_footer(self):
        """Create footer"""
        footer = ctk.CTkFrame(self.frame, fg_color="transparent")
        footer.grid(row=18, column=0, padx=20, pady=20, sticky="s")
        
        ctk.CTkLabel(
            footer,
            text="v1.0 • Made with ❤️ for Odoo",
            font=ctk.CTkFont(size=11),
            text_color="#666666"
        ).pack()
    
    def create_section_label(self, text, row):
        """Create section label with better styling"""
        ctk.CTkLabel(
            self.frame,
            text=text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#888888",
            anchor="w"
        ).grid(row=row, column=0, padx=24, pady=(24, 12), sticky="w")
    
    def create_button(self, text, command, row, color, height=44, disabled=False):
        """Create button with improved styling"""
        btn = ctk.CTkButton(
            self.frame,
            text=text,
            command=command,
            height=height,
            fg_color=color,
            hover_color=self.darken_color(color),
            corner_radius=10,
            border_width=0,
            font=ctk.CTkFont(size=13, weight="bold"),
            state="disabled" if disabled else "normal"
        )
        btn.grid(row=row, column=0, padx=24, pady=(0, 10), sticky="ew")
        return btn
    
    def create_stat_label(self, parent, label, value, row, color="#888888"):
        """Create stat label"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=8)
        
        ctk.CTkLabel(
            frame,
            text=label,
            font=ctk.CTkFont(size=11),
            text_color="#666666",
            anchor="w"
        ).pack(side="left")
        
        lbl = ctk.CTkLabel(
            frame,
            text=value,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=color,
            anchor="e"
        )
        lbl.pack(side="right")
        return lbl
    
    def darken_color(self, hex_color):
        """Darken hex color"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = max(0, r-30), max(0, g-30), max(0, b-30)
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def update_stats(self, total, translated, untranslated, selected):
        """Update statistics display"""
        self.lbl_total.configure(text=str(total))
        self.lbl_translated.configure(text=str(translated))
        self.lbl_untranslated.configure(text=str(untranslated))
        self.lbl_selected.configure(text=str(selected))
        self.set_selection_actions_enabled(selected > 0)
    
    def update_undo_redo(self, can_undo, can_redo):
        """Update undo/redo button states"""
        self.btn_undo.configure(state="normal" if can_undo else "disabled")
        self.btn_redo.configure(state="normal" if can_redo else "disabled")

    def enable_translation_buttons(self):
        """Enable translation buttons"""
        self.translation_enabled = True
        self._update_translation_buttons()

    def disable_translation_buttons(self):
        """Disable translation buttons"""
        self.translation_enabled = False
        self._update_translation_buttons()

    def enable_file_buttons(self):
        """Enable file operation buttons"""
        self.btn_save.configure(state="normal")
        self.btn_export.configure(state="normal")

    def disable_file_buttons(self):
        """Disable file operation buttons"""
        self.btn_save.configure(state="disabled")
        self.btn_export.configure(state="disabled")

    def set_selection_actions_enabled(self, has_selection):
        """Enable/disable selection dependent actions"""
        self.has_selection = has_selection
        state = "normal" if has_selection else "disabled"
        if self.btn_delete:
            self.btn_delete.configure(state=state)
        self._update_translation_buttons()

    def _update_translation_buttons(self):
        """Update translation button states based on current flags"""
        translate_state = "normal" if self.translation_enabled else "disabled"
        selected_state = "normal" if self.translation_enabled and self.has_selection else "disabled"
        self.btn_translate.configure(state=translate_state)
        self.btn_translate_selected.configure(state=selected_state)
    
    def get_language_settings(self):
        """Get current language settings"""
        lang_map = {
            "English": "en",
            "French": "fr",
            "Spanish": "es",
            "German": "de",
            "Italian": "it",
            "Portuguese": "pt",
            "Dutch": "nl",
            "Arabic": "ar"
        }
        return {
            'source': lang_map.get(self.source_lang_var.get(), 'en'),
            'target': lang_map.get(self.target_lang_var.get(), 'fr'),
            'auto_detect': self.auto_detect_var.get()
        }

