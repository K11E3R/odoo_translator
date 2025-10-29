"""PO file cleaner for deduplication and validation"""
import polib
from po_translator.utils.file_utils import validate_po_entry, sanitize_text


class POCleaner:
    """Clean and deduplicate PO entries"""
    
    def __init__(self):
        self.seen_msgids = set()
    
    def clean_entries(self, entries):
        """
        Clean and deduplicate list of PO entries
        
        Args:
            entries: List of polib.POEntry objects
            
        Returns:
            list: Cleaned and deduplicated entries
        """
        cleaned = []
        self.seen_msgids.clear()
        
        for entry in entries:
            if not validate_po_entry(entry):
                continue
            
            msgid = sanitize_text(entry.msgid)
            
            if not msgid:
                continue
            
            if msgid in self.seen_msgids:
                continue
            
            self.seen_msgids.add(msgid)
            
            entry.msgid = msgid
            entry.msgstr = sanitize_text(entry.msgstr)
            
            cleaned.append(entry)
        
        return cleaned
    
    def merge_entries(self, entry1, entry2):
        """
        Merge two entries with same msgid
        
        Args:
            entry1: First POEntry
            entry2: Second POEntry
            
        Returns:
            POEntry: Merged entry (prefers non-empty msgstr)
        """
        if entry2.msgstr and not entry1.msgstr:
            entry1.msgstr = entry2.msgstr
        
        if entry2.comment and not entry1.comment:
            entry1.comment = entry2.comment
        
        if hasattr(entry2, 'occurrences') and entry2.occurrences:
            if not hasattr(entry1, 'occurrences'):
                entry1.occurrences = []
            entry1.occurrences.extend(entry2.occurrences)
        
        return entry1
    
    def remove_obsolete(self, entries):
        """
        Remove obsolete entries
        
        Args:
            entries: List of POEntry objects
            
        Returns:
            list: Entries without obsolete ones
        """
        return [e for e in entries if not e.obsolete]
    
    def sort_entries(self, entries):
        """
        Sort entries alphabetically by msgid
        
        Args:
            entries: List of POEntry objects
            
        Returns:
            list: Sorted entries
        """
        return sorted(entries, key=lambda e: e.msgid.lower())
