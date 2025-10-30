"""
Statistics Dialog
Dialog showing translation statistics and cache information
"""
import customtkinter as ctk

from ..theme import THEME


class StatisticsDialog:
    """Dialog for displaying statistics"""
    
    def __init__(self, parent, entries, translator, on_clear_cache_callback):
        """
        Initialize statistics dialog
        
        Args:
            parent: Parent window
            entries: List of all entries
            translator: Translator instance
            on_clear_cache_callback: Callback when cache is cleared
        """
        self.parent = parent
        self.entries = entries
        self.translator = translator
        self.on_clear_cache_callback = on_clear_cache_callback
        
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Statistics")
        self.dialog.geometry("600x500")
        
        # Wait for window to be visible before grabbing
        self.dialog.after(100, lambda: self.dialog.grab_set())
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        # Header
        header = ctk.CTkFrame(self.dialog, fg_color=THEME.SURFACE_ALT, height=60, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="📊  Translation Statistics",
            font=THEME.font(size=18, weight="bold"),
            text_color=THEME.TEXT_PRIMARY,
        ).pack(side="left", padx=25, pady=15)
        
        # Content
        content = ctk.CTkScrollableFrame(self.dialog)
        content.pack(fill="both", expand=True, padx=25, pady=20)
        
        # Calculate statistics
        from po_translator.utils.language import is_untranslated
        
        total = len(self.entries)
        translated = sum(1 for e in self.entries if not is_untranslated(e.msgid, e.msgstr))
        stats = self.translator.get_stats()
        
        stats_data = [
            ("Project Statistics", [
                ("Total Entries", str(total)),
                ("Translated", f"{translated} ({translated/max(1,total)*100:.1f}%)"),
                ("Untranslated", f"{total-translated} ({(total-translated)/max(1,total)*100:.1f}%)")
            ]),
            ("Translation Performance", [
                ("Total Requests", str(stats['total_requests'])),
                ("API Calls", str(stats['api_calls'])),
                ("Cache Hits", str(stats['cache_hits'])),
                ("Cache Hit Rate", stats['cache_hit_rate']),
                ("Errors", str(stats['errors'])),
                ("Retries", str(stats['retries']))
            ]),
            ("Cache Information", [
                ("Cache Entries", str(stats['cache_entries'])),
                ("API Efficiency", stats['api_efficiency'])
            ])
        ]
        
        for section, items in stats_data:
            section_frame = ctk.CTkFrame(content, fg_color=THEME.SURFACE_RAISED, corner_radius=12)
            section_frame.pack(fill="x", pady=(0, 15))
            
            ctk.CTkLabel(
                section_frame,
                text=section,
                font=THEME.font(size=14, weight="bold"),
                text_color=THEME.TEXT_PRIMARY,
                anchor="w"
            ).pack(padx=20, pady=(15, 10), fill="x")
            
            for label, value in items:
                row = ctk.CTkFrame(section_frame, fg_color="transparent")
                row.pack(fill="x", padx=20, pady=5)
                
                ctk.CTkLabel(
                    row,
                    text=label,
                    font=THEME.font(size=12),
                    text_color=THEME.TEXT_MUTED,
                    anchor="w"
                ).pack(side="left")

                ctk.CTkLabel(
                    row,
                    text=value,
                    font=THEME.font(size=12, weight="bold"),
                    text_color=THEME.ACCENT_SUCCESS,
                    anchor="e"
                ).pack(side="right")
            
            ctk.CTkFrame(section_frame, height=1, fg_color=THEME.DIVIDER).pack(pady=10, fill="x", padx=20)
        
        # Footer
        footer = ctk.CTkFrame(self.dialog, fg_color="transparent")
        footer.pack(fill="x", padx=25, pady=(0, 20))
        
        ctk.CTkButton(
            footer,
            text="Clear Cache",
            command=self.clear_cache,
            height=40,
            fg_color=THEME.ACCENT_DANGER,
            hover_color="#b91c1c",
            text_color="#ffffff",
            font=THEME.font(size=12, weight="bold"),
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            footer,
            text="Close",
            command=self.dialog.destroy,
            height=40,
            fg_color=THEME.SURFACE_RAISED,
            hover_color=THEME.SURFACE_HOVER,
            text_color=THEME.TEXT_PRIMARY,
            font=THEME.font(size=12),
        ).pack(side="left", fill="x", expand=True)
    
    def clear_cache(self):
        """Clear translation cache"""
        self.on_clear_cache_callback()
        self.dialog.destroy()

