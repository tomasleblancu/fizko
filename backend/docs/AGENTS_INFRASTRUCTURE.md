# Agents Infrastructure - Backend V2

## ✅ Status: COMPLETE

La infraestructura completa del sistema de agentes ha sido copiada exitosamente desde `backend/app/agents` a `backend-v2/app/agents`.

## 📊 Resumen de Archivos Copiados

**Total: 90 archivos Python**

Todos los archivos compilan sin errores ✅

## 📁 Estructura de Directorios

```
backend-v2/app/agents/
├── config/                    # Configuración de agentes
├── core/                      # Funcionalidad core (contexto, stores, loaders)
├── guardrails/               # Validaciones y seguridad
│   └── implementations/      # Implementaciones específicas de guardrails
├── instructions/             # Instrucciones de agentes por categoría
├── orchestration/            # Coordinación multi-agente
├── specialized/              # Agentes especializados
├── tools/                    # Herramientas de agentes
│   ├── feedback/            # Herramientas de feedback
│   ├── memory/              # Herramientas de memoria
│   ├── orchestration/       # Herramientas de orquestación
│   ├── payroll/             # Herramientas de nómina
│   ├── settings/            # Herramientas de configuración
│   ├── tax/                 # Herramientas tributarias
│   └── widgets/             # Herramientas de widgets UI
├── ui_tools/                 # Sistema de herramientas UI
│   ├── core/                # Core UI tools
│   └── tools/               # Implementaciones de UI tools
├── runner.py                 # Ejecutor principal de agentes
└── __init__.py              # Inicialización del módulo
```

## 🔧 Componentes Clave Copiados

### 1. Core (`app/agents/core/`)
- **context.py**: Sistema de contexto compartido (FizkoContext)
- **context_loaders.py**: Cargadores de contexto
- **attachment_stores.py**: Almacenamiento de adjuntos
- **base.py**: Clases base

### 2. Orchestration (`app/agents/orchestration/`)
- **handoffs_manager.py**: Gestor de transferencias entre agentes
- **multi_agent_orchestrator.py**: Orquestador multi-agente

### 3. Specialized Agents (`app/agents/specialized/`)
- **general_knowledge_agent.py**: Agente de conocimiento general
- **tax_documents_agent.py**: Agente de documentos tributarios
- **monthly_taxes_agent.py**: Agente de impuestos mensuales
- **payroll_agent.py**: Agente de nómina
- **expense_agent.py**: Agente de gastos
- **feedback_agent.py**: Agente de feedback
- **settings_agent.py**: Agente de configuración

### 4. Tools (`app/agents/tools/`)

#### Tax Tools (`tax/`)
- **f29_tools.py**: Herramientas de formulario 29
- **documentos_tributarios_tools.py**: Herramientas de documentos
- **expense_tools.py**: Herramientas de gastos
- **operacion_renta_tools.py**: Herramientas de operación renta
- **remuneraciones_tools.py**: Herramientas de remuneraciones
- **sii_general_tools.py**: Herramientas generales SII

#### Widget Tools (`widgets/`)
- Herramientas para componentes UI interactivos

#### Payroll Tools (`payroll/`)
- **payroll_tools.py**: Herramientas de nómina

#### Memory Tools (`memory/`)
- **memory_tools.py**: Herramientas de memoria

#### Settings Tools (`settings/`)
- **notification_tools.py**: Herramientas de notificaciones

#### Feedback Tools (`feedback/`)
- **feedback_tools.py**: Herramientas de feedback

#### Orchestration Tools (`orchestration/`)
- **return_to_supervisor.py**: Herramienta para retornar al supervisor

