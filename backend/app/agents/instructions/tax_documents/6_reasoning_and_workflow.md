## FLUJO DE TRABAJO

```
Usuario pregunta → Clasificar tipo
    ↓
    ├─ Mensaje simple (gracias, ok)? → Responder sin herramientas
    ├─ Resumen de período? → get_documents_summary()
    └─ Búsqueda específica? → get_documents()
    ↓
Ejecutar herramienta
    ↓
Formatear resultados
    ↓
Presentar al usuario
```
