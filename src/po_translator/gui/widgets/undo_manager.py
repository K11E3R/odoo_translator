"""
Undo/Redo Manager
Manages action history for undo/redo functionality
"""
from collections import deque


class UndoManager:
    """Manage undo/redo operations"""
    
    def __init__(self, max_history=50):
        """
        Initialize undo manager
        
        Args:
            max_history: Maximum number of actions to keep in history
        """
        self.undo_stack = deque(maxlen=max_history)
        self.redo_stack = deque(maxlen=max_history)
    
    def record(self, action, data):
        """
        Record an action
        
        Args:
            action: Action type (e.g., 'edit', 'delete')
            data: Action data for reverting
        """
        self.undo_stack.append({'action': action, 'data': data})
        self.redo_stack.clear()
    
    def can_undo(self):
        """Check if undo is available"""
        return len(self.undo_stack) > 0
    
    def can_redo(self):
        """Check if redo is available"""
        return len(self.redo_stack) > 0
    
    def undo(self):
        """
        Undo last action
        
        Returns:
            Action dict or None if no actions to undo
        """
        if self.can_undo():
            action = self.undo_stack.pop()
            self.redo_stack.append(action)
            return action
        return None
    
    def redo(self):
        """
        Redo last undone action
        
        Returns:
            Action dict or None if no actions to redo
        """
        if self.can_redo():
            action = self.redo_stack.pop()
            self.undo_stack.append(action)
            return action
        return None
    
    def clear(self):
        """Clear all history"""
        self.undo_stack.clear()
        self.redo_stack.clear()
    
    def get_stats(self):
        """Get undo/redo statistics"""
        return {
            'undo_available': len(self.undo_stack),
            'redo_available': len(self.redo_stack)
        }

