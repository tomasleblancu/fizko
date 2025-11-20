# Sistema de Caché de Archivos Subidos

## Descripción

Para evitar subir archivos duplicados a OpenAI, el sistema mantiene un caché de archivos ya subidos en cada directorio de output.

## Funcionamiento

### Archivo de Caché

Cada directorio de output (e.g., `output/20251110_121904/`) contiene un archivo `uploaded_files.json` con la siguiente estructura:

```json
{
  "archivo1.md": "file-abc123xyz",
  "archivo2.md": "file-def456uvw",
  ...
}
```

Mapea `nombre_archivo` → `file_id` de OpenAI.

### Flujo de Vectorización

1. **Cargar caché**: Lee `uploaded_files.json` del directorio
2. **Identificar archivos**: Lista todos los archivos `.md` (excepto `INDEX.md`)
3. **Reusar file_ids**: Para archivos en caché, reutiliza el `file_id` existente
4. **Subir nuevos**: Solo sube archivos que NO están en caché
5. **Actualizar caché**: Guarda los nuevos `file_id` en el JSON

### Beneficios

- **Ahorro de costos**: No sube el mismo archivo múltiples veces
- **Velocidad**: Vectorizaciones subsiguientes son mucho más rápidas
- **Consistencia**: Mismo `file_id` para mismo archivo garantiza consistencia

## Ejemplo de Uso

```bash
# Primera vectorización - sube todos los archivos
python -m app.integrations.sii_faq.vectorize_faqs --version 20251110_121904

# Output:
# Found 0 files in cache
# Found 149 markdown files in directory
# Uploading 149 new files...
# Updated cache with 149 new files

# Segunda vectorización - reutiliza file_ids
python -m app.integrations.sii_faq.vectorize_faqs --version 20251110_121904

# Output:
# Found 149 files in cache
# Found 149 markdown files in directory
# All files already uploaded, using cached file_ids
```

## Invalidación del Caché

Si necesitas forzar la re-subida de archivos:

1. **Manual**: Elimina `uploaded_files.json` del directorio
2. **Selectivo**: Elimina entradas específicas del JSON
3. **Completo**: Elimina el directorio completo y re-extrae

## Notas Técnicas

- Los archivos en OpenAI expiran después de 30 días (límite de OpenAI)
- Si un `file_id` en caché ya expiró, la creación del vector store fallará
- En ese caso, elimina el caché y vuelve a vectorizar
- El caché es por directorio de extracción (version-specific)
