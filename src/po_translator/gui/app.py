"""
Main Application
Orchestrates all GUI components and business logic
"""
import os
import threading
from collections import Counter
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple
from tkinter import filedialog, messagebox

try:
    import customtkinter as ctk
except ImportError:
    print("Error: Install dependencies with: pip install -r requirements.txt")
    exit(1)

from po_translator.core.merger import POMerger
from po_translator.translator import Translator
from po_translator.utils.language import detect_language, detect_language_details, is_untranslated
from po_translator.utils.logger import get_logger

from .components import Sidebar, Toolbar, TranslationTable, StatusBar
from .dialogs import EditDialog, ExportDialog, StatisticsDialog
from .widgets import UndoManager

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


@dataclass(frozen=True)
class EntryLanguageStatus:
    """Language analysis for a PO entry."""

    source_lang: Optional[str]
    source_confidence: float
    translation_lang: Optional[str]
    translation_confidence: float
    source_matches: Optional[bool]
    translation_matches: Optional[bool]
    missing_translation: bool


class POTranslatorApp:
    """Main PO Translator Application"""

    def __init__(self):
        self.logger = get_logger('po_translator.gui')
        
        # Core components
        self.merger = POMerger()
        self.translator = Translator()
        self.undo_manager = UndoManager()

        # Language configuration state
        self._updating_language_controls = False
        self._manual_language_override = False

        # State
        self.entries = []
        self.filtered_entries = []
        self.unsaved = False
        self.translating = False
        self._language_analysis_cache: Dict[int, tuple] = {}
        
        # Window
        self.root = ctk.CTk()
        self.root.title("PO Translator • Advanced Odoo Translation Tool")
        self.root.geometry("1500x900")
        
        # Ensure window decorations are visible (for WSL/Linux)
        self.root.resizable(True, True)
        self.root.minsize(1200, 700)
        
        self.setup_ui()
        self.load_config()
        self.setup_shortcuts()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.apply_language_settings(show_status=False)

        self.logger.info("Application initialized")
    
    def setup_ui(self):
        """Setup UI components"""
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        # Create callbacks dict
        callbacks = {
            'import_files': self.import_files,
            'save_file': self.save_file,
            'show_export_dialog': self.show_export_dialog,
            'save_api_key': self.save_api_key,
            'translate_all': self.translate_all,
            'translate_selected': self.translate_selected,
            'undo': self.undo,
            'redo': self.redo,
            'show_statistics': self.show_statistics,
            'search': self.search,
            'apply_filter': self.apply_filter,
            'select_all': self.select_all,
            'clear_selection': self.clear_selection,
            'delete_selected': self.delete_selected,
            'edit': self.edit_entry,
            'selection_changed': self.on_selection_changed,
            'language_changed': self.on_language_changed
        }
        
        # Create components
        self.sidebar = Sidebar(self.root, callbacks)
        self.sidebar.disable_file_buttons()

        # Content area
        content = ctk.CTkFrame(self.root, corner_radius=0, fg_color="#0f0f0f")
        content.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        content.grid_rowconfigure(2, weight=1)
        content.grid_columnconfigure(0, weight=1)
        
        self.toolbar = Toolbar(content, callbacks)
        self.table = TranslationTable(content, callbacks)
        self.statusbar = StatusBar(self.root)
        
        self.table.show_empty_state()
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.root.bind("<Control-o>", lambda e: self.import_files())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-e>", lambda e: self.show_export_dialog())
        self.root.bind("<Control-f>", lambda e: self.toolbar.focus_search())
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Control-a>", lambda e: self.select_all())
        self.root.bind("<F5>", lambda e: self.refresh())
        self.root.bind("<Escape>", lambda e: self.toolbar.clear_search())
        self.root.bind("<Delete>", lambda e: self.delete_selected())
    
    def load_config(self):
        """Load saved configuration"""
        config = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.config')
        if os.path.exists(config):
            try:
                with open(config) as f:
                    key = f.read().strip()
                    if key:
                        self.sidebar.api_key_entry.insert(0, key)
                        self.translator.set_api_key(key)
            except:
                pass
    
    def save_api_key(self):
        """Save API key"""
        key = self.sidebar.api_key_entry.get().strip()
        if not key:
            messagebox.showerror("Error", "Please enter an API key")
            return
        
        config = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.config')
        try:
            with open(config, 'w') as f:
                f.write(key)
        except:
            pass
        
        self.translator.set_api_key(key)
        self.apply_language_settings(show_status=False)

        if self.entries:
            self.sidebar.enable_translation_buttons()

        self.statusbar.set_status("✅ API key saved successfully")
        messagebox.showinfo("Success", "API key saved! Translation features are now enabled.")
    
    def import_files(self):
        """Import PO files with progress tracking"""
        if not self.confirm_discard_changes("to import new files"):
            return

        files = filedialog.askopenfilenames(
            title="Select PO Files",
            filetypes=[("PO Files", "*.po"), ("All Files", "*.*")]
        )
        
        if not files:
            return
        
        self.statusbar.set_status(f"Loading {len(files)} file(s)...", True, "0%")
        self.sidebar.btn_import.configure(state="disabled")
        
        def worker():
            # Load files with progress
            self.root.after(0, lambda: self.statusbar.set_status("📂 Loading PO files...", True, "10%"))
            self.root.after(0, lambda: self.statusbar.set_progress(0.1))
            
            merged = self.merger.merge_files(list(files))
            
            self.root.after(0, lambda: self.statusbar.set_status("🔄 Processing entries...", True, "50%"))
            self.root.after(0, lambda: self.statusbar.set_progress(0.5))
            
            entries = list(merged.values())
            
            self.root.after(0, lambda: self.statusbar.set_status("✨ Rendering...", True, "90%"))
            self.root.after(0, lambda: self.statusbar.set_progress(0.9))
            
            self.root.after(0, lambda: self.on_import(entries))
        
        threading.Thread(target=worker, daemon=True).start()
    
    def on_import(self, entries):
        """Handle import completion"""
        self.invalidate_language_analysis()
        self.entries = entries
        self.filtered_entries = entries
        self.table.clear_selection()
        self.undo_manager.clear()
        self.unsaved = False
        self.populate()

        self.sidebar.btn_import.configure(state="normal")
        auto_configured = False
        if self.entries:
            self.sidebar.enable_file_buttons()
            if not self._manual_language_override:
                auto_configured = self.auto_configure_languages()
        else:
            self.sidebar.disable_file_buttons()

        if self.sidebar.api_key_entry.get().strip():
            self.sidebar.enable_translation_buttons()

        if not auto_configured:
            self.statusbar.set_status(f"✅ Imported {len(entries)} entries successfully")
    
    def populate(self):
        """Populate table"""
        status_map = self.build_language_status_map(self.filtered_entries)
        self.table.populate(self.filtered_entries, self.merger, status_map=status_map)
        self.update_stats()
        self.update_entry_status_message()

    def invalidate_language_analysis(self, entries: Optional[Iterable] = None):
        """Invalidate cached language analysis for entries."""

        if entries is None:
            self._language_analysis_cache.clear()
            return

        entry_ids = {id(entry) for entry in entries}
        for entry_id in list(self._language_analysis_cache.keys()):
            if entry_id in entry_ids:
                self._language_analysis_cache.pop(entry_id, None)

    def build_language_status_map(self, entries: Iterable) -> Dict[int, EntryLanguageStatus]:
        """Analyse languages for a batch of entries."""

        status_map: Dict[int, EntryLanguageStatus] = {}
        for entry in entries:
            try:
                status_map[id(entry)] = self.get_entry_language_status(entry)
            except Exception as exc:
                self.logger.debug("Language analysis failed for entry: %s", exc)
        return status_map

    def get_entry_language_status(self, entry) -> EntryLanguageStatus:
        """Return language analysis for a single entry with caching."""

        entry_id = id(entry)
        expected_source = self.translator.source_lang
        expected_target = self.translator.target_lang

        msgid = (entry.msgid or "").strip()
        msgstr = (entry.msgstr or "").strip()

        cached = self._language_analysis_cache.get(entry_id)
        if cached:
            cached_msgid, cached_msgstr, cached_source, cached_target, status = cached
            if (
                cached_msgid == msgid
                and cached_msgstr == msgstr
                and cached_source == expected_source
                and cached_target == expected_target
            ):
                return status

        src_lang, src_conf = detect_language_details(msgid)
        missing_translation = is_untranslated(entry.msgid, entry.msgstr)

        trans_lang, trans_conf = (None, 0.0)
        if not missing_translation and msgstr:
            trans_lang, trans_conf = detect_language_details(msgstr)

        source_matches = (src_lang == expected_source) if src_lang else None
        translation_matches: Optional[bool]
        if missing_translation:
            translation_matches = None
        elif trans_lang:
            translation_matches = trans_lang == expected_target
        else:
            translation_matches = False

        status = EntryLanguageStatus(
            source_lang=src_lang,
            source_confidence=src_conf,
            translation_lang=trans_lang,
            translation_confidence=trans_conf,
            source_matches=source_matches,
            translation_matches=translation_matches,
            missing_translation=missing_translation,
        )

        self._language_analysis_cache[entry_id] = (
            msgid,
            msgstr,
            expected_source,
            expected_target,
            status,
        )
        return status

    def validate_entries_for_translation(self, entries: Iterable) -> Tuple[bool, bool, List]:
        """Validate source/translation languages before sending to the API.

        Returns a tuple of (should_continue, force_translation, retranslate_entries).
        """

        entries = list(entries)
        if not entries:
            return True, False, []

        statuses = [self.get_entry_language_status(entry) for entry in entries]
        expected_source = self.translator.source_lang
        expected_target = self.translator.target_lang

        mismatched_sources = [s for s in statuses if s.source_matches is False]
        mismatched_targets = [s for s in statuses if s.translation_matches is False and not s.missing_translation]

        if not mismatched_sources and not mismatched_targets:
            return True, False, []

        lang_names = {code: data.get("name", code.upper()) for code, data in self.translator.LANGUAGES.items()}
        source_counts = Counter(s.source_lang for s in mismatched_sources if s.source_lang)
        target_counts = Counter(s.translation_lang for s in mismatched_targets if s.translation_lang)

        def format_counts(counts: Counter) -> str:
            if not counts:
                return "unknown"
            parts = []
            for code, count in counts.items():
                label = lang_names.get(code, code.upper())
                parts.append(f"{label} × {count}")
            return ", ".join(parts)

        message_lines: List[str] = [
            "Some entries do not match the selected language pair:",
            "",
        ]

        if mismatched_sources:
            expected = lang_names.get(expected_source, expected_source.upper())
            message_lines.append(f"• Source expected {expected}, detected {format_counts(source_counts)}")

        if mismatched_targets:
            expected = lang_names.get(expected_target, expected_target.upper())
            message_lines.append(f"• Translation expected {expected}, detected {format_counts(target_counts)}")

        message_lines.append("")
        message_lines.append("Continue with translation anyway?")

        proceed = messagebox.askyesno("Language Mismatch", "\n".join(message_lines))
        if not proceed:
            return False, False, []

        retranslate_entries: List = [
            entry
            for entry, status in zip(entries, statuses)
            if status.translation_matches is False and not status.missing_translation
        ]

        return True, bool(retranslate_entries), retranslate_entries
    def update_stats(self):
        """Update statistics display"""
        total = len(self.filtered_entries)
        translated = sum(1 for e in self.filtered_entries if not is_untranslated(e.msgid, e.msgstr))
        selected = self.table.get_selected_count()
        
        self.sidebar.update_stats(total, translated, total - translated, selected)
        self.sidebar.update_undo_redo(self.undo_manager.can_undo(), self.undo_manager.can_redo())
    
    def on_selection_changed(self):
        """Handle selection change"""
        self.update_stats()
    
    def search(self):
        """Search entries"""
        query = self.toolbar.get_search_query()
        
        if not query:
            self.filtered_entries = self.entries
        else:
            self.filtered_entries = [
                e for e in self.entries
                if query in e.msgid.lower() or query in e.msgstr.lower()
            ]
        
        self.apply_filter()
    
    def apply_filter(self):
        """Apply filter"""
        filter_type = self.toolbar.get_filter_value()
        query = self.toolbar.get_search_query()
        
        # Start with all entries
        base = self.entries
        
        # Apply search
        if query:
            base = [e for e in base if query in e.msgid.lower() or query in e.msgstr.lower()]
        
        # Apply filter
        if filter_type == "translated":
            self.filtered_entries = [e for e in base if not is_untranslated(e.msgid, e.msgstr)]
        elif filter_type == "untranslated":
            self.filtered_entries = [e for e in base if is_untranslated(e.msgid, e.msgstr)]
        else:
            self.filtered_entries = base
        
        self.populate()
    
    def select_all(self):
        """Select all entries"""
        self.table.select_all()
        self.populate()
        self.statusbar.set_status(f"✓ Selected {self.table.get_selected_count()} entries")
    
    def clear_selection(self):
        """Clear selection"""
        self.table.clear_selection()
        self.populate()
        self.statusbar.set_status("Selection cleared")
    
    def edit_entry(self, entry):
        """Edit entry"""
        def on_save(entry, old_msgid, old_msgstr, new_msgid, new_msgstr):
            # Record undo
            self.undo_manager.record('edit', {
                'entry': entry,
                'old_msgid': old_msgid,
                'old_msgstr': old_msgstr,
                'new_msgid': new_msgid,
                'new_msgstr': new_msgstr
            })
            
            entry.msgid = new_msgid
            entry.msgstr = new_msgstr
            self.unsaved = True
            self.invalidate_language_analysis(entries=[entry])
            self.populate()
            self.statusbar.set_status("✏️ Entry updated")
        
        EditDialog(self.root, entry, self.merger, on_save)
    
    def translate_all(self):
        """Translate all untranslated entries"""
        if self.translating:
            messagebox.showinfo("Translation in Progress", "Please wait for the current translation to finish.")
            return

        if not self.translator.model:
            messagebox.showerror("Error", "Please save your API key first")
            return

        self.apply_language_settings(show_status=False)

        if not self.entries:
            messagebox.showinfo("Info", "No entries loaded to translate.")
            return

        self.invalidate_language_analysis(entries=self.entries)
        proceed, force_due_to_mismatch, flagged_entries = self.validate_entries_for_translation(self.entries)
        if not proceed:
            return

        entries_to_translate: List = []
        seen_ids = set()

        for entry in self.entries:
            if is_untranslated(entry.msgid, entry.msgstr):
                entries_to_translate.append(entry)
                seen_ids.add(id(entry))

        flagged_ids = {id(entry) for entry in flagged_entries}
        for entry in flagged_entries:
            if id(entry) not in seen_ids:
                entries_to_translate.append(entry)
                seen_ids.add(id(entry))

        if not entries_to_translate:
            messagebox.showinfo("Info", "All entries already match the configured languages.")
            return

        est_time = len(entries_to_translate) * 4 // 60
        prompt_lines = [
            f"Translate {len(entries_to_translate)} entries?",
        ]
        if flagged_ids:
            prompt_lines.append(f"Re-checking {len(flagged_ids)} existing translation(s).")
        prompt_lines.extend([
            "",
            f"Estimated time: ~{est_time} minute{'s' if est_time != 1 else ''}",
            "This will use your Gemini API quota.",
        ])
        if not messagebox.askyesno("Confirm Translation", "\n".join(prompt_lines)):
            return

        force = force_due_to_mismatch or bool(flagged_ids)
        self.start_translation(entries_to_translate, force=force)

    def translate_selected(self):
        """Translate selected entries"""
        if self.translating:
            messagebox.showinfo("Translation in Progress", "Please wait for the current translation to finish.")
            return

        if not self.translator.model:
            messagebox.showerror("Error", "Please save your API key first")
            return
        if self.table.get_selected_count() == 0:
            messagebox.showwarning("Warning", "Please select entries to translate")
            return

        selected = self.table.get_selected_entries(self.entries)
        if not selected:
            messagebox.showinfo("Info", "No selectable entries found for translation.")
            return

        self.apply_language_settings(show_status=False)
        self.invalidate_language_analysis(entries=selected)

        proceed, force_due_to_mismatch, flagged_entries = self.validate_entries_for_translation(selected)
        if not proceed:
            return

        entries_to_translate: List = []
        seen_ids = set()
        for entry in selected:
            if is_untranslated(entry.msgid, entry.msgstr):
                entries_to_translate.append(entry)
                seen_ids.add(id(entry))

        flagged_ids = {id(entry) for entry in flagged_entries}
        for entry in flagged_entries:
            if id(entry) not in seen_ids:
                entries_to_translate.append(entry)
                seen_ids.add(id(entry))

        if not entries_to_translate:
            messagebox.showinfo("Info", "Selected entries already match the configured languages.")
            return

        est_time = len(entries_to_translate) * 4 // 60
        prompt_lines = [
            f"Translate {len(entries_to_translate)} selected entries?",
        ]
        if flagged_ids:
            prompt_lines.append(f"Re-checking {len(flagged_ids)} existing translation(s).")
        prompt_lines.extend([
            "",
            f"Estimated time: ~{est_time} minute{'s' if est_time != 1 else ''}",
        ])
        if not messagebox.askyesno("Confirm Translation", "\n".join(prompt_lines)):
            return

        force = force_due_to_mismatch or bool(flagged_ids)
        self.start_translation(entries_to_translate, force=force)

    def start_translation(self, entries_to_translate, force=False):
        """Start translation process with parallel processing"""
        self.apply_language_settings(show_status=False)
        self.translating = True
        self.statusbar.set_status("🌐 Translating entries...", True)
        self.sidebar.disable_translation_buttons()
        
        def worker():
            import concurrent.futures
            from queue import Queue
            
            total = len(entries_to_translate)
            completed = 0
            progress_queue = Queue()
            
            def translate_entry(entry):
                """Translate single entry"""
                if not self.translating:
                    return False
                module = self.merger.indexer.get_module(entry.msgid)
                return self.translator.auto_translate_entry(entry, module, force=force)
            
            # Use ThreadPoolExecutor for parallel translation (4 threads = 4x faster)
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = {executor.submit(translate_entry, entry): entry for entry in entries_to_translate}
                
                for future in concurrent.futures.as_completed(futures):
                    if not self.translating:
                        break
                    
                    try:
                        future.result()
                    except Exception as e:
                        self.logger.error(f"Translation error: {e}")
                    
                    completed += 1
                    progress = completed / total
                    percent = int(progress * 100)
                    self.root.after(0, lambda p=progress: self.statusbar.set_progress(p))
                    self.root.after(0, lambda c=completed, t=total, pct=percent: 
                                   self.statusbar.set_status(f"🌐 Translating: {c}/{t} ({pct}%)", True, f"{pct}%"))
            
            self.root.after(0, lambda items=entries_to_translate: self.invalidate_language_analysis(items))
            self.root.after(0, self.on_translate)
        
        threading.Thread(target=worker, daemon=True).start()
    
    def on_translate(self):
        """Translation complete"""
        self.translating = False
        self.populate()
        self.sidebar.enable_translation_buttons()
        self.statusbar.set_status("✅ Translation completed successfully!")
        self.unsaved = True

        # Show statistics
        stats = self.translator.get_stats()
        messagebox.showinfo(
            "Translation Complete",
            f"Translation finished!\n\n"
            f"API Calls: {stats['api_calls']}\n"
            f"Cache Hits: {stats['cache_hits']}\n"
            f"Errors: {stats['errors']}\n"
            f"Cache Hit Rate: {stats['cache_hit_rate']}"
        )
    
    def undo(self):
        """Undo last action"""
        action = self.undo_manager.undo()
        if action:
            if action['action'] == 'edit':
                data = action['data']
                data['entry'].msgid = data['old_msgid']
                data['entry'].msgstr = data['old_msgstr']
                self.invalidate_language_analysis(entries=[data['entry']])
                self.populate()
                self.statusbar.set_status("↶ Undone")
    
    def redo(self):
        """Redo last undone action"""
        action = self.undo_manager.redo()
        if action:
            if action['action'] == 'edit':
                data = action['data']
                data['entry'].msgid = data['new_msgid']
                data['entry'].msgstr = data['new_msgstr']
                self.invalidate_language_analysis(entries=[data['entry']])
                self.populate()
                self.statusbar.set_status("↷ Redone")
    
    def delete_selected(self):
        """Delete selected entries"""
        if self.table.get_selected_count() == 0:
            return
        
        if messagebox.askyesno("Confirm Delete", f"Delete {self.table.get_selected_count()} selected entries?"):
            selected_ids = set(self.table.selected_entries)
            for entry_id in selected_ids:
                self._language_analysis_cache.pop(entry_id, None)
            self.entries = [e for e in self.entries if id(e) not in selected_ids]
            self.table.clear_selection()
            self.apply_filter()
            self.unsaved = True
            if not self.entries:
                self.sidebar.disable_file_buttons()
            self.statusbar.set_status(f"🗑️ Deleted entries")
    
    def show_statistics(self):
        """Show statistics dialog"""
        def on_clear_cache():
            self.translator.clear_cache()
            self.statusbar.set_status("🗑️ Cache cleared")
        
        StatisticsDialog(self.root, self.entries, self.translator, on_clear_cache)
    
    def show_export_dialog(self):
        """Show export dialog"""
        def on_export(filename, compiled_mo):
            if compiled_mo:
                mo_file = filename.replace('.po', '.mo')
                self.statusbar.set_status(f"💾 Exported to {os.path.basename(filename)} and {os.path.basename(mo_file)}")
            else:
                self.statusbar.set_status(f"💾 Exported to {os.path.basename(filename)}")
            self.unsaved = False
        
        ExportDialog(self.root, self.entries, self.merger, on_export)
    
    def save_file(self):
        """Quick save file"""
        if not self.entries:
            return
        
        from datetime import datetime
        filename = filedialog.asksaveasfilename(
            defaultextension=".po",
            filetypes=[("PO Files", "*.po")],
            initialfile=f"fr_translated_{datetime.now().strftime('%Y%m%d')}.po"
        )
        
        if filename:
            self.merger.export_to_file(filename)
            self.unsaved = False
            self.statusbar.set_status(f"💾 Saved to {os.path.basename(filename)}")
            messagebox.showinfo("Success", f"File saved successfully!\n\n{filename}")
    
    def refresh(self):
        """Refresh view"""
        self.populate()
        self.statusbar.set_status("🔄 View refreshed")
    
    def run(self):
        """Run application"""
        self.root.mainloop()

    def on_language_changed(self, *_args):
        """Handle language configuration changes from the sidebar"""
        if self._updating_language_controls:
            return
        self._manual_language_override = True
        self.apply_language_settings()

    def apply_language_settings(self, show_status=True):
        """Synchronize sidebar language settings with the translator"""
        settings = self.sidebar.get_language_settings()
        changed = self.translator.configure_languages(
            source=settings['source'],
            target=settings['target'],
            auto_detect=settings['auto_detect']
        )

        if changed:
            self.invalidate_language_analysis()

        if changed and show_status and not self.translating:
            source = settings['source'].upper()
            target = settings['target'].upper()
            detect = "on" if settings['auto_detect'] else "off"
            self.statusbar.set_status(f"🌐 Language settings updated: {source} → {target} (auto-detect {detect})")

    def auto_configure_languages(self):
        """Auto-detect entry language and adjust translator defaults"""
        changed = False
        samples = [entry.msgid for entry in self.entries if entry.msgid]
        if not samples:
            return changed

        language_votes = Counter()
        for text in samples[:50]:
            detected = detect_language(text)
            if detected in self.translator.LANGUAGES:
                language_votes[detected] += 1

        if not language_votes:
            return changed

        dominant_lang, count = language_votes.most_common(1)[0]
        if dominant_lang != self.translator.target_lang:
            return changed

        current_source = self.translator.source_lang
        if dominant_lang == current_source:
            fallback_targets = [code for code in self.translator.LANGUAGES if code not in {dominant_lang}]
            new_target = fallback_targets[0] if fallback_targets else current_source
        else:
            new_target = current_source

        new_source = dominant_lang

        if new_source == new_target:
            return changed

        self.logger.info(
            "Auto-configuring languages based on imported entries: %s → %s (detected %s entries)",
            new_source,
            new_target,
            count,
        )

        code_to_name = {code: data["name"] for code, data in self.translator.LANGUAGES.items()}

        self._updating_language_controls = True
        try:
            if new_source in code_to_name:
                self.sidebar.source_lang_var.set(code_to_name[new_source])
            if new_target in code_to_name:
                self.sidebar.target_lang_var.set(code_to_name[new_target])
        finally:
            self._updating_language_controls = False

        self.apply_language_settings(show_status=False)
        changed = True
        source_label = code_to_name.get(new_source, new_source).upper()
        target_label = code_to_name.get(new_target, new_target).upper()
        self.statusbar.set_status(
            f"🤖 Auto-detected {source_label} entries. Translating into {target_label} by default.")
        return changed

    def update_entry_status_message(self):
        """Display contextual status message for the current table view"""
        if self.translating:
            return

        total_filtered = len(self.filtered_entries)
        total_entries = len(self.entries)
        filter_type = self.toolbar.get_filter_value()
        search_text = self.toolbar.get_search_text().strip()

        filter_labels = {
            'all': 'all entries',
            'translated': 'translated entries',
            'untranslated': 'pending entries'
        }

        if total_entries == 0:
            self.statusbar.set_status("Import .po files to begin translating.")
            return

        if total_filtered == 0:
            if search_text:
                self.statusbar.set_status(f"No entries match \"{search_text}\" with current filters.")
            elif filter_type != 'all':
                self.statusbar.set_status("No entries match the selected filter.")
            else:
                self.statusbar.set_status("No entries available.")
            return

        message = f"Showing {total_filtered} {filter_labels.get(filter_type, 'entries')}"
        if total_filtered != total_entries:
            message += f" (of {total_entries})"
        if search_text:
            message += f" matching \"{search_text}\""

        self.statusbar.set_status(message + ".")

    def confirm_discard_changes(self, action_description):
        """Prompt the user when unsaved changes would be lost"""
        if not self.unsaved:
            return True

        proceed = messagebox.askyesno(
            "Unsaved Changes",
            f"You have unsaved changes. Continue {action_description} without saving?"
        )

        if not proceed:
            self.statusbar.set_status("💾 Save your changes before continuing.")
        return proceed

    def on_close(self):
        """Handle window close event with unsaved change protection"""
        if not self.confirm_discard_changes("and exit"):
            return

        self.logger.info("Application closed")
        self.root.destroy()

