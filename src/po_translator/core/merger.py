"""PO file merger for combining multiple .po files"""
import polib
from po_translator.core.cleaner import POCleaner
from po_translator.core.indexer import ModuleIndexer
from po_translator.utils.logger import get_logger


class POMerger:
    """Merge multiple PO files into one"""
    
    def __init__(self):
        self.cleaner = POCleaner()
        self.indexer = ModuleIndexer()
        self.merged_entries = {}
        self.logger = get_logger('po_translator.merger')
    
    def load_po_file(self, filepath):
        """
        Load a single PO file
        
        Args:
            filepath: Path to .po file
            
        Returns:
            polib.POFile: Loaded PO file or None if error
        """
        self.logger.info(f"Loading PO file: {filepath}")
        try:
            po_file = polib.pofile(filepath)
            self.logger.debug(f"  Loaded {len(po_file)} entries from {filepath}")
            return po_file
        except Exception as e:
            self.logger.error(f"Error loading {filepath}: {e}")
            print(f"Error loading {filepath}: {e}")
            return None
    
    def merge_files(self, filepaths):
        """
        Merge multiple PO files
        
        Args:
            filepaths: List of paths to .po files
            
        Returns:
            dict: Dictionary of merged entries {msgid: POEntry}
        """
        self.logger.info(f"Starting merge of {len(filepaths)} files")
        self.merged_entries.clear()
        self.indexer.clear()
        
        all_entries = []
        
        for filepath in filepaths:
            po_file = self.load_po_file(filepath)
            if not po_file:
                continue
            
            entry_count = 0
            for entry in po_file:
                if entry.obsolete:
                    continue
                
                self.indexer.index_entry(entry.msgid, filepath)
                all_entries.append(entry)
                entry_count += 1
            
            self.logger.debug(f"  Added {entry_count} entries from {filepath}")
        
        self.logger.info(f"Total entries before cleaning: {len(all_entries)}")
        cleaned_entries = self.cleaner.clean_entries(all_entries)
        self.logger.info(f"Total entries after cleaning: {len(cleaned_entries)}")
        
        duplicates = 0
        for entry in cleaned_entries:
            msgid = entry.msgid
            
            if msgid in self.merged_entries:
                self.merged_entries[msgid] = self.cleaner.merge_entries(
                    self.merged_entries[msgid], 
                    entry
                )
                duplicates += 1
            else:
                self.merged_entries[msgid] = entry
        
        self.logger.info(f"Merged entries: {len(self.merged_entries)} unique (removed {duplicates} duplicates)")
        return self.merged_entries
    
    def get_entries_list(self):
        """
        Get list of merged entries
        
        Returns:
            list: List of POEntry objects
        """
        return list(self.merged_entries.values())
    
    def get_entry(self, msgid):
        """
        Get specific entry by msgid
        
        Args:
            msgid: Message ID
            
        Returns:
            POEntry: Entry or None
        """
        return self.merged_entries.get(msgid)
    
    def update_entry(self, msgid, new_msgid=None, new_msgstr=None):
        """
        Update an entry
        
        Args:
            msgid: Current message ID
            new_msgid: New message ID (optional)
            new_msgstr: New translation (optional)
            
        Returns:
            bool: True if updated successfully
        """
        if msgid not in self.merged_entries:
            return False
        
        entry = self.merged_entries[msgid]
        
        if new_msgstr is not None:
            entry.msgstr = new_msgstr
        
        if new_msgid is not None and new_msgid != msgid:
            self.merged_entries[new_msgid] = entry
            entry.msgid = new_msgid
            del self.merged_entries[msgid]
            
            old_module = self.indexer.get_module(msgid)
            self.indexer.index_entry(new_msgid, f"addons/{old_module}/i18n/fr.po")
        
        return True
    
    def export_to_file(self, filepath, metadata=None):
        """
        Export merged entries to .po file
        
        Args:
            filepath: Output path
            metadata: Optional metadata dict
            
        Returns:
            bool: True if successful
        """
        self.logger.info(f"Exporting to {filepath}")
        try:
            po_file = polib.POFile()
            
            if metadata:
                po_file.metadata = metadata
            else:
                po_file.metadata = {
                    'Content-Type': 'text/plain; charset=UTF-8',
                    'Language': 'fr',
                }
            
            entries = self.cleaner.sort_entries(self.get_entries_list())
            self.logger.debug(f"  Exporting {len(entries)} entries")
            
            for entry in entries:
                po_file.append(entry)
            
            po_file.save(filepath)
            self.logger.info(f"Successfully exported to {filepath}")
            
            return True
        except Exception as e:
            self.logger.error(f"Error exporting to {filepath}: {e}")
            print(f"Error exporting to {filepath}: {e}")
            return False
    
    def compile_mo(self, po_filepath, mo_filepath=None):
        """
        Compile .po to .mo file
        
        Args:
            po_filepath: Path to .po file
            mo_filepath: Output path for .mo (optional, defaults to same name)
            
        Returns:
            bool: True if successful
        """
        try:
            po_file = polib.pofile(po_filepath)
            
            if mo_filepath is None:
                mo_filepath = po_filepath.replace('.po', '.mo')
            
            po_file.save_as_mofile(mo_filepath)
            
            return True
        except Exception as e:
            print(f"Error compiling to {mo_filepath}: {e}")
            return False

