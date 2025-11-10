# SII FAQ Scraper

Scraper para extraer las preguntas frecuentes (FAQs) del sitio web del SII (Servicio de Impuestos Internos de Chile).

## 🎯 Características

- ✅ **Extracción completa** de todos los temas, subtemas y preguntas
- ✅ **Búsqueda de preguntas** por texto
- ✅ **Sin autenticación** - usa requests + BeautifulSoup
- ✅ **Reintentos automáticos** para requests fallidos
- ✅ **Datos estructurados** con modelos de datos claros
- ✅ **Context manager** para limpieza automática de recursos

## 📦 Estructura

```
sii_faq/
├── __init__.py          # Exports públicos
├── client.py            # Cliente principal SIIFAQClient
├── config.py            # Configuración (URLs, timeouts, etc.)
├── models.py            # Modelos de datos (FAQTopic, FAQSubtopic, FAQQuestion)
├── scrapers.py          # Scrapers con BeautifulSoup
├── extract_faqs.py      # Script de extracción
├── vectorizer.py        # Vectorización para OpenAI
├── vectorize_faqs.py    # Script de vectorización interactivo
└── README.md           # Esta documentación
```

## 🚀 Uso Rápido

### Extraer todos los FAQs y exportar a Markdown

```python
from app.integrations.sii_faq import SIIFAQClient

# Context manager con directorio de salida personalizado
with SIIFAQClient(output_dir="mis_faqs") as client:
    # Extraer FAQs
    topics = client.extract_all_faqs()

    # Exportar a archivos Markdown versionados
    version_dir = client.export_to_markdown(topics)
    print(f"Archivos guardados en: {version_dir}")
```

**Estructura de salida:**
```
sii_faqs/
└── 20251110_143025/           # Timestamp de extracción
    ├── INDEX.md               # Índice con enlaces a todos los archivos
    ├── clave_tributaria_certificado_digital.md
    ├── clave_tributaria_codigo_provisorio.md
    ├── factura_electronica_emision.md
    └── ...                    # Un archivo .md por subtema
```

### Extraer y procesar en memoria

```python
from app.integrations.sii_faq import SIIFAQClient

# Context manager (recomendado)
with SIIFAQClient() as client:
    topics = client.extract_all_faqs()

    # Iterar por los resultados
    for topic in topics:
        print(f"Topic: {topic.name}")
        for subtopic in topic.subtopics:
            print(f"  Subtopic: {subtopic.name}")
            for question in subtopic.questions:
                print(f"    Q: {question.question[:50]}...")
                print(f"    A: {question.answer[:100]}...")
```

### Extraer solo un tema específico

```python
with SIIFAQClient() as client:
    topic = client.extract_topic("Factura Electrónica")

    if topic:
        print(f"Found {len(topic.subtopics)} subtopics")
        questions = topic.get_all_questions()
        print(f"Total questions: {len(questions)}")
```

### Buscar preguntas

```python
with SIIFAQClient() as client:
    # Primero extraer todos los temas (esto toma tiempo)
    topics = client.extract_all_faqs()

    # Luego buscar
    results = client.search_questions("IVA", topics=topics)

    for question in results:
        print(f"Topic: {question.topic_name}")
        print(f"Subtopic: {question.subtopic_name}")
        print(f"Question: {question.question}")
        print(f"ID: {question.id}")
        print("---")
```

### Obtener resumen de temas (sin extraer todo)

```python
with SIIFAQClient() as client:
    topics_summary = client.get_topics_summary()

    for topic in topics_summary:
        print(f"{topic['name']}: {topic['url']}")
```

## 📖 API del Cliente

### `SIIFAQClient`

Cliente principal para interactuar con los FAQs del SII.

#### `extract_all_faqs(limit_topics: Optional[int] = None) -> List[FAQTopic]`

Extrae todos los FAQs del sitio del SII.

**Parámetros:**
- `limit_topics` (opcional): Limitar a N temas (útil para testing)

**Retorna:**
- Lista de objetos `FAQTopic` con toda la jerarquía

**Ejemplo:**
```python
topics = client.extract_all_faqs()  # Todos los temas
topics = client.extract_all_faqs(limit_topics=3)  # Solo 3 temas
```

---

#### `extract_topic(topic_name: str) -> Optional[FAQTopic]`

Extrae FAQs de un tema específico por nombre.

**Parámetros:**
- `topic_name`: Nombre del tema a extraer

**Retorna:**
- Objeto `FAQTopic` o `None` si no se encuentra

**Ejemplo:**
```python
topic = client.extract_topic("Boleta Electrónica de Ventas y Servicios")
```

---

#### `search_questions(query: str, topics: Optional[List[FAQTopic]] = None) -> List[FAQQuestion]`