### 5. UI Tools (`app/agents/ui_tools/`)
- **core/**: Sistema core de UI tools
- **tools/**: Implementaciones específicas de componentes UI

### 6. Guardrails (`app/agents/guardrails/`)
- Sistema de validación y seguridad para agentes
- Implementaciones específicas de guardrails

### 7. Instructions (`app/agents/instructions/`)
- Instrucciones categorizadas para agentes

### 8. Config (`app/agents/config/`)
- Configuración del sistema de agentes

### 9. Runner (`app/agents/runner.py`)
- Ejecutor principal del sistema de agentes

## ✅ Verificación de Compilación

Todos los 90 archivos Python han sido verificados:

```bash
find app/agents -name "*.py" -type f -exec python3 -m py_compile {} +
```

**Resultado**: ✅ Sin errores de compilación

## 📦 Dependencias Actuales

Las dependencias actuales en `pyproject.toml` son suficientes para la compilación básica:

```toml
[project]
dependencies = [
    "fastapi>=0.114.1,<0.116",
    "uvicorn[standard]>=0.36,<0.37",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "requests>=2.31.0",
    "beautifulsoup4>=4.12.0",
    "selenium>=4.0.0",
    "selenium-wire>=5.1.0",
    "webdriver-manager>=4.0.0",
    "blinker<1.8",
    "setuptools>=68.0",
    "pypdf>=6.0.0",
    "python-dateutil>=2.8.0",
]
```

## 🔄 Próximos Pasos

Según lo indicado por el usuario: **"primero la infraestructura de 'agents', luego agregaremos servicios y routers"**

**Pendiente:**
1. ✅ Infraestructura de agentes (COMPLETADO)
2. ⏳ Agregar servicios de agentes
3. ⏳ Agregar routers de agentes

## 📋 Notas Importantes

### Arquitectura Multi-Agente

El sistema sigue una arquitectura de **supervisor + agentes especializados**:

```
User Query
    ↓
HandoffsManager
    ↓
Multi-Agent Orchestrator
    ↓
├─→ General Knowledge Agent
├─→ Tax Documents Agent
├─→ Monthly Taxes Agent
├─→ Payroll Agent
├─→ Expense Agent
└─→ [Otros agentes especializados]
```

### Convenciones Importantes

1. **Contexto Compartido**: Todos los agentes usan `FizkoContext` para estado compartido
2. **Tools con Decoradores**: Usar `@function_tool` para definir herramientas
3. **Imports Absolutos**: Siempre usar `from app.agents...`
4. **Dos Canales**: `chatkit` (con widgets UI) y `whatsapp` (texto simple)

### Diferencias con Backend Original

**Backend-v2 es STATELESS:**
- ❌ No tiene base de datos
- ❌ No tiene autenticación
- ✅ Enfocado en procesamiento SII
- ✅ Respuestas directas sin persistencia

Esto significa que algunas herramientas de agentes que dependen de la base de datos **necesitarán adaptación** cuando se agreguen los servicios y routers.

## 🎯 Estado del Proyecto

| Componente | Estado | Archivos | Notas |
|-----------|--------|----------|-------|
| Config | ✅ Copiado | - | Configuración de agentes |
| Core | ✅ Copiado | - | Contexto, loaders, stores |
| Guardrails | ✅ Copiado | - | Validaciones |
| Instructions | ✅ Copiado | - | Instrucciones por categoría |
| Orchestration | ✅ Copiado | - | Multi-agent coordination |
| Specialized | ✅ Copiado | 7 agentes | Sin supervisor_agent.py |
| Tools | ✅ Copiado | 6 categorías | Tax, payroll, widgets, etc. |
| UI Tools | ✅ Copiado | - | Sistema de componentes UI |
| Runner | ✅ Copiado | runner.py | Ejecutor principal |
| **TOTAL** | **✅ COMPLETO** | **90 archivos** | **Sin errores** |

## 🚀 Listo Para

La infraestructura de agentes está **100% lista** para que se agreguen:
- Servicios de agentes
- Routers de agentes
- Integración con endpoints del backend-v2

---

**Fecha de Completación**: 19 de Noviembre, 2025
**Archivos Copiados**: 90 Python files
**Errores de Compilación**: 0 ✅
**Status**: INFRASTRUCTURE COMPLETE - READY FOR SERVICES
