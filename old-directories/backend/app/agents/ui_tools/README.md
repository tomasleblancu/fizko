# UI Tools System

Sistema modular para pre-cargar contexto cuando el usuario interactúa con componentes específicos del frontend.

## 🎯 Concepto

Cuando el usuario hace clic en elementos del UI, el frontend envía parámetros que activan un "UI Tool" en el backend. Este tool:

1. Pre-carga datos relevantes desde la base de datos
2. Formatea el contexto en markdown legible  
3. Prepone el contexto al mensaje del usuario
4. El agente recibe todo y responde inmediatamente

## 📁 Estructura

```
ui_tools/
├── core/                   # Infraestructura
│   ├── base.py            # BaseUITool, UIToolContext, UIToolResult
│   ├── registry.py        # Auto-registro
│   └── dispatcher.py      # Enrutamiento
│
└── tools/                 # Implementaciones
    ├── contact_card.py
    ├── document_detail.py
    ├── tax_summary_iva.py
    ├── tax_summary_revenue.py
    └── tax_summary_expenses.py
```

## 🔧 Uso desde Frontend

### Caso 1: Componente general (sin additional_data)

```typescript
// Resumen tributario, totales del período, etc.
const url = `/chatkit?company_id=${companyId}&ui_component=tax_summary_iva`;
```

### Caso 2: Elemento específico (con additional_data)

```typescript
// Documento, contacto, transacción específica
const params = new URLSearchParams({
  company_id: companyId,
  ui_component: 'document_detail',
  entity_id: documentId,        // UUID del documento
  entity_type: 'sales_document' // Tipo de entidad
});

const url = `/chatkit?${params}`;
```

## 📝 Crear nuevo UI Tool

### 1. Crear archivo en tools/

```python
"""UI Tool for My Component."""

from __future__ import annotations
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from ....db.models import MyModel
from ..core.base import BaseUITool, UIToolContext, UIToolResult
from ..core.registry import ui_tool_registry


@ui_tool_registry.register  # Auto-registro
class MyNewTool(BaseUITool):
    @property
    def component_name(self) -> str:
        return "my_component"  # Debe coincidir con frontend

    @property
    def description(self) -> str:
        return "Descripción corta"

    @property
    def domain(self) -> str:
        return "my_domain"  # contacts, documents, financials, etc.

    async def process(self, context: UIToolContext) -> UIToolResult:
        # Validar
        if not context.db or not context.company_id:
            return UIToolResult(success=False, error="Missing required context")

        try:
            # Extraer additional_data si existe
            entity_id = None
            if context.additional_data:
                entity_id = context.additional_data.get("entity_id")

            # Cargar datos
            data = await self._load_data(context.db, context.company_id, entity_id)

            # Formatear contexto
            context_text = self._format_context(data)

            return UIToolResult(
                success=True,
                context_text=context_text,
                structured_data=data,
            )
        except Exception as e:
            self.logger.error(f"Error: {e}", exc_info=True)
            return UIToolResult(success=False, error=str(e))

    async def _load_data(self, db, company_id, entity_id=None):
        # Tu lógica de carga aquí
        pass

    def _format_context(self, data: dict) -> str:
        return """
## 📊 CONTEXTO: Mi Componente

**Información relevante**

### Datos
- Punto 1
- Punto 2

💡 *El usuario está consultando sobre X. Puedes sugerir Y o Z.*
"""
```

### 2. Registrar en __init__.py

```python
from .my_new_tool import MyNewTool

__all__ = [
    # ... existing ...
    "MyNewTool",
]
```

### 3. Reiniciar servidor

```bash
# El servidor se recarga automáticamente si tienes --reload activo
```

## 🔍 Additional Data

### Parámetros disponibles

| Query Param | Uso | Ejemplo |
|------------|-----|---------|
| `entity_id` | UUID del elemento | `&entity_id=a1b2c3...` |
| `entity_type` | Tipo de entidad | `&entity_type=sales_document` |

### Cuándo usar

✅ **USA additional_data:**
- Usuario hace clic en elemento específico (documento, contacto)
- Necesitas cargar detalles de una entidad particular
- Tienes un UUID o identificador único

❌ **NO uses additional_data:**
- Contexto general (resumen de período, totales)
- Información viene del mensaje del usuario
- Análisis agregado sin entidad específica

### Ejemplo

```python
async def process(self, context: UIToolContext) -> UIToolResult:
    # Verificar si hay additional_data
    if context.additional_data and "entity_id" in context.additional_data:
        # Cargar elemento específico
        entity_id = context.additional_data["entity_id"]
        entity_type = context.additional_data.get("entity_type", "default")
        data = await self._load_specific_entity(db, entity_id, entity_type)
    else:
        # Cargar datos generales
        data = await self._load_summary(db, company_id)
```

## 📊 Tools Actuales

| Tool | Component Name | Additional Data | Descripción |
|------|---------------|----------------|-------------|
| ContactCardTool | `contact_card` | ❌ | Contactos y transacciones |
| TaxSummaryIVATool | `tax_summary_iva` | ❌ | Cálculo IVA del período |
| TaxSummaryRevenueTool | `tax_summary_revenue` | ❌ | Ingresos + top clientes |
| TaxSummaryExpensesTool | `tax_summary_expenses` | ❌ | Gastos + top proveedores |
| DocumentDetailTool | `document_detail` | ✅ | Detalles documento específico |

## 🧪 Testing

```bash
# Ver tools registrados
python3 -c "
import sys
sys.path.insert(0, 'backend')
from app.agents.ui_tools.core import ui_tool_registry
print('Tools:', [name for name, _, _ in ui_tool_registry.list_tools()])
"
```

## 🎨 Best Practices

### Contexto Rico

```python
# ✅ BUENO
return """
## 📊 CONTEXTO: Análisis de Ventas

**Empresa XYZ** (RUT: 12345678-9)
**Período:** Octubre 2025

### 💰 Resumen
- Total Ventas: $1.500.000
- 45 documentos

### 👥 Top 3 Clientes
1. Cliente A: $500.000
2. Cliente B: $300.000
3. Cliente C: $200.000

💡 *El usuario está analizando ventas. Puedes detallar por tipo de documento o comparar períodos.*
"""

# ❌ MALO
return f"Total: {total}, Docs: {count}"
```

### Validaciones

```python
# ✅ BUENO: Validar al inicio
if not context.db:
    return UIToolResult(success=False, error="DB not available")
if not context.company_id:
    return UIToolResult(success=False, error="Company ID required")

# ❌ MALO: Esperar errores más tarde
data = await self._load(context.db)  # Puede fallar
```

## 📚 Referencias

- Integration: [../../main.py](../../main.py) líneas 160-177
- Agent prepending: [../chat.py](../chat.py) líneas 107-110