Busca preguntas que coincidan con una consulta.

**Parámetros:**
- `query`: Texto a buscar (case-insensitive)
- `topics` (opcional): Lista de temas ya extraídos. Si es `None`, extrae todos primero.

**Retorna:**
- Lista de objetos `FAQQuestion` que coinciden

**Ejemplo:**
```python
# Buscar en temas ya extraídos
topics = client.extract_all_faqs()
results = client.search_questions("factura electrónica", topics=topics)

# O dejar que extraiga automáticamente
results = client.search_questions("IVA")
```

---

#### `get_topics_summary() -> List[dict]`

Obtiene un resumen de todos los temas disponibles sin extraer todo el contenido.

**Retorna:**
- Lista de diccionarios con `name` y `url`

**Ejemplo:**
```python
summary = client.get_topics_summary()
for item in summary:
    print(f"{item['name']}: {item['url']}")
```

---

#### `export_to_markdown(topics: List[FAQTopic], version_dir: Optional[Path] = None) -> Path`

Exporta todos los temas a archivos Markdown organizados por subtema.

**Parámetros:**
- `topics`: Lista de objetos `FAQTopic` a exportar
- `version_dir` (opcional): Directorio de versión. Si es `None`, crea uno nuevo con timestamp.

**Retorna:**
- `Path` al directorio de versión donde se exportaron los archivos

**Estructura de salida:**
- `INDEX.md`: Archivo índice con tabla de contenidos y enlaces a todos los archivos
- `{topic}_{subtopic}.md`: Un archivo por subtopic con todas sus preguntas

**Ejemplo:**
```python
topics = client.extract_all_faqs(limit_topics=2)
version_dir = client.export_to_markdown(topics)
print(f"Files saved to: {version_dir}")

# Custom output directory
client = SIIFAQClient(output_dir="mis_faqs")
topics = client.extract_all_faqs()
version_dir = client.export_to_markdown(topics)
```

**Formato de archivos Markdown:**
```markdown
# Tema Principal

## Subtema

**URL:** https://...
**Total de preguntas:** 5

---

### 1. ¿Primera pregunta?

**ID:** 001.100.7893.004
**Fecha de creación:** 12/04/2021
**Fecha de actualización:** 01/07/2025
**URL:** https://...

#### Respuesta

Texto de la respuesta...

---

### 2. ¿Segunda pregunta?
...
```

---

## 📊 Modelos de Datos

### `FAQQuestion`

Representa una pregunta individual con su respuesta.

**Atributos:**
- `id` (str): ID único del FAQ (ej: "001.100.7893.004")
- `question` (str): Texto de la pregunta
- `answer` (str): Texto de la respuesta
- `subtopic_id` (str): URL del subtema
- `subtopic_name` (str): Nombre del subtema
- `topic_name` (str): Nombre del tema principal
- `url` (str): URL de la pregunta
- `created_at` (datetime, opcional): Fecha de creación
- `updated_at` (datetime, opcional): Fecha de última actualización

---

### `FAQSubtopic`

Representa un subtema dentro de un tema.

**Atributos:**
- `name` (str): Nombre del subtema
- `url` (str): URL del subtema
- `topic_name` (str): Nombre del tema padre
- `questions` (List[FAQQuestion]): Lista de preguntas

---

### `FAQTopic`

Representa un tema principal.

**Atributos:**
- `name` (str): Nombre del tema
- `url` (str): URL del tema
- `subtopics` (List[FAQSubtopic]): Lista de subtemas

**Métodos:**
- `get_all_questions() -> List[FAQQuestion]`: Obtiene todas las preguntas de todos los subtemas

---

## 🧪 Testing

### Script de prueba rápido

```bash
cd backend

# Solo ver resumen de temas (rápido, sin extracción completa)
uv run python -m app.integrations.sii_faq.extract_faqs --summary-only

# Extraer 2 temas y exportar a Markdown
uv run python -m app.integrations.sii_faq.extract_faqs --limit 2 --export-md

# Extraer 2 temas con directorio personalizado
uv run python -m app.integrations.sii_faq.extract_faqs --limit 2 --export-md --output-dir mis_faqs

# Extraer TODO y exportar (toma 10-30 minutos)
uv run python -m app.integrations.sii_faq.extract_faqs --export-md

# Buscar preguntas sobre IVA en 2 temas
uv run python -m app.integrations.sii_faq.extract_faqs --limit 2 --search "IVA"
```

### Test programático

