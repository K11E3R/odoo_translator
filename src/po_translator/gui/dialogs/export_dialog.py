"""
Export Dialog
Dialog for configuring export options
"""
import os
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox

from ..theme import THEME


class ExportDialog:
    """Dialog for export options"""
    
    def __init__(self, parent, entries, merger, on_export_callback):
        """
        Initialize export dialog
        
        Args:
            parent: Parent window
            entries: List of entries to export
            merger: POMerger instance
            on_export_callback: Callback function when export is confirmed
        """
        self.parent = parent
        self.entries = entries
        self.merger = merger
        self.on_export_callback = on_export_callback
        
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Export Options")
        self.dialog.geometry("500x400")
        
        # Wait for window to be visible before grabbing
        self.dialog.after(100, lambda: self.dialog.grab_set())
        
        self.export_translated = ctk.BooleanVar(value=True)
        self.export_untranslated = ctk.BooleanVar(value=False)
        self.compile_mo = ctk.BooleanVar(value=True)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        # Header
        header = ctk.CTkFrame(self.dialog, fg_color=THEME.SURFACE_ALT, height=60, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="📤  Export Translation File",
            font=THEME.font(size=18, weight="bold"),
            text_color=THEME.TEXT_PRIMARY,
        ).pack(side="left", padx=25, pady=15)
        
        # Content
        content = ctk.CTkFrame(self.dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=25, pady=20)
        
        ctk.CTkLabel(
            content,
            text="Export Options:",
            font=THEME.font(size=14, weight="bold"),
            anchor="w"
        ).pack(fill="x", pady=(0, 15))

        ctk.CTkCheckBox(
            content,
            text="Include translated entries",
            variable=self.export_translated,
            font=THEME.font(size=12),
            hover_color=THEME.ACCENT_PRIMARY_HOVER,
            fg_color=THEME.ACCENT_PRIMARY,
        ).pack(anchor="w", pady=8)

        ctk.CTkCheckBox(
            content,
            text="Include untranslated entries",
            variable=self.export_untranslated,
            font=THEME.font(size=12),
            hover_color=THEME.ACCENT_PRIMARY_HOVER,
            fg_color=THEME.ACCENT_PRIMARY,
        ).pack(anchor="w", pady=8)

        ctk.CTkCheckBox(
            content,
            text="Compile .mo file",
            variable=self.compile_mo,
            font=THEME.font(size=12),
            hover_color=THEME.ACCENT_PRIMARY_HOVER,
            fg_color=THEME.ACCENT_PRIMARY,
        ).pack(anchor="w", pady=8)

        # Footer
        footer = ctk.CTkFrame(self.dialog, fg_color="transparent")
        footer.pack(fill="x", padx=25, pady=(0, 20), side="bottom")

        ctk.CTkButton(
            footer,
            text="Cancel",
            command=self.dialog.destroy,
            height=45,
            fg_color=THEME.SURFACE_RAISED,
            hover_color=THEME.SURFACE_HOVER,
            text_color=THEME.TEXT_PRIMARY,
            font=THEME.font(size=13)
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            footer,
            text="📤  Export",
            command=self.export,
            height=45,
            fg_color=THEME.ACCENT_SECONDARY,
            hover_color=THEME.ACCENT_SECONDARY_HOVER,
            text_color="#ffffff",
            font=THEME.font(size=13, weight="bold")
        ).pack(side="left", fill="x", expand=True)
    
    def export(self):
        """Execute export"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".po",
            filetypes=[("PO Files", "*.po")],
            initialfile=f"fr_translated_{datetime.now().strftime('%Y%m%d')}.po"
        )
        
        if filename:
            # Export file
            self.merger.export_to_file(filename)
            
            # Compile .mo if requested
            if self.compile_mo.get():
                mo_file = filename.replace('.po', '.mo')
                self.merger.compile_mo(filename, mo_file)
                message = f"Exported to:\n{filename}\n{mo_file}"
            else:
                message = f"Exported to:\n{filename}"
            
            self.on_export_callback(filename, self.compile_mo.get())
            self.dialog.destroy()
            messagebox.showinfo("Success", message)

