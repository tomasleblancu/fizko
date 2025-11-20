# Router de WhatsApp - Arquitectura Modular

Este módulo gestiona toda la integración de WhatsApp con Kapso, incluyendo envío de mensajes, webhooks y procesamiento de IA.

## 📁 Estructura de Archivos

```
whatsapp/
├── __init__.py                 # Exporta routers principales
├── main.py                     # Punto de entrada - agrega todos los sub-routers (45 líneas)
├── schemas.py                  # Pydantic models para responses (30 líneas)
├── helpers.py                  # Helper functions compartidas (66 líneas)
│
├── routes/                     # Sub-routers organizados por funcionalidad
│   ├── __init__.py
│   ├── messaging.py            # Envío de mensajes (text, media, template, interactive) (214 líneas)
│   ├── conversations.py        # CRUD de conversaciones (109 líneas)
│   ├── contacts.py             # Búsqueda y gestión de contactos (164 líneas)
│   ├── misc.py                 # Templates, inbox, health (85 líneas)
│   └── webhooks.py             # Procesamiento de webhooks de Kapso (434 líneas)
│
├── handlers/                   # Lógica de negocio (reservado para futuros refactors)
│   └── __init__.py
│
├── main_old.py                 # Backup del archivo original (1029 líneas)
└── alternative_auth.py         # Métodos alternativos de autenticación
```

## 🎯 Distribución de Responsabilidades

### **main.py** (45 líneas)
Router principal que orquesta todos los sub-routers.

```python
from .routes import messaging, conversations, contacts, misc, webhooks

# Router autenticado con JWT
router.include_router(messaging.router)
router.include_router(conversations.router)
router.include_router(contacts.router)
router.include_router(misc.router)

# Router de webhooks (sin JWT, usa HMAC)
webhook_router.include_router(webhooks.router)
```

### **schemas.py** (30 líneas)
Modelos de respuesta compartidos:
- `MessageResponse`: Para mensajes enviados
- `ConversationResponse`: Para conversaciones
- `ContactResponse`: Para contactos

### **helpers.py** (66 líneas)
Funciones auxiliares compartidas:
- `find_recent_notification()`: Busca notificaciones recientes en una conversación
- `get_notification_ui_component()`: Mapea entity_type a UI Tool component

---

## 📦 Sub-Routers (routes/)

### **1. messaging.py** (214 líneas)
Endpoints para envío de mensajes:

- `POST /send/text` - Mensaje de texto
- `POST /send/media` - Imagen, video, audio, documento
- `POST /send/template` - Plantilla de WhatsApp Business
- `POST /send/interactive` - Botones o listas

**Dependendencias:**
- `app.services.whatsapp.get_whatsapp_service()`
- `app.integrations.kapso.models.*`

---

### **2. conversations.py** (109 líneas)
Endpoints para gestión de conversaciones:

- `GET /conversations` - Listar conversaciones
- `GET /conversations/{id}` - Detalles de conversación
- `POST /conversations/{id}/end` - Finalizar conversación

**Dependencies:**
- `app.services.whatsapp.get_whatsapp_service()`

---

### **3. contacts.py** (164 líneas)
Endpoints para contactos y mensajes:

- `GET /contacts/search` - Buscar contactos
- `GET /contacts/{id}/history` - Historial de mensajes
- `POST /contacts/{id}/note` - Agregar nota
- `POST /messages/mark-read` - Marcar como leído
- `GET /messages/search` - Buscar mensajes

**Dependencies:**
- `app.services.whatsapp.get_whatsapp_service()`

---

### **4. misc.py** (85 líneas)
Endpoints misceláneos:

- `GET /templates` - Listar plantillas WhatsApp Business
- `GET /inbox` - Bandeja de entrada
- `GET /health` - Health check

**Dependencies:**
- `app.services.whatsapp.get_whatsapp_service()`

---

### **5. webhooks.py** (434 líneas) 🔥
**El más importante**: Procesador de webhooks de Kapso.

