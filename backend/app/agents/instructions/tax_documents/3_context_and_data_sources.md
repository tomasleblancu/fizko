## HERRAMIENTAS DISPONIBLES

### get_documents_summary(month, year)
Obtiene resúmenes y totales para un período.
- Retorna: ventas totales, compras totales, cálculos de IVA
- Si no se especifica mes/año, usa el mes actual

### get_documents(document_type, rut, folio, start_date, end_date, limit)
Busca documentos específicos.
- Todos los parámetros son opcionales
- `document_type`: "sales", "purchases", o "both"
- `limit`: Máximo de documentos (default 20)

### Memoria de Usuario (solo lectura)
Patrones de búsqueda de documentos del usuario.

### Memoria de Empresa (solo lectura)
Proveedores y clientes comunes, patrones de facturación.
