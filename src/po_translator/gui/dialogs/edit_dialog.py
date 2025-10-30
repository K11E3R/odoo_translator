"""
Edit Dialog
Dialog for editing translation entries
"""
import customtkinter as ctk

from ..theme import THEME


class EditDialog:
    """Dialog for editing translation entries"""
    
    def __init__(self, parent, entry, merger, on_save_callback):
        """
        Initialize edit dialog
        
        Args:
            parent: Parent window
            entry: PO entry to edit
            merger: POMerger instance for module lookup
            on_save_callback: Callback function when save is clicked
        """
        self.parent = parent
        self.entry = entry
        self.merger = merger
        self.on_save_callback = on_save_callback
        
        # Store original values
        self.original_msgid = entry.msgid
        self.original_msgstr = entry.msgstr
        
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Edit Translation")
        self.dialog.geometry("900x700")
        
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
            text="✏️  Edit Translation",
            font=THEME.font(size=18, weight="bold"),
        ).pack(side="left", padx=25, pady=15)
        
        module = self.merger.indexer.get_module(self.entry.msgid)
        ctk.CTkLabel(
            header,
            text=f"Module: {module}",
            font=THEME.font(size=12),
            text_color="#10b981"
        ).pack(side="right", padx=25)
        
        # Content
        content = ctk.CTkFrame(self.dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=25, pady=20)
        
        ctk.CTkLabel(
            content,
            text="Source Text (English)",
            font=THEME.font(size=13, weight="bold"),
            anchor="w"
        ).pack(fill="x", pady=(0, 8))

        self.src_text = ctk.CTkTextbox(content, height=220, font=THEME.font(size=12))
        self.src_text.pack(fill="both", expand=True, pady=(0, 20))
        self.src_text.insert("1.0", self.entry.msgid)
        
        ctk.CTkLabel(
            content,
            text="Translation (French)",
            font=THEME.font(size=13, weight="bold"),
            anchor="w"
        ).pack(fill="x", pady=(0, 8))

        self.trans_text = ctk.CTkTextbox(content, height=220, font=THEME.font(size=12))
        self.trans_text.pack(fill="both", expand=True)
        self.trans_text.insert("1.0", self.entry.msgstr)
        
        # Footer
        footer = ctk.CTkFrame(self.dialog, fg_color="transparent")
        footer.pack(fill="x", padx=25, pady=(0, 20))

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
            text="💾  Save Changes",
            command=self.save,
            height=45,
            fg_color=THEME.ACCENT_PRIMARY,
            hover_color=THEME.ACCENT_PRIMARY_HOVER,
            text_color="#ffffff",
            font=THEME.font(size=13, weight="bold")
        ).pack(side="left", fill="x", expand=True)
    
    def save(self):
        """Save changes"""
        new_msgid = self.src_text.get("1.0", "end-1c").strip()
        new_msgstr = self.trans_text.get("1.0", "end-1c").strip()
        
        # Call callback with old and new values
        self.on_save_callback(
            self.entry,
            self.original_msgid,
            self.original_msgstr,
            new_msgid,
            new_msgstr
        )
        
        self.dialog.destroy()

