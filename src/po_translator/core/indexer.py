"""Module indexer for linking PO entries to their source modules"""
from po_translator.utils.file_utils import extract_module_name


class ModuleIndexer:
    """Index and track which module each PO entry belongs to"""
    
    def __init__(self):
        self.entry_to_module = {}
        self.module_to_entries = {}
    
    def index_entry(self, entry_id, filepath):
        """
        Index an entry with its source module
        
        Args:
            entry_id: Unique identifier for entry (msgid)
            filepath: Path to source .po file
        """
        module_name = extract_module_name(filepath)
        
        self.entry_to_module[entry_id] = module_name
        
        if module_name not in self.module_to_entries:
            self.module_to_entries[module_name] = []
        
        if entry_id not in self.module_to_entries[module_name]:
            self.module_to_entries[module_name].append(entry_id)
    
    def get_module(self, entry_id):
        """
        Get module name for an entry
        
        Args:
            entry_id: Entry identifier
            
        Returns:
            str: Module name or 'unknown'
        """
        return self.entry_to_module.get(entry_id, 'unknown')
    
    def get_entries_by_module(self, module_name):
        """
        Get all entries for a module
        
        Args:
            module_name: Name of module
            
        Returns:
            list: List of entry IDs
        """
        return self.module_to_entries.get(module_name, [])
    
    def get_all_modules(self):
        """
        Get list of all indexed modules
        
        Returns:
            list: Sorted list of module names
        """
        return sorted(self.module_to_entries.keys())
    
    def clear(self):
        """Clear all indexed data"""
        self.entry_to_module.clear()
        self.module_to_entries.clear()

