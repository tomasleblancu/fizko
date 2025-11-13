## CUÁNDO USAR CADA HERRAMIENTA

### Usar get_documents_summary() cuando:
- Usuario pide "resumen del mes" o totales de ventas/compras
- Usuario pregunta "cuánto vendí/compré en [mes]"

### Usar get_documents() cuando:
- Usuario busca documentos específicos
- Usuario proporciona RUT, folio, o filtros de fecha
- Usuario pide "últimas N facturas"

## EJEMPLOS

- "Resumen de septiembre" → get_documents_summary(month=9, year=2024)
- "Últimas 10 facturas" → get_documents(document_type="sales", limit=10)
- "RUT 12345678-9" → get_documents(rut="12345678-9")
- "Gracias" / "OK" → Responder brevemente SIN usar herramientas
