# PO Translator v1.0

Professional Odoo translation tool with AI-powered translations, caching, and advanced features.

## ✨ Features

### Core Features
- 🎨 **Modern Dark UI** - Clean, professional 2025 design
- 🤖 **AI Translation** - Gemini-powered with Odoo-specific terminology
- 💾 **Smart Caching** - Avoid duplicate API calls, save costs
- 📊 **Batch Operations** - Translate multiple files at once
- ✏️ **Inline Editing** - Quick edit any translation
- 🔍 **Advanced Search** - Filter by status, module, or text
- 📈 **Statistics** - Track translation progress and API usage

### Advanced Features
- ↶↷ **Undo/Redo** - Revert changes easily (Ctrl+Z/Ctrl+Y)
- ☑️ **Batch Selection** - Select and translate specific entries
- 🎯 **Module Tracking** - Know which Odoo module each entry belongs to
- ✅ **Validation** - Automatic variable preservation check
- 🔄 **Retry Logic** - Automatic retry on API failures
- 📤 **Export Options** - Choose what to export, compile .mo files
- ⌨️ **Keyboard Shortcuts** - Work faster with shortcuts
- 🧩 **Modular Architecture** - Clean, maintainable codebase

## 🚀 Quick Start

```bash
./run.sh
```

That's it! The script handles everything automatically.

## 📋 Requirements

