# Agents System

Sistema de agentes de IA para la plataforma Fizko.

## Estructura

```
agents/
├── core/                    # Componentes fundamentales
│   ├── context.py          # FizkoContext - contexto compartido
│   ├── context_loader.py   # Carga de info de empresa/usuario
│   └── *_attachment_store.py  # Gestión de attachments
│
├── orchestration/          # Sistema de orquestación multi-agente
│   ├── handoffs_manager.py      # Manager global (singleton)
│   ├── multi_agent_orchestrator.py  # Orquestador
│   └── unified_agent.py    # Agente unificado (legacy)
│
├── specialized/            # Agentes especializados
│   ├── supervisor_agent.py        # Supervisor (router)
│   ├── general_knowledge_agent.py # Conocimiento general
│   └── tax_documents_agent.py     # Documentos tributarios
│
├── tools/                  # Herramientas de negocio
│   ├── tax/               # Tools de impuestos
│   │   ├── documentos_tributarios_tools.py
│   │   ├── f29_tools.py
│   │   ├── operacion_renta_tools.py
│   │   ├── remuneraciones_tools.py
│   │   └── sii_general_tools.py
│   └── widgets/           # Widgets UI (ChatKit)
│       ├── widgets.py
│       └── tax_widget_tools.py
│
├── ui_tools/              # Sistema de UI Tools (notificaciones, etc.)
│   ├── core/             # Base classes y dispatcher
│   └── tools/            # Implementaciones específicas
│
├── legacy/               # ⚠️ DEPRECATED - Sistema antiguo
│
├── chat.py              # Integración con ChatKit
├── general_knowledge_agent.py   # Agent raíz
└── supervisor_agent.py          # Agent raíz
```

## Uso

### Multi-Agent Mode (Recomendado)

```python
from app.agents.orchestration import handoffs_manager

# Obtener supervisor (entry point)
supervisor = await handoffs_manager.get_supervisor_agent(
    thread_id=thread_id,
    db=db,
    user_id=user_id
)

# El supervisor automáticamente hace handoff a agentes especializados
```

### Unified Mode (Legacy)

```python
from app.agents.orchestration import create_unified_agent

agent = create_unified_agent(
    db=db,
    openai_client=openai_client,
    channel="whatsapp"
)
```

## Componentes principales

### HandoffsManager

Singleton que gestiona orquestadores por thread. Cachea instancias para mantener estado.

```python
from app.agents.orchestration import handoffs_manager

# Obtener o crear orquestador
orchestrator = await handoffs_manager.get_orchestrator(
    thread_id=thread_id,
    db=db
)
```

### FizkoContext

Contexto compartido entre agentes con info de empresa y usuario.

```python
from app.agents.core import FizkoContext, load_company_info

company_info = await load_company_info(db, company_id)
context = FizkoContext(...)
context.company_info = company_info
```

### Tools

Funciones que los agentes pueden llamar para realizar acciones.

```python
from app.agents.tools.tax import get_documentos_tributarios_tools

tools = get_documentos_tributarios_tools(db)
```

## Channels

Los agentes soportan dos canales:

- **`chatkit`**: UI completa con widgets interactivos
- **`whatsapp`**: Solo texto (sin widgets)

## Performance

El sistema está optimizado para:
- ⚡ Caché de orquestadores por thread
- ⚡ Caché de info de usuario (30 min TTL)
- ⚡ Logs atomizados para reducir I/O
- ⚡ Lazy initialization de agentes

## Testing

```bash
# Verificar sintaxis
python3 -m py_compile backend/app/agents/**/*.py

# Run tests
pytest backend/tests/agents/
```

## Convenciones

- **Imports absolutos**: Siempre usar `from app.agents...`
- **Async/await**: Todas las funciones IO son async
- **Type hints**: Siempre agregar type hints
- **Logging**: Usar logger atomizado (ver guía en código)

## Migración desde Legacy

Ver `legacy/README.md` para guía de migración.
