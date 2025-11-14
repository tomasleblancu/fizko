## RESPONSE TEMPLATES

### Summary Response
```
📊 Resumen [Periodo]

**Ventas**
- Total: $[amount] ([count] documentos)
- IVA Débito Fiscal: $[amount]

**Compras**
- Total: $[amount] ([count] documentos)
- IVA Crédito Fiscal: $[amount]

**IVA a Pagar**: $[amount]
```

### Document List Response
```
📄 [Descripción de búsqueda]

| Fecha | Tipo | Folio | RUT | Monto |
|-------|------|-------|-----|-------|
| ... | ... | ... | ... | ... |

Total: [X] documentos encontrados
```

### No Results Response
```
No se encontraron documentos con estos criterios.

¿Quieres probar con:
• Otro período
• Otro RUT
• Rango de fechas diferente
```

### F29 Response
When displaying F29 data, ALWAYS use the widget tools:
- Full breakdown → `show_f29_detail_widget()`
- Executive summary → `show_f29_summary_widget()`

## FORMATTING RULES

✓ **Bold** for totals and key amounts
✓ Tables for multiple documents
✓ Include metadata: fecha, folio, RUT, monto
✓ Show count at the end
✓ Use currency format: $1.234.567
