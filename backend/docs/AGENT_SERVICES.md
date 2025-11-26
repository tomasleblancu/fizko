# Agent Services - Backend V2

## ✅ Estado: COMPLETO

Los servicios de agentes han sido creados para backend-v2 con versiones **simplificadas y stateless** adaptadas para el entorno sin base de datos.

## 📁 Archivos Creados

```
app/services/
├── __init__.py                          # Módulo principal de servicios
└── agents/
    ├── __init__.py                      # Módulo de servicios de agentes
    ├── agent_executor.py                # AgentService - Ejecutor de agentes
    └── context_builder.py               # ContextBuilder - Constructor de contexto
```

## 🎯 Componentes

### 1. AgentService (`agent_executor.py`)

Servicio de ejecución de agentes **sin dependencias de base de datos**.

**Diferencias con backend original:**
- ❌ NO se conecta a base de datos
- ❌ NO carga contexto de compañía desde DB
- ❌ NO maneja UI tools (sin ChatKit)
- ✅ Acepta company_info como parámetro
- ✅ Versión completamente stateless
- ✅ Enfocado en tareas SII

**Métodos principales:**

#### `execute()`
Ejecución genérica con contexto proporcionado.

```python
from app.services.agents import AgentService

service = AgentService()

result = await service.execute(
    user_id="user123",
    company_id="77794858-k",
    thread_id="thread_1",
    message="¿Qué documentos tengo pendientes?",
    company_info={
        "rut": "77794858-k",
        "razon_social": "EMPRESA DEMO SPA"
    }
)

print(result.response_text)
```

#### `execute_with_sii_context()`
Ejecución especializada con contexto SII (desde endpoint `/verify`).

```python
# 1. Verificar credenciales SII
verify_response = requests.post("/api/sii/verify", json={
    "rut": "77794858",
    "dv": "k",
    "password": "******"
})

contribuyente_info = verify_response.json()["contribuyente_info"]

# 2. Ejecutar agente con contexto SII
service = AgentService()
result = await service.execute_with_sii_context(
    user_id="user123",
    rut="77794858-k",
    thread_id="thread_1",
    message="¿Cuál es mi razón social?",
    contribuyente_info=contribuyente_info
)
```

**Parámetros de `execute()`:**

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `user_id` | str | ✅ | Identificador del usuario |
| `company_id` | str | ✅ | Identificador de la compañía (RUT) |
| `thread_id` | str | ✅ | ID de conversación/thread |
| `message` | str o List[Dict] | ✅ | Mensaje del usuario |
| `company_info` | Dict | ❌ | Información de la compañía |
| `attachments` | List[Dict] | ❌ | Adjuntos procesados |
| `metadata` | Dict | ❌ | Metadata adicional |
| `channel` | str | ❌ | Canal ("api", "sii") |
| `stream` | bool | ❌ | Si hacer streaming (default: False) |

**Retorna:** `AgentExecutionResult`

```python
class AgentExecutionResult:
    response_text: str      # Respuesta del agente
    metadata: Dict          # Metadata adicional
    # ... otros campos
```

### 2. ContextBuilder (`context_builder.py`)

Constructor de contexto **sin dependencias de base de datos**.

**Diferencias con backend original:**
- ❌ NO carga company info desde DB
- ❌ NO maneja cache
- ❌ NO carga UI tool context
- ✅ Solo formatea datos proporcionados
- ✅ Métodos utilitarios para formatear contexto SII

**Métodos principales:**

#### `format_company_context_text()`
Formatea información de compañía como texto para el agente.

```python
from app.services.agents import ContextBuilder

company_info = {
    "rut": "77794858-k",
    "razon_social": "EMPRESA DEMO SPA",
    "actividad_economica": "Servicios de software",
    "direccion": "Av. Apoquindo 1234",
    "comuna": "Las Condes"
}

context_text = ContextBuilder.format_company_context_text(company_info)
```

**Output:**
```
# Información de la Empresa
- RUT: 77794858-k
- Razón Social: EMPRESA DEMO SPA
- Actividad Económica: Servicios de software
- Dirección: Av. Apoquindo 1234, Las Condes
```

