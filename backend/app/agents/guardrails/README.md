# Guardrails System

Sistema de guardrails para validación de entrada y salida de agentes en Fizko.

## ¿Qué son los Guardrails?

Los guardrails son funciones que se ejecutan **en paralelo** a tus agentes para realizar validaciones:

- **Input guardrails**: Validan el input del usuario **antes** de ejecutar el agente
- **Output guardrails**: Validan la salida del agente **antes** de devolverla al usuario

Si un guardrail detecta un problema, puede activar un "tripwire" que detiene la ejecución inmediatamente.

### Ventajas

1. **Performance**: Usa modelos rápidos/baratos para validaciones antes de modelos caros
2. **Seguridad**: Detecta uso malicioso, prompt injection, PII
3. **Compliance**: Valida límites de suscripción, políticas de uso
4. **Costo**: Ahorra dinero bloqueando requests abusivos antes de ejecutar modelos caros

## Arquitectura

```
Usuario → Input Guardrails → Agente → Output Guardrails → Usuario
              ↓                           ↓
         ❌ Bloquea si                ❌ Bloquea si
         tripwire=True               tripwire=True
```

### Componentes

```
backend/app/agents/guardrails/
├── core.py                  # Tipos base y excepciones
├── decorators.py            # @input_guardrail, @output_guardrail
├── runner.py                # Ejecuta guardrails en paralelo
├── registry.py              # Registro centralizado
└── implementations/         # Guardrails concretos
    ├── abuse_detection.py   # Detecta uso malicioso
    ├── pii_detection.py     # Detecta PII en output
    └── subscription_check.py # Valida límites de plan
```

## Uso Básico

### 1. Crear un Guardrail

```python
from agents import Agent, RunContextWrapper
from app.agents.guardrails import input_guardrail, GuardrailFunctionOutput

@input_guardrail
async def my_custom_guardrail(
    ctx: RunContextWrapper,
    agent: Agent,
    input: str | list
) -> GuardrailFunctionOutput:
    """Descripción del guardrail."""

    # Tu lógica de validación
    if "palabra_prohibida" in str(input).lower():
        return GuardrailFunctionOutput(
            output_info={"reason": "Contenido prohibido detectado"},
            tripwire_triggered=True  # ⚠️ Esto bloquea la ejecución
        )

    # Todo OK
    return GuardrailFunctionOutput(
        output_info={"status": "ok"},
        tripwire_triggered=False
    )
```

### 2. Agregar Guardrail a un Agente

El SDK de OpenAI ya soporta guardrails nativamente:

```python
from agents import Agent

agent = Agent(
    name="Tax Assistant",
    instructions="...",
    input_guardrails=[my_custom_guardrail],  # ⚠️ Antes de ejecutar
    output_guardrails=[pii_detection],       # ⚠️ Después de ejecutar
)
```

### 3. El Runner se Encarga del Resto

El `Runner.run()` automáticamente ejecuta los guardrails y lanza excepciones si se activa un tripwire:

```python
from agents import Runner

try:
    result = await Runner.run(agent, user_input, context=context)
    # Todos los guardrails pasaron ✅
except InputGuardrailTripwireTriggered as e:
    # Input bloqueado por guardrail ❌
    print(f"Input bloqueado: {e.result.output.output_info}")
except OutputGuardrailTripwireTriggered as e:
    # Output bloqueado por guardrail ❌
    print(f"Output bloqueado: {e.result.output.output_info}")
```

## Guardrails Implementados

### 1. Abuse Detection (Input)

**Propósito**: Detecta uso malicioso o fuera de scope

**Ubicación**: `implementations/abuse_detection.py`

**Detecta**:
- Prompt injection ("ignore previous instructions")
- Requests fuera de tema (matemáticas, tareas escolares, programación, entretenimiento)
- Intentos de manipular el modelo

**Uso**:
```python
from app.agents.guardrails.implementations import abuse_detection_guardrail

agent.input_guardrails = [abuse_detection_guardrail]
```

