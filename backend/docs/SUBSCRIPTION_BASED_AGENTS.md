# Subscription-Based Agent & Tool Access

Sistema de restricción de acceso a agentes y herramientas según el plan de suscripción de la empresa.

## 📋 Tabla de Contenidos

- [Visión General](#visión-general)
- [Arquitectura](#arquitectura)
- [Configuración de Planes](#configuración-de-planes)
- [Uso en Agentes](#uso-en-agentes)
- [Uso en Tools](#uso-en-tools)
- [Flujo de Bloqueos](#flujo-de-bloqueos)
- [Mensajes al Usuario](#mensajes-al-usuario)
- [Testing](#testing)

## Visión General

El sistema permite restringir el acceso a:
1. **Agentes completos** (ej: Payroll Agent requiere Plan Pro)
2. **Tools individuales** (ej: `get_f29_data` requiere Plan Pro)

### Ventajas

✅ **Control granular**: Bloquear agentes completos o solo herramientas específicas
✅ **Mensajes educativos**: Los agentes reformulan bloqueos de forma natural
✅ **Upselling inteligente**: Se explican beneficios, no solo "acceso denegado"
✅ **Reutiliza infraestructura**: Usa `SubscriptionService` existente
✅ **Sin romper API**: Respuestas estructuradas que agentes pueden procesar

## Arquitectura

### Componentes Principales

```
SubscriptionService (existente)
    ↓
SubscriptionGuard (nuevo)
    ↓ valida
[MultiAgentOrchestrator] → Crea solo agentes permitidos
    ↓
[HandoffsManager] → Pasa company_id
    ↓
[Supervisor Agent] → Recibe respuesta de bloqueo
    ↓ procesa y reformula
[Usuario] ← Mensaje educativo amigable
```

### Archivos Nuevos

- `backend/app/agents/core/subscription_guard.py` - Valida acceso a agentes/tools
- `backend/app/agents/core/subscription_responses.py` - Genera respuestas estructuradas
- `backend/app/agents/tools/decorators.py` - Decorators para tools

### Archivos Modificados

- `backend/app/agents/orchestration/multi_agent_orchestrator.py` - Filtra agentes por suscripción
- `backend/app/agents/orchestration/handoffs_manager.py` - Pasa company_id
- `backend/app/config/constants.py` - Instrucciones del supervisor actualizadas

## Configuración de Planes

### Estructura de Features

Los planes de suscripción tienen un campo `features` (JSONB) con esta estructura:

```json
{
  "agents": {
    "general_knowledge": true,      // Todos los planes
    "tax_documents": true,           // Plan Básico+
    "payroll": false,                // Plan Pro+ ⭐
    "settings": true                 // Todos los planes
  },
  "tools": {
    "get_documents": true,           // Básico+
    "get_documents_summary": true,   // Básico+
    "get_f29_data": false,          // Pro+ ⭐
    "get_people": false,            // Pro+ ⭐
    "create_person": false,         // Pro+ ⭐
    "calculate_payroll": false      // Enterprise ⭐⭐
  },
  "limits": {
    "max_monthly_queries": 100,     // null = ilimitado
    "max_documents_per_query": 20
  }
}
```

### Ejemplo: Migración para Configurar Planes

```sql
-- Actualizar plan Pro con acceso a agente de nómina
UPDATE subscription_plans
SET features = jsonb_set(
    features,
    '{agents}',
    '{"general_knowledge": true, "tax_documents": true, "payroll": true, "settings": true}'::jsonb
)
WHERE code = 'pro';

-- Actualizar herramientas disponibles en Plan Pro
UPDATE subscription_plans
SET features = jsonb_set(
    features,
    '{tools}',
    '{"get_documents": true, "get_f29_data": true, "get_people": true, "create_person": true}'::jsonb
)
WHERE code = 'pro';
```

## Uso en Agentes

### 1. En MultiAgentOrchestrator

El orchestrator filtra automáticamente los agentes disponibles:

```python
# Al inicializar con company_id
orchestrator = create_multi_agent_orchestrator(
    db=db,
    openai_client=openai_client,
    company_id=company_id,  # ⭐ Requerido para validación
    thread_id=thread_id,
    channel="web"
)

# Solo se crean agentes permitidos por la suscripción
# Si payroll está bloqueado, payroll_agent NO se crea
```

### 2. En HandoffsManager

```python
# Pasar company_id al obtener supervisor
supervisor = await handoffs_manager.get_supervisor_agent(
    thread_id=thread_id,
    db=db,
    user_id=user_id,
    company_id=company_id,  # ⭐ Requerido
    channel="web"
)
```

### 3. En Router de ChatKit

```python
from app.dependencies.company import get_user_company_id

@router.post("/chatkit")
async def chatkit_endpoint(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user),
    company_id: UUID = Depends(get_user_company_id)  # ⭐ Obtener company_id
):
    # Pasar company_id al supervisor
    supervisor_agent = await handoffs_manager.get_supervisor_agent(
        thread_id=request.thread_id,
        db=db,
        user_id=user_id,
        company_id=company_id,  # ⭐ Validación de suscripción
        channel="web"
    )
```

## Uso en Tools

### Decorator @require_subscription_tool

Para restringir herramientas individuales:

```python
from app.agents.tools.decorators import require_subscription_tool

@function_tool(strict_mode=False)
@require_subscription_tool("get_f29_data")  # ⭐ Validación de suscripción
async def get_f29_data(
    ctx: RunContextWrapper[FizkoContext],
    periodo: str
) -> dict[str, Any]:
    """
    Get F29 form data (requires Pro+ subscription).

    If blocked, returns structured error that agent can process.
    """
    # Implementación normal
    # Solo se ejecuta si la validación pasa
    ...
```

### Respuesta de Tool Bloqueado

```json
{
  "error": "subscription_required",
  "blocked": true,
  "blocked_type": "tool",
  "tool_name": "get_f29_data",
  "display_name": "Datos de Formulario 29",
  "plan_required": "pro",
  "user_message": "🔒 Datos de Formulario 29 requiere Plan Pro...",
  "benefits": [
    "Acceso completo a información del F29",
    "Histórico de declaraciones mensuales"
  ],
  "upgrade_url": "/configuracion/suscripcion",
  "alternative_message": "Puedo ayudarte con información general sobre el F29..."
}
```

El agente recibe esta respuesta y puede:
1. Informar al usuario sobre la limitación
2. Mencionar los beneficios del upgrade
3. Ofrecer funcionalidad alternativa
4. Guiar al usuario a la página de suscripciones

## Flujo de Bloqueos

### Caso 1: Agente Bloqueado

```
Usuario: "¿Cuántos empleados tengo?"
    ↓
Supervisor: Intenta handoff a payroll_agent
    ↓
Handoff bloqueado (agente no creado)
    ↓
Supervisor recibe SubscriptionBlockResponse:
{
  "blocked": true,
  "blocked_type": "agent",
  "blocked_item": "payroll",
  "display_name": "Nómina",
  "plan_required": "pro",
  "benefits": ["Gestión completa de empleados", ...],
  ...
}
    ↓
Supervisor reformula para el usuario:
"Entiendo que quieres revisar tu nómina 👥

El módulo de Nómina está disponible en el Plan Pro, que incluye:
• Gestión completa de empleados y colaboradores
• Cálculo automático de remuneraciones
• Asesoría en legislación laboral chilena

¿Te gustaría conocer más sobre el Plan Pro?
Puedes verlo en Configuración > Suscripción.

Mientras tanto, ¿hay algo más en lo que pueda ayudarte? 😊"
```

### Caso 2: Tool Bloqueado

```
Usuario: "Dame el detalle del F29 de octubre"
    ↓
Supervisor: Handoff a tax_documents_agent ✅
    ↓
Tax Agent: Intenta usar get_f29_data()
    ↓
Tool bloqueado por decorator
    ↓
Tax Agent recibe error estructurado:
{
  "error": "subscription_required",
  "blocked": true,
  "tool_name": "get_f29_data",
  "plan_required": "pro",
  "alternative_message": "Puedo ayudarte con información general..."
}
    ↓
Tax Agent reformula:
"Para acceder al detalle específico de tu F29 de octubre,
necesitas el Plan Pro 🎯

Este plan incluye:
• Acceso completo a información del F29
• Histórico de declaraciones
• Detalle de impuestos pagados

Mientras tanto, puedo ayudarte con información general
sobre cómo llenar el F29 o responder dudas conceptuales.
¿Te sirve?"
```

## Mensajes al Usuario

### Principios de Diseño

✅ **Positivo**: "Disponible en Plan Pro" (no "bloqueado")
✅ **Educativo**: Explicar beneficios, no solo restricción
✅ **Alternativas**: Sugerir qué SÍ pueden hacer
✅ **Accionable**: Link claro a página de upgrade
✅ **Empático**: Tono amigable, no frustrante

### Template de Respuesta

```
[Reconocimiento empático] 👥

[Información de limitación positiva] 🎯

Con este plan podrás:
• [beneficio 1]
• [beneficio 2]
• [beneficio 3]

¿Te gustaría conocer más sobre los planes disponibles?
Puedes verlos en Configuración > Suscripción.

[Alternativa si existe]

Mientras tanto, ¿hay algo más en lo que pueda ayudarte? 😊
```

## Testing

### Test Manual

```python
# 1. Crear company con plan básico (sin payroll)
from app.services.subscriptions import SubscriptionService

async with get_db() as db:
    service = SubscriptionService(db)
    subscription = await service.create_subscription(
        company_id=company_id,
        plan_code="basic"
    )

# 2. Verificar acceso a agentes
from app.agents.core import SubscriptionGuard

async with get_db() as db:
    guard = SubscriptionGuard(db)

    # Debería retornar True (básico tiene acceso)
    can_use, msg = await guard.can_use_agent(company_id, "tax_documents")

    # Debería retornar False (básico no tiene payroll)
    can_use, msg = await guard.can_use_agent(company_id, "payroll")
    print(msg)  # Mensaje de error educativo

# 3. Testear en chat
# Enviar consulta de nómina y verificar respuesta del supervisor
```

### Test de Integración

```python
# tests/test_subscription_agents.py

async def test_payroll_agent_blocked_for_basic_plan():
    """Verify payroll agent is blocked for basic plan."""
    # Setup: company with basic plan
    ...

    # Create orchestrator with company_id
    orchestrator = create_multi_agent_orchestrator(
        db=db,
        openai_client=client,
        company_id=company_id
    )

    # Verify payroll agent NOT in agents
    assert "payroll_agent" not in orchestrator.agents
    assert "tax_documents_agent" in orchestrator.agents
```

## Checklist de Implementación

### Backend Core
- [x] Crear `SubscriptionGuard`
- [x] Crear `subscription_responses`
- [x] Crear decorator `@require_subscription_tool`
- [x] Modificar `MultiAgentOrchestrator`
- [x] Actualizar `HandoffsManager`
- [x] Actualizar instrucciones del supervisor

### Configuración
- [ ] Migración SQL para agregar features a planes existentes
- [ ] Seed script para datos de prueba

### Frontend (Opcional)
- [ ] Badge de "Premium" en chat cuando feature bloqueada
- [ ] Modal de upgrade al hacer click en feature bloqueada
- [ ] Tabla comparativa de agentes por plan en /suscripcion

### Testing
- [ ] Tests unitarios de `SubscriptionGuard`
- [ ] Tests de integración de orchestrator
- [ ] Test E2E de flujo de bloqueo completo

---

## Próximos Pasos

1. **Crear migración SQL** para configurar features en planes
2. **Agregar decorator** a herramientas premium (F29, payroll)
3. **Actualizar router ChatKit** para pasar `company_id`
4. **Testing completo** de flujos de bloqueo
5. **Documentar en frontend** cómo mostrar limitaciones

## Soporte

Para dudas o problemas:
- Revisar logs con filtro `🔒` para bloqueos de suscripción
- Verificar `features` JSONB en tabla `subscription_plans`
- Confirmar que `company_id` se pasa correctamente en toda la cadena