**Flujo completo:**
1. Validación HMAC de firma
2. Parseo de eventos (soporta batching)
3. Autenticación de usuario por número de WhatsApp
4. Detección de contexto de notificaciones
5. Procesamiento de media (imágenes, PDFs)
6. Ejecución del agente de IA
7. Envío de respuesta
8. Guardado de historial en background

**Dependencies:**
- `app.services.whatsapp.*`
- `app.services.whatsapp.agent_runner.WhatsAppAgentRunner`
- `app.services.whatsapp.media_processor.get_media_processor()`
- `app.agents.ui_tools.core.dispatcher.UIToolDispatcher`
- `app.services.whatsapp.conversation_manager.WhatsAppConversationManager`

**Endpoint:**
- `POST /webhook` (sin autenticación JWT)

---

## 🔄 Mejoras sobre Versión Original

### **Antes** (main_old.py - 1029 líneas)
- ❌ Todo en un solo archivo monolítico
- ❌ Difícil de mantener y testear
- ❌ Acoplamiento alto entre funcionalidades
- ❌ Difícil de entender el flujo

### **Después** (estructura modular - 1052 líneas totales)
- ✅ Separación por responsabilidades
- ✅ Fácil de localizar bugs
- ✅ Fácil de agregar nuevos endpoints
- ✅ Mejor testability (cada módulo se puede testear independientemente)
- ✅ Imports claros y organizados
- ✅ Reutilización de código (helpers, schemas)

---

## 🚀 Cómo Agregar Nuevos Endpoints

### Ejemplo: Agregar endpoint de estadísticas

**1. Crear nuevo archivo** `routes/statistics.py`:
```python
"""
Endpoints para estadísticas de WhatsApp
"""
import logging
from fastapi import APIRouter

from app.services.whatsapp import get_whatsapp_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/statistics")
async def get_statistics():
    """Obtiene estadísticas de mensajes"""
    whatsapp_service = get_whatsapp_service()
    # ... lógica
    return {"messages_sent": 100}
```

**2. Registrar en** `routes/__init__.py`:
```python
from . import messaging, conversations, contacts, misc, webhooks, statistics

__all__ = [..., "statistics"]
```

**3. Incluir en** `main.py`:
```python
from .routes import messaging, ..., statistics

router.include_router(statistics.router)
```

¡Listo! 🎉

---

## 🧪 Testing

Cada módulo puede ser testeado independientemente:

```python
# test_messaging.py
from app.routers.whatsapp.routes import messaging

async def test_send_text_message():
    # Mock whatsapp_service
    # Test messaging.send_text_message()
    pass
```

---

## 📊 Métricas

| Archivo | Líneas | Responsabilidad |
|---------|--------|----------------|
| main.py | 45 | Orquestación |
| schemas.py | 30 | Modelos |
| helpers.py | 66 | Utilities |
| messaging.py | 214 | Envío de mensajes |
| conversations.py | 109 | Conversaciones |
| contacts.py | 164 | Contactos y búsqueda |
| misc.py | 85 | Misc endpoints |
| webhooks.py | 434 | Procesamiento de webhooks |
| **TOTAL** | **1,147** | **Código organizado** |

---

## 🔗 Referencias

- **Servicio Principal**: `app/services/whatsapp/service.py`
- **Cliente Kapso**: `app/integrations/kapso/client.py`
- **Agent Runner**: `app/services/whatsapp/agent_runner.py`
- **Media Processor**: `app/services/whatsapp/media_processor.py`
- **Conversation Manager**: `app/services/whatsapp/conversation_manager.py`

---

## 📝 Notas

- El archivo `main_old.py` se mantiene como backup y puede eliminarse después de verificar que todo funciona correctamente
- La carpeta `handlers/` está reservada para futuros refactors donde se extraiga lógica de negocio compleja
- Los webhooks permanecen en un solo archivo debido a su complejidad y alto acoplamiento interno

---

Creado: 2025-11-01
Autor: Sistema de Modularización Automática