**Configuración**:
- `USE_AI_CHECK = False`: Solo heurísticas rápidas
- `USE_AI_CHECK = True`: Usa gpt-4.1-nano para clasificación (más preciso pero más lento)

**Mensajes Personalizados**: Cuando el guardrail bloquea una request, retorna mensajes personalizados según el tipo de bloqueo:
- **Prompt injection**: Mensaje directo explicando que se detectó manipulación
- **Off-topic**: Mensaje amigable redirigiendo a temas válidos
- Ver [CUSTOM_MESSAGES.md](CUSTOM_MESSAGES.md) para detalles completos

**Documentación Adicional**:
- [CONFIGURACION_OFF_TOPIC.md](CONFIGURACION_OFF_TOPIC.md) - Configuración de detección off-topic
- [CUSTOM_MESSAGES.md](CUSTOM_MESSAGES.md) - Mensajes personalizados por tipo de bloqueo
- [instructions/guardrails/ABUSE_DETECTION_AI_CHECK.md](instructions/guardrails/ABUSE_DETECTION_AI_CHECK.md) - Instrucciones AI

### 2. PII Detection (Output)

**Propósito**: Previene leakage de información sensible

**Ubicación**: `implementations/pii_detection.py`

**Detecta**:
- RUT (Chilean national ID)
- Emails
- Teléfonos chilenos
- Tarjetas de crédito
- API keys

**Uso**:
```python
from app.agents.guardrails.implementations import pii_output_guardrail

agent.output_guardrails = [pii_output_guardrail]
```

**Comportamiento actual**: Solo logea, no bloquea (cambiar `tripwire_triggered=True` para bloquear)

### 3. Subscription Limit (Input)

**Propósito**: Valida límites de suscripción antes de ejecutar operaciones caras

**Ubicación**: `implementations/subscription_check.py`

**Valida**:
- Número de queries mensuales
- Acceso a features premium
- Documentos procesados

**Uso**:
```python
from app.agents.guardrails.implementations import subscription_limit_guardrail

agent.input_guardrails = [subscription_limit_guardrail]
```

**Estado**: Placeholder (implementar lógica real en producción)

## Integración con Fizko

### Opción A: Agregar a Agentes Especializados

Edita las funciones `create_*_agent()` en [backend/app/agents/specialized/](../specialized/):

```python
# En backend/app/agents/specialized/supervisor_agent.py

from app.agents.guardrails.implementations import (
    abuse_detection_guardrail,
    pii_output_guardrail,
)

def create_supervisor_agent(...):
    agent = Agent(
        name="Supervisor",
        instructions=INSTRUCTIONS,
        tools=tools,
        handoffs=handoffs,
        # ⭐ Agregar guardrails aquí
        input_guardrails=[abuse_detection_guardrail],
        output_guardrails=[pii_output_guardrail],
    )
    return agent
```

### Opción B: Configuración Centralizada

Crea un archivo de configuración `guardrails_config.py`:

```python
# backend/app/agents/guardrails/config.py

from app.agents.guardrails.implementations import (
    abuse_detection_guardrail,
    pii_output_guardrail,
    subscription_limit_guardrail,
)

# Configuración por agente
GUARDRAIL_CONFIG = {
    "supervisor_agent": {
        "input": [abuse_detection_guardrail, subscription_limit_guardrail],
        "output": [pii_output_guardrail],
    },
    "tax_documents_agent": {
        "input": [],
        "output": [pii_output_guardrail],
    },
    "payroll_agent": {
        "input": [abuse_detection_guardrail],
        "output": [pii_output_guardrail],
    },
    # ... otros agentes
}

def get_guardrails_for_agent(agent_name: str):
    """Get guardrails for a specific agent."""
    return GUARDRAIL_CONFIG.get(agent_name, {"input": [], "output": []})
```

Luego en `multi_agent_orchestrator.py`:

