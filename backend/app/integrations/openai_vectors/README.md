# OpenAI Vector Stores Integration

Módulo para gestionar archivos y vector stores en OpenAI para búsqueda semántica con agentes de IA.

## 📋 Descripción

Este módulo proporciona una interfaz simple para:
- Subir archivos a OpenAI
- Crear vector stores para file search
- Gestionar batches de archivos con metadata
- Integración con extracción de FAQs del SII

## 🚀 Uso Rápido

### Crear Vector Store desde Archivos

```python
from app.integrations.openai_vectors import OpenAIVectorClient

client = OpenAIVectorClient()

# Subir archivos desde un directorio
uploaded_files = client.upload_files_from_directory(
    directory="app/integrations/sii_faq/output/20251110_115900",
    pattern="*.md",
    exclude_index=True,
    expires_after_days=365
)

# Crear vector store
vector_store = client.create_vector_store(
    name="SII FAQs - 2025-11-10",
    files=uploaded_files,
    metadata={"source": "sii_faqs", "extraction_date": "2025-11-10"}
)

print(f"Vector Store ID: {vector_store.vector_store_id}")
```

### Crear Vector Store con Batches por Tema

```python
# Crear vector store vacío
vector_store = client.create_vector_store(
    name="SII FAQs - By Topic",
    metadata={"organized_by_topic": True}
)

# Subir archivos de un tema específico
files_topic_1 = client.upload_files_from_directory(
    directory="faqs/impuestos",
    pattern="*.md"
)

# Crear batch con metadata de tema
batch = client.create_vector_store_batch(
    vector_store_id=vector_store.vector_store_id,
    files=files_topic_1,
    topic_name="Impuestos",
    subtopic_name="IVA",
    chunking_strategy={
        "type": "static",
        "max_chunk_size_tokens": 1200,
        "chunk_overlap_tokens": 200
    }
)
```

## 📚 API Reference

### `OpenAIVectorClient`

#### Métodos de Archivos

**`upload_file(file_path, purpose="assistants", expires_after_days=30)`**

Sube un archivo individual a OpenAI.

**`upload_files_from_directory(directory, pattern="*.md", exclude_index=True, purpose="assistants", expires_after_days=30)`**

Sube todos los archivos que coincidan con el patrón desde un directorio.

**`list_files(purpose=None)`**

Lista todos los archivos subidos, opcionalmente filtrados por propósito.

**`delete_file(file_id)`**

Elimina un archivo de OpenAI.

#### Métodos de Vector Stores

**`create_vector_store(name, files=None, file_ids=None, metadata=None)`**

Crea un nuevo vector store.

**`create_vector_store_batch(vector_store_id, files, topic_name=None, subtopic_name=None, chunking_strategy=None)`**

Agrega un batch de archivos a un vector store con metadata.

**`get_vector_store_batch(vector_store_id, batch_id)`**

Recupera información sobre un batch.

**`list_vector_stores()`**

Lista todos los vector stores.

**`delete_vector_store(vector_store_id)`**

Elimina un vector store.

## 🧪 Testing

```bash
# Ver documentación de testing de FAQs
python -m app.integrations.sii_faq.test_vectorizer --help
```

## 🔗 Integración con Agentes

Una vez creado el vector store, usa el ID en la configuración de tu agente:

```python
from chatkit import Agent

agent = Agent(
    name="SII FAQ Agent",
    model="gpt-4o",
    instructions="Eres un experto en tributación chilena...",
    tools=[...],
    tool_resources={
        "file_search": {
            "vector_store_ids": ["vs_abc123xyz"]
        }
    }
)
```

## 📝 Notas

- Los archivos expiran automáticamente según `expires_after_days`
- La metadata de batches permite filtrar búsquedas por tema/subtema
- El chunking strategy es opcional pero recomendado para mejorar búsqueda
- Tamaño máximo de chunk recomendado: 1200 tokens
- Overlap recomendado: 200 tokens

## 🔧 Configuración

Requiere variable de entorno:
```bash
OPENAI_API_KEY=sk-...
```

## 🔗 Enlaces

- [OpenAI Vector Stores API](https://platform.openai.com/docs/assistants/tools/file-search)
- [OpenAI Files API](https://platform.openai.com/docs/api-reference/files)
