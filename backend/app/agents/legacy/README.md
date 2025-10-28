# Legacy Multi-Agent System

⚠️ **DEPRECATED - DO NOT USE**

Este directorio contiene el sistema de agentes antiguo que ha sido reemplazado por el nuevo sistema de orquestación.

## ¿Por qué está deprecado?

El sistema antiguo tenía varios problemas:
- Gestión compleja de handoffs
- Difícil de mantener y extender
- Performance subóptimo

## Sistema actual

En su lugar, usa:
- **`app.agents.orchestration`** - Sistema de orquestación moderno
- **`app.agents.specialized`** - Agentes especializados actuales
- **`app.agents.core`** - Componentes core compartidos

## Migración

Si encuentras código que importa desde `app.agents.legacy`, actualízalo para usar:

```python
# ❌ Antiguo (NO USAR)
from app.agents.legacy.multi_agent_system import ...

# ✅ Nuevo
from app.agents.orchestration import handoffs_manager
```

## Eliminación futura

Este código será eliminado en una futura versión. No agregues nuevas dependencias a estos archivos.