#### `format_sii_document_context()`
Formatea documentos SII (compras/ventas) como contexto.

```python
compras = [
    {
        "folio": "123",
        "tipo_documento": "Factura Electrónica",
        "fecha_emision": "2024-01-15",
        "rut_emisor": "12345678-9",
        "razon_social_emisor": "PROVEEDOR ABC LTDA",
        "monto_neto": 100000,
        "monto_iva": 19000,
        "monto_total": 119000
    }
]

context = ContextBuilder.format_sii_document_context("compras", compras)
```

**Parámetros:**
- `document_type`: Tipo ("compras", "ventas", "f29", "boletas_honorarios")
- `documents`: Lista de documentos
- `max_documents`: Máximo a incluir (default: 10)

#### `format_f29_context()`
Formatea datos de Formulario 29 como contexto.

```python
f29_data = {
    "periodo": "2024-01",
    "folio": "987654321",
    "debito_fiscal": 1000000,
    "credito_fiscal": 500000,
    "iva_a_pagar": 500000,
    "ppm": 100000,
    "total_a_pagar": 600000,
    "fecha_vencimiento": "2024-02-12",
    "estado": "Pendiente"
}

context = ContextBuilder.format_f29_context(f29_data)
```

#### `build_agent_context()`
Combina múltiples fuentes de contexto.

```python
complete_context = ContextBuilder.build_agent_context(
    company_info=company_info,
    recent_compras=compras_list,
    recent_ventas=ventas_list,
    recent_f29=f29_data,
    custom_context="Información adicional..."
)
```

**Parámetros (todos opcionales):**
- `company_info`: Información de compañía
- `recent_compras`: Documentos de compra recientes
- `recent_ventas`: Documentos de venta recientes
- `recent_f29`: Formulario F29 reciente
- `custom_context`: Contexto personalizado

## 💡 Casos de Uso

### Caso 1: Agente con Contexto Mínimo

```python
from app.services.agents import AgentService

service = AgentService()

result = await service.execute(
    user_id="user123",
    company_id="demo",
    thread_id="thread_1",
    message="¿Qué es el IVA?"
)

print(result.response_text)
# "El IVA (Impuesto al Valor Agregado) es un impuesto..."
```

### Caso 2: Agente con Contexto de Compañía

```python
company_info = {
    "rut": "77794858-k",
    "razon_social": "EMPRESA DEMO SPA",
    "actividad_economica": "Servicios de software"
}

result = await service.execute(
    user_id="user123",
    company_id="77794858-k",
    thread_id="thread_1",
    message="Dame un resumen de mi empresa",
    company_info=company_info
)
```

### Caso 3: Agente con Contexto SII Completo

```python
from app.services.agents import AgentService, ContextBuilder

# 1. Obtener datos desde endpoints SII
verify_result = # ... llamar a /api/sii/verify
compras_result = # ... llamar a /api/sii/compras
ventas_result = # ... llamar a /api/sii/ventas
f29_result = # ... llamar a /api/sii/f29

# 2. Construir contexto completo
context = ContextBuilder.build_agent_context(
    company_info=verify_result["contribuyente_info"],
    recent_compras=compras_result["data"][:10],
    recent_ventas=ventas_result["data"][:10],
    recent_f29=f29_result
)

# 3. Ejecutar agente
service = AgentService()
result = await service.execute(
    user_id="user123",
    company_id="77794858-k",
    thread_id="thread_1",
    message="Dame un análisis completo de mi situación tributaria",
    company_info=verify_result["contribuyente_info"],
    metadata={"sii_context": context}
)
```

### Caso 4: Pipeline Completo (Verify → Agent)

```python
import requests
from app.services.agents import AgentService

# 1. Verificar credenciales SII
verify_response = requests.post("http://localhost:8000/api/sii/verify", json={
    "rut": "77794858",
    "dv": "k",
    "password": "mi_password"
})

if verify_response.status_code != 200:
    raise Exception("Credenciales inválidas")

contribuyente_info = verify_response.json()["contribuyente_info"]

# 2. Ejecutar agente con contexto SII
service = AgentService()
result = await service.execute_with_sii_context(
    user_id="user123",
    rut="77794858-k",
    thread_id="thread_1",
    message="Explícame mi situación tributaria actual",
    contribuyente_info=contribuyente_info
)

print(result.response_text)
```