- **Python 3.11+** (system Python)
- **Internet connection**
- **Gemini API key** (free at https://makersuite.google.com/app/apikey)

## 🎯 Usage

### 1. Get API Key (FREE)
1. Visit https://makersuite.google.com/app/apikey
2. Create a free API key
3. Paste it in the app and click "Save API Key"

### 2. Import Files
- Click "📁 Import Files" or press `Ctrl+O`
- Select one or more `.po` files
- Files are automatically merged and deduplicated

### 3. Translate
**Option A: Translate All**
- Click "🌐 Translate All"
- Translates all untranslated entries

**Option B: Translate Selected**
- Select specific entries with checkboxes
- Click "✓ Translate Selected"
- Only selected entries are translated

### 4. Review & Edit
- Click any entry to edit
- Changes are tracked for undo/redo
- Use search to find specific translations

### 5. Export
- Click "📤 Export"
- Choose export options:
  - Include translated/untranslated
  - Compile .mo file
- Save your file

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Import files |
| `Ctrl+S` | Save file |
| `Ctrl+E` | Export with options |
| `Ctrl+F` | Focus search |
| `Ctrl+A` | Select all |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `F5` | Refresh view |
| `Esc` | Clear search |
| `Delete` | Delete selected |

## 📊 Statistics

View detailed statistics:
- Translation progress
- API usage and cache efficiency
- Cache hit rate
- Error tracking

Click "📊 Statistics" to view full report.

## 🏗️ Project Structure (Modular Architecture)

```
translator_odoo/
├── app.py                      # Entry point
├── run.sh                      # Launcher script
├── requirements.txt            # Dependencies
├── src/
│   └── po_translator/
│       ├── core/               # Business logic
│       │   ├── merger.py       # PO file merging
│       │   ├── cleaner.py      # Entry deduplication
│       │   └── indexer.py      # Module tracking
│       ├── utils/              # Utilities
│       │   ├── logger.py       # Logging system
│       │   ├── language.py     # Language detection
│       │   └── file_utils.py   # File operations
│       ├── translator.py       # AI translator with caching
│       ├── gui/                # GUI Package (Modular)
│       │   ├── app.py          # Main application
│       │   ├── components/     # UI Components
│       │   │   ├── sidebar.py  # Left sidebar
│       │   │   ├── toolbar.py  # Top toolbar
│       │   │   ├── table.py    # Translation table
│       │   │   └── statusbar.py # Bottom status bar
│       │   ├── dialogs/        # Dialog Windows
│       │   │   ├── edit_dialog.py       # Edit entry
│       │   │   ├── export_dialog.py     # Export options
│       │   │   └── statistics_dialog.py # Statistics
│       │   └── widgets/        # Custom Widgets
│       │       └── undo_manager.py # Undo/redo logic
│       └── gui.py              # Backward compatibility
└── .config                     # API key (auto-created)
```

### Why Modular?

✅ **Maintainability** - Each component has a single responsibility  
✅ **Scalability** - Easy to add new features  
✅ **Testability** - Components can be tested independently  
✅ **Team Collaboration** - Multiple developers can work on different components  
✅ **Code Reusability** - Components can be reused in other projects  

## 🎨 Features Showcase

### Smart Caching
- Translations are cached locally
- Avoid duplicate API calls
- Save API quota and time
- ~70-90% cache hit rate on repeated translations

### Validation
- Automatic variable preservation
- Format string validation
- Prevents broken translations
- Retry on validation failure

### Batch Operations
- Select multiple entries
- Translate only what you need
- Delete unwanted entries
- Export filtered results

### Undo/Redo
- Track all changes
- Revert mistakes instantly
- Up to 50 actions history
- Works across all operations

## 🔧 Configuration

### API Key
Stored in `.config` file (auto-created when you save the key in the app).

### Cache
Translation cache is stored in `~/.po_translator/translation_cache.json`

To clear cache:
1. Click "📊 Statistics"
2. Click "Clear Cache"

Or manually delete: `~/.po_translator/translation_cache.json`

## 🐛 Troubleshooting

### "Can't find init.tcl"
The app uses system Python for WSL compatibility. Run:
```bash
sudo apt install python3-tk
```

### "Module not found"
Install dependencies:
```bash
pip install --break-system-packages polib langdetect customtkinter google-generativeai
```

### Translation not working
1. Check API key is saved
2. Check internet connection
3. View Statistics for error details
4. Check Gemini API quota

### Slow performance
- Limit visible entries (use filters)
- Clear translation cache
- Check API rate limits

## 📝 Translation Quality

The translator uses Odoo-specific terminology:
- "Bon de commande" → "Purchase Order"
- "Facture" → "Invoice"
- "Livraison" → "Delivery Order"
- "Devis" → "Quotation"
- And many more...

Variables and formatting are automatically preserved:
- `%(name)s`, `%s`, `{field}`, `${var}`
- HTML tags: `<b>`, `<i>`, `<span>`
- Line breaks: `\n`

## 👨‍💻 For Developers

### Adding New Components

1. **Create component file** in appropriate directory:
   - `src/po_translator/gui/components/` for UI components
   - `src/po_translator/gui/dialogs/` for dialog windows
   - `src/po_translator/gui/widgets/` for custom widgets

2. **Import in `__init__.py`**:
```python
from .my_component import MyComponent
__all__ = ['MyComponent', ...]
```

3. **Use in app.py**:
```python
from .components import MyComponent
self.my_component = MyComponent(parent, callbacks)
```

### Component Structure

Each component should:
- Accept `parent` and `callbacks` in `__init__`
- Have a `setup_ui()` method
- Expose public methods for external control
- Handle its own state internally

### Example Component

```python
class MyComponent:
    def __init__(self, parent, callbacks):
        self.parent = parent
        self.callbacks = callbacks
        self.frame = ctk.CTkFrame(parent)
        self.setup_ui()
    
    def setup_ui(self):
        # Create UI elements
        pass
    
    def update_data(self, data):
        # Public method to update component
        pass
```

## 🤝 Contributing

Contributions welcome! The modular architecture makes it easy to add features:

1. Fork the repository
2. Create a feature branch
3. Add your component/feature
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - Free to use and modify

## 👤 Author

**BOUBOU**

Made with ❤️ for the Odoo community

---

## 🎯 Pro Tips

1. **Use filters** - Work on untranslated entries first
2. **Select specific entries** - Don't translate everything at once
3. **Check statistics** - Monitor your API usage
4. **Use keyboard shortcuts** - Work faster
5. **Review before exporting** - Use inline editing to fix issues
6. **Cache is your friend** - Re-importing files reuses cached translations
7. **Modular code** - Easy to extend and customize

## 🔮 Future Ideas

- [ ] Translation memory across projects
- [ ] Glossary management
- [ ] Multiple AI providers (OpenAI, Claude)
- [ ] Collaborative translation
- [ ] Version control integration
- [ ] Custom terminology database
- [ ] Batch file processing
- [ ] Translation quality scoring
- [ ] Plugin system for custom components
- [ ] REST API for automation

---

**Need help?** Check the logs in `app.log` for detailed debugging information.

**Enjoy translating!** 🚀