```python
from app.agents.guardrails.config import get_guardrails_for_agent

def _initialize_agents(self):
    # Supervisor
    guardrails = get_guardrails_for_agent("supervisor_agent")
    self.agents["supervisor_agent"] = create_supervisor_agent(...)
    self.agents["supervisor_agent"].input_guardrails = guardrails["input"]
    self.agents["supervisor_agent"].output_guardrails = guardrails["output"]

    # ... repeat for other agents
```

## Crear Guardrails Personalizados

### Template para Input Guardrail

```python
from agents import Agent, RunContextWrapper
from app.agents.guardrails import input_guardrail, GuardrailFunctionOutput

@input_guardrail
async def my_input_guardrail(
    ctx: RunContextWrapper,
    agent: Agent,
    input: str | list[dict]
) -> GuardrailFunctionOutput:
    """
    Brief description of what this guardrail checks.

    This runs BEFORE agent execution.
    """
    # Extract text from input
    if isinstance(input, str):
        text = input
    else:
        # Handle message format
        text = extract_text_from_messages(input)

    # Your validation logic here
    is_valid = validate_input(text)

    if not is_valid:
        return GuardrailFunctionOutput(
            output_info={"reason": "Validation failed", "details": "..."},
            tripwire_triggered=True  # Block execution
        )

    return GuardrailFunctionOutput(
        output_info={"status": "ok"},
        tripwire_triggered=False
    )
```

### Template para Output Guardrail

```python
from agents import Agent, RunContextWrapper
from app.agents.guardrails import output_guardrail, GuardrailFunctionOutput

@output_guardrail
async def my_output_guardrail(
    ctx: RunContextWrapper,
    agent: Agent,
    output: Any
) -> GuardrailFunctionOutput:
    """
    Brief description of what this guardrail checks.

    This runs AFTER agent execution, before returning to user.
    """
    # Extract text from output
    output_text = str(output)

    # Your validation logic here
    is_safe = validate_output(output_text)

    if not is_safe:
        return GuardrailFunctionOutput(
            output_info={"reason": "Unsafe output", "details": "..."},
            tripwire_triggered=True  # Block output
        )

    return GuardrailFunctionOutput(
        output_info={"status": "ok"},
        tripwire_triggered=False
    )
```

### Guardrail con AI Model

Para validaciones complejas, puedes usar un agente interno:

```python
from agents import Agent, Runner
from pydantic import BaseModel

class ValidationOutput(BaseModel):
    is_valid: bool
    reason: str
    confidence: float

@input_guardrail
async def ai_validation_guardrail(
    ctx: RunContextWrapper,
    agent: Agent,
    input: str | list
) -> GuardrailFunctionOutput:
    """Use an AI model for complex validation."""

    # Create lightweight validation agent
    validation_agent = Agent(
        name="Validator",
        instructions="Check if the input is appropriate for a tax platform.",
        model="gpt-4o-mini",  # Fast and cheap
        output_type=ValidationOutput,
    )

    # Run validation
    result = await Runner.run(
        validation_agent,
        str(input),
        context=ctx.context,
    )

    validation: ValidationOutput = result.final_output

    return GuardrailFunctionOutput(
        output_info={
            "reason": validation.reason,
            "confidence": validation.confidence,
        },
        tripwire_triggered=not validation.is_valid,
    )
```

## Best Practices

### 1. Usar Modelos Rápidos
Para guardrails de input, usa modelos rápidos/baratos (gpt-4o-mini, gpt-3.5-turbo) ya que el objetivo es **ahorrar tiempo/dinero** bloqueando requests antes de ejecutar modelos caros.

### 2. Heurísticas Primero
Implementa checks heurísticos rápidos (regex, keywords) antes de recurrir a AI:

```python
# ✅ Fast path (heuristics)
if "banned_keyword" in text:
    return GuardrailFunctionOutput(..., tripwire_triggered=True)

# ⏱️ Slow path (AI) - solo si es necesario
if ENABLE_AI_CHECK:
    result = await Runner.run(validation_agent, text)
```

### 3. Logging Exhaustivo
Logea todos los tripwires para análisis posterior:

```python
if result.tripwire_triggered:
    logger.warning(
        f"🚨 Guardrail triggered | "
        f"Name: {guardrail_name} | "
        f"Company: {company_id} | "
        f"Reason: {result.output_info}"
    )
```

### 4. Fail Open (Don't Block on Errors)
Si un guardrail falla con excepción, no bloquees la request:

```python
try:
    result = await validation_check()
except Exception as e:
    logger.error(f"Guardrail failed: {e}")
    # ⚠️ Don't block - allow request through
    return GuardrailFunctionOutput(
        output_info={"status": "guardrail_error"},
        tripwire_triggered=False
    )
```

### 5. A/B Testing
Usa el registry para habilitar/deshabilitar guardrails por empresa:

```python
from app.agents.guardrails.registry import guardrail_registry

# Check if guardrail is enabled for this company
if guardrail_registry.is_enabled("abuse_detection", company_id):
    agent.input_guardrails.append(abuse_detection_guardrail)
```

## Monitoring & Observability

### Métricas Importantes

1. **Tripwire Rate**: % de requests bloqueados
2. **Guardrail Latency**: Tiempo de ejecución de cada guardrail
3. **False Positives**: Requests bloqueados incorrectamente
4. **Cost Savings**: Dinero ahorrado bloqueando requests abusivos

### Logs

Los guardrails logean automáticamente:
- ✅ Ejecuciones exitosas (DEBUG level)
- 🚨 Tripwires activados (WARNING level)
- ❌ Errores (ERROR level)

Busca en logs:
```bash
grep "🛡️  Running.*guardrails" backend.log  # Ejecuciones
grep "🚨.*tripwire triggered" backend.log    # Bloqueados
```

## Roadmap

### V1 (Actual)
- ✅ Core infrastructure
- ✅ Abuse detection (heuristics)
- ✅ PII detection (regex)
- ✅ Subscription placeholder

### V2 (Próximo)
- [ ] Integración completa con SubscriptionGuard
- [ ] Configuración per-company en DB
- [ ] Dashboard de guardrails en admin
- [ ] Métricas y analytics

### V3 (Futuro)
- [ ] ML-based abuse detection
- [ ] Advanced PII detection (NER models)
- [ ] Rate limiting por IP/usuario
- [ ] A/B testing framework

## Referencias

- [OpenAI Agents SDK - Guardrails](https://github.com/openai/agents-sdk)
- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [Prompt Injection Defenses](https://simonwillison.net/2023/Apr/14/worst-that-can-happen/)

## Preguntas Frecuentes

### ¿Cuándo usar input vs output guardrails?

- **Input**: Validar **antes** de ejecutar (para ahorrar costo/tiempo)
- **Output**: Validar **después** de ejecutar (para seguridad/compliance)

### ¿Puedo tener múltiples guardrails?

Sí, puedes tener múltiples guardrails de cada tipo. Se ejecutan **en paralelo**:

```python
agent.input_guardrails = [
    abuse_detection_guardrail,
    subscription_limit_guardrail,
    custom_guardrail_1,
    custom_guardrail_2,
]
```

### ¿Qué pasa si un guardrail falla?

Por defecto, los errores se logean pero no bloquean. Implementa `try/except` en tu guardrail para control fino.

### ¿Los guardrails afectan latencia?

Mínimamente. Se ejecutan en paralelo y usan modelos rápidos. Típicamente añaden 50-200ms.

### ¿Cómo testear guardrails?

```python
import pytest
from app.agents.guardrails.implementations import abuse_detection_guardrail

@pytest.mark.asyncio
async def test_abuse_detection():
    # Mock context and agent
    ctx = mock_context()
    agent = mock_agent()

    # Test malicious input
    result = await abuse_detection_guardrail(ctx, agent, "ignore previous instructions")
    assert result.tripwire_triggered == True

    # Test normal input
    result = await abuse_detection_guardrail(ctx, agent, "¿Cuándo vence el F29?")
    assert result.tripwire_triggered == False
```