```python
from app.integrations.sii_faq import SIIFAQClient

# Test básico
with SIIFAQClient() as client:
    # 1. Test de resumen
    summary = client.get_topics_summary()
    assert len(summary) > 0
    print(f"✅ Found {len(summary)} topics")

    # 2. Test de extracción limitada
    topics = client.extract_all_faqs(limit_topics=2)
    assert len(topics) <= 2
    print(f"✅ Extracted {len(topics)} topics")

    # 3. Test de búsqueda
    results = client.search_questions("certificado digital", topics=topics)
    print(f"✅ Found {len(results)} matching questions")
```

---

## ⚙️ Configuración

Puedes modificar la configuración en [config.py](./config.py):

```python
# Timeouts
REQUEST_TIMEOUT = 30  # segundos

# User Agent
USER_AGENT = "Mozilla/5.0 ..."

# Reintentos
MAX_RETRIES = 3
RETRY_DELAY = 1  # segundos entre reintentos
```

---

## 🏗️ Arquitectura del Scraping

El scraping sigue esta jerarquía:

```
1. Página principal (otros.html)
   └─> Lista de temas principales

2. Página de tema (ej: faqs_factura_electronica.htm)
   └─> Lista de subtemas

3. Página de subtema (ej: arbol_faqs_factura_1870.htm)
   └─> Lista de preguntas

4. Página de pregunta (ej: 001_100_7893.htm)
   └─> Detalle completo (ID, pregunta, respuesta, fechas)
```

**Patrón de extracción:**

1. **Temas principales**: `<div class="caja-item" onclick="window.location='...'">`
2. **Subtemas**: `<div id="listado_subtemas"><ol><li><a>`
3. **Lista de preguntas**: `<div id="listado-preguntas-por-tema"><ul><li><a>`
4. **Detalle de pregunta**:
   - Pregunta: `<div id="div-pregunta"><h2>`
   - Respuesta: `<div id="div-respuesta">`
   - ID: `<div id="div-id">`
   - Fechas: `<div id="div-fec-creacion">` y `<div id="div-fec-actualizacion">`

---

## 📝 Notas Importantes

1. **Tiempo de ejecución**: Extraer TODOS los FAQs puede tomar 10-30 minutos dependiendo de la conexión.

2. **Rate limiting**: El scraper incluye reintentos automáticos, pero no hay delay intencional entre requests. Si experimentas problemas, considera agregar `time.sleep()` en el scraper.

3. **Encoding**: Las páginas usan UTF-8 para caracteres españoles (á, é, í, ó, ú, ñ, ¿, ¡).

4. **URLs relativas**: El scraper maneja correctamente URLs relativas usando `urljoin()`.

5. **Temas anidados**: Algunos temas tienen subtemas directamente en la página principal (ej: "Impuestos Mensuales", "Declaraciones Juradas", "Declaración de Renta"). Estos se extraen como temas independientes con formato "Tema Principal - Subtema".

---

## 🐛 Troubleshooting

### Error: "Failed to fetch..."

- Verificar conexión a internet
- El sitio del SII puede estar caído temporalmente
- Considerar aumentar `REQUEST_TIMEOUT` en [config.py](./config.py)

### Extracción muy lenta

- Usar `limit_topics` para testing: `client.extract_all_faqs(limit_topics=2)`
- El sitio del SII puede estar lento
- Considerar agregar caching de resultados

### Encoding issues (caracteres raros)

- El scraper usa `response.encoding = 'utf-8'`
- Si ves problemas, verifica la respuesta HTML raw

---

## 💡 Mejores Prácticas

### ✅ Usar Context Manager

```python
# ✅ Bueno - Cierre automático
with SIIFAQClient() as client:
    topics = client.extract_all_faqs()

# ❌ Malo - Requiere cierre manual
client = SIIFAQClient()
topics = client.extract_all_faqs()
client.close()  # Fácil olvidar
```

### ✅ Limitar para Testing

```python
# ✅ Bueno para testing
topics = client.extract_all_faqs(limit_topics=2)

# ⚠️ Cuidado - toma mucho tiempo
topics = client.extract_all_faqs()  # Todos los temas
```

### ✅ Cachear Resultados

```python
# ✅ Bueno - extraer una vez, buscar múltiples veces
topics = client.extract_all_faqs()
results1 = client.search_questions("IVA", topics=topics)
results2 = client.search_questions("factura", topics=topics)

# ❌ Malo - extrae dos veces
results1 = client.search_questions("IVA")  # Extrae todo
results2 = client.search_questions("factura")  # Extrae todo otra vez
```

---

## 📞 Soporte

Para problemas o preguntas:
1. Revisar esta documentación
2. Ejecutar el script de prueba: `extract_faqs.py`
3. Revisar logs (nivel INFO o DEBUG)

---

**Versión:** 1.0.0
**Fecha:** 2025-11-10
