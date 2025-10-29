# Test PO Files

This directory contains test PO files for the translator.

## Files

### 1. `test_fr_en.po`
- **Purpose**: Test basic French to English translation
- **Contains**: Common Odoo terms (Facture, Bon de commande, etc.)
- **Expected**: Should translate to proper Odoo English terms

### 2. `test_mixed.po`
- **Purpose**: Test auto-detection and correction
- **Contains**: French msgid with English msgstr (reversed)
- **Expected**: Should detect and auto-correct the language mismatch

### 3. `test_with_variables.po`
- **Purpose**: Test variable preservation
- **Contains**: Strings with %(name)s, %s, {field}, ${var}, HTML tags, \n
- **Expected**: Should preserve all variables and formatting

## How to Test

1. **Import test files** in the application
2. **Select languages**:
   - Source: English
   - Target: French
   - Auto-detect: ON
3. **Click "Translate All"**
4. **Check results**:
   - Variables preserved
   - Odoo terms correctly translated
   - Mixed languages auto-corrected

## Expected Results

### test_fr_en.po
```
"Bon de commande" → "Purchase Order"
"Facture" → "Invoice"
"Livraison" → "Delivery Order"
"Client" → "Customer"
```

### test_mixed.po
- Should detect French in msgid
- Should auto-correct to English msgid
- Should swap msgid/msgstr

### test_with_variables.po
- All variables preserved: %(name)s, %s, {amount}, ${order_ref}
- HTML tags preserved: <b>, <i>
- Line breaks preserved: \n
- All formatting intact

## Testing Checklist

- [ ] Import all 3 files
- [ ] Check statistics (total entries)
- [ ] Test "Translate All"
- [ ] Verify variable preservation
- [ ] Check Odoo terminology
- [ ] Test auto-detection
- [ ] Export and verify .po format
- [ ] Check cache hit rate
- [ ] Review translation quality

## Notes

- These files are designed to test edge cases
- Use with Gemini API or free translator
- Check logs for auto-correction messages
- Verify no validation errors