## 🔄 Integración con Backend V2

### Con Endpoint de Verificación

```python
# routers/agents.py (ejemplo)
from fastapi import APIRouter
from app.services.agents import AgentService

router = APIRouter()

@router.post("/chat")
async def chat_with_agent(
    user_id: str,
    rut: str,
    message: str,
    contribuyente_info: dict
):
    service = AgentService()

    result = await service.execute_with_sii_context(
        user_id=user_id,
        rut=rut,
        thread_id=f"chat_{user_id}_{rut}",
        message=message,
        contribuyente_info=contribuyente_info
    )

    return {"response": result.response_text}
```

### Con Múltiples Endpoints SII

```python
@router.post("/advanced-chat")
async def advanced_chat(
    user_id: str,
    rut: str,
    message: str,
    include_documents: bool = True
):
    # 1. Obtener datos SII
    sii_client = SIIClient(...)
    contribuyente = sii_client.get_contribuyente()

    compras = []
    ventas = []
    if include_documents:
        compras = sii_client.get_compras(periodo="202401")
        ventas = sii_client.get_ventas(periodo="202401")

    # 2. Construir contexto
    from app.services.agents import ContextBuilder
    context = ContextBuilder.build_agent_context(
        company_info=contribuyente,
        recent_compras=compras[:10],
        recent_ventas=ventas[:10]
    )

    # 3. Ejecutar agente
    service = AgentService()
    result = await service.execute(
        user_id=user_id,
        company_id=rut,
        thread_id=f"advanced_{user_id}",
        message=message,
        company_info=contribuyente,
        metadata={"full_context": context}
    )

    return {"response": result.response_text}
```

## 🚀 Compilación y Verificación

```bash
# Verificar que los servicios compilan
python3 -m py_compile app/services/agents/agent_executor.py
python3 -m py_compile app/services/agents/context_builder.py
python3 -m py_compile app/services/agents/__init__.py
python3 -m py_compile app/services/__init__.py

# O todos a la vez
find app/services -name "*.py" -exec python3 -m py_compile {} +
```

## 📊 Comparación con Backend Original

| Característica | Backend Original | Backend V2 |
|----------------|------------------|------------|
| Base de datos | ✅ PostgreSQL/Supabase | ❌ Sin DB |
| Cache de contexto | ✅ 30 min TTL | ❌ Sin cache |
| UI Tools | ✅ ChatKit widgets | ❌ No soportado |
| Canales | web, whatsapp | api, sii |
| Company context | Carga desde DB | Recibe como parámetro |
| Streaming | ✅ Soporte completo | ⚠️ Limitado |
| Attachments | ✅ Con storage | ⚠️ En memoria |
| Session management | ✅ Persistente | ❌ Stateless |

## 🎯 Próximos Pasos

1. ✅ Servicios de agentes - **COMPLETADO**
2. ⏳ **Routers de agentes** - Siguiente paso
3. ⏳ Tests de integración

## 📝 Notas Importantes

### Limitaciones

1. **Sin persistencia**: Los threads/conversaciones no se guardan
2. **Sin UI tools**: No hay componentes interactivos ChatKit
3. **Sin streaming avanzado**: Streaming limitado a respuestas texto
4. **Sin session management**: Cada request es independiente

### Ventajas

1. **Stateless**: Fácil de escalar horizontalmente
2. **Simple**: Sin complejidad de base de datos
3. **Rápido**: No hay overhead de DB queries
4. **Portable**: Puede correrse anywhere con Python

### Recomendaciones

- Usar `execute_with_sii_context()` para integración con SII
- Construir contexto rico con `ContextBuilder` para mejores respuestas
- Mantener threads en memoria del cliente (frontend/app)
- Considerar agregar cache en Redis si se necesita persistencia

---

**Fecha de Creación**: 19 de Noviembre, 2025
**Archivos**: 4 Python files
**Status**: ✅ SERVICES COMPLETE
