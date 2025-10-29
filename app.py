#!/usr/bin/env python3
"""
PO Translator - Odoo Translation Tool
Author: BOUBOU
License: MIT
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from po_translator.utils.logger import setup_logger, get_logger

# Setup logging
log_file = os.path.join(os.path.dirname(__file__), 'app.log')
setup_logger('po_translator', log_file=log_file)
logger = get_logger('po_translator')

logger.info("Starting PO Translator")

try:
    from po_translator.gui import POTranslatorApp
    
    app = POTranslatorApp()
    app.run()
    
    logger.info("Application closed")
except KeyboardInterrupt:
    logger.info("Interrupted by user")
    sys.exit(0)
except Exception as e:
    logger.exception(f"Error: {e}")
    print(f"Error: {e}")
    print(f"See log: {log_file}")
    sys.exit(1)
