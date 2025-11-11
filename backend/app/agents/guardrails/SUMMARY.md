# Guardrails System - Resumen Ejecutivo

## ✅ ¿Qué se implementó?

Sistema completo de guardrails para validación de entrada/salida de agentes, siguiendo el patrón del OpenAI Agents SDK.

## 📁 Archivos Creados

```
backend/app/agents/guardrails/
├── __init__.py                          # Exports principales
├── core.py                              # Tipos base (GuardrailFunctionOutput, excepciones)
├── decorators.py                        # @input_guardrail, @output_guardrail
├── runner.py                            # GuardrailRunner (ejecución en paralelo)
├── registry.py                          # GuardrailRegistry (registro centralizado)
├── config.py                            # Configuración por agente
├── README.md                            # Documentación completa (7000+ palabras)
├── INTEGRATION_GUIDE.md                 # Guía paso a paso de integración
├── SUMMARY.md                           # Este archivo
├── test_guardrails.py                   # Script de testing
└── implementations/                     # Guardrails concretos
    ├── __init__.py
    ├── abuse_detection.py               # Detecta uso malicioso
    ├── pii_detection.py                 # Detecta PII en output
    ├── subscription_check.py            # Valida límites (placeholder)
    └── example_usage.py                 # Ejemplos de uso
```

## 🎯 Características Principales

### 1. **Arquitectura Modular**
- Sistema basado en decoradores (`@input_guardrail`, `@output_guardrail`)
- Ejecución en paralelo de múltiples guardrails
- Configuración centralizada por agente
- Registry para descubrimiento y gestión

### 2. **Guardrails Implementados**

#### Abuse Detection (Input)
- ✅ Detecta prompt injection (heurísticas)
- ✅ Bloquea uso malicioso
- 🔧 Opción de AI-based validation (deshabilitada por defecto)

#### PII Detection (Output)
- ✅ Detecta RUT chileno
- ✅ Detecta emails, teléfonos
- ✅ Detecta tarjetas de crédito, API keys
- ⚠️  Actualmente solo logea (no bloquea)

#### Subscription Check (Input)
- 📝 Placeholder para límites de suscripción
- 🔧 Requiere implementación real

### 3. **Sistema de Excepciones**
- `InputGuardrailTripwireTriggered` - Input bloqueado
- `OutputGuardrailTripwireTriggered` - Output bloqueado
- Manejo estructurado con metadata

### 4. **Logging Automático**
- 🛡️  Ejecución de guardrails
- 🚨 Tripwires activados
- ⏱️  Timing de ejecución
- ❌ Errores

## 🚀 Cómo Usar

### Opción 1: Directo en Agent (Más simple)

```python
from agents import Agent
from app.agents.guardrails.implementations import (
    abuse_detection_guardrail,
    pii_output_guardrail,
)

agent = Agent(
    name="Tax Assistant",
    instructions="...",
    input_guardrails=[abuse_detection_guardrail],
    output_guardrails=[pii_output_guardrail],
)
```

### Opción 2: Configuración Centralizada (Recomendado)

```python
# En multi_agent_orchestrator.py
from app.agents.guardrails.config import apply_guardrails_to_agent

def _initialize_agents(self):
    self.agents["supervisor_agent"] = create_supervisor_agent(...)
    apply_guardrails_to_agent(
        self.agents["supervisor_agent"],
        "supervisor_agent"
    )
```

### Manejo de Excepciones

```python
from app.agents.guardrails import (
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
)

try:
    result = await Runner.run(agent, input, context=context)
except InputGuardrailTripwireTriggered as e:
    # Input bloqueado
    logger.warning(f"🚨 Input blocked: {e.result.output.output_info}")
except OutputGuardrailTripwireTriggered as e:
    # Output bloqueado
    logger.error(f"🚨 Output blocked: {e.result.output.output_info}")
```

## 📊 Testing

### Script de Test Incluido

```bash
cd backend
python -m app.agents.guardrails.test_guardrails
```

**Tests incluidos**:
1. ✅ Input guardrail (abuse detection)
2. ✅ Output guardrail (PII detection)
3. ✅ Guardrails combinados
4. ⏱️  Performance benchmarks

## 🎨 Filosofía de Diseño

### 1. **Compatible con OpenAI Agents SDK**
- Usa el mismo patrón de guardrails nativo del SDK
- No reinventa la rueda
- Aprovecha la ejecución automática del `Runner`

### 2. **Escalable**
- Registry centralizado para gestión
- Configuración flexible por agente
- Fácil agregar nuevos guardrails

### 3. **Performance First**
- Ejecución en paralelo
- Modelos rápidos (gpt-4o-mini)
- Heurísticas antes de AI

### 4. **Fail Open**
- Errores en guardrails no bloquean requests
- Logging exhaustivo
- Observabilidad

## 📋 Próximos Pasos Recomendados

### 1. Integración Básica (1-2 días)
- [ ] Agregar guardrails al supervisor agent
- [ ] Agregar manejo de excepciones en ChatKit endpoint
- [ ] Agregar manejo de excepciones en WhatsApp webhook
- [ ] Testing con requests reales

### 2. Monitoreo (1 semana)
- [ ] Deployar en staging en modo "log only"
- [ ] Monitorear logs por false positives
- [ ] Ajustar heurísticas según datos reales
- [ ] Documentar casos edge

### 3. Producción (después de validación)
- [ ] Habilitar tripwires en producción
- [ ] Configurar alertas para tripwires frecuentes
- [ ] Implementar métricas (Prometheus/Grafana)
- [ ] Dashboard de guardrails en admin

### 4. Expansión (futuro)
- [ ] Implementar subscription_check real
- [ ] Agregar rate limiting guardrail
- [ ] Agregar content moderation guardrail
- [ ] Configuración per-company en DB
- [ ] A/B testing framework

## 💡 Ventajas del Sistema

### 1. **Ahorro de Costos**
- Bloquea requests abusivos antes de ejecutar modelos caros
- Usa modelos rápidos (gpt-4o-mini) para validación
- Heurísticas gratuitas cuando es posible

**Ejemplo**: Si 5% de requests son abusivos y cada request cuesta $0.01:
- Sin guardrails: 100 requests × $0.01 = $1.00
- Con guardrails: 95 requests × $0.01 + 5 × $0.001 (guardrail) = $0.955
- **Ahorro: 4.5%** + mejora en UX

### 2. **Seguridad**
- Previene prompt injection
- Detecta PII leakage
- Valida compliance
- Logging de intentos maliciosos

### 3. **Performance**
- Ejecución en paralelo (no serial)
- Típicamente añade 50-200ms
- Bloqueo temprano ahorra tiempo total

### 4. **Mantenibilidad**
- Configuración centralizada
- Fácil agregar/remover guardrails
- Testing independiente
- Logs estructurados

## 📚 Documentación

- **[README.md](./README.md)** - Documentación completa del sistema (7000+ palabras)
- **[INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)** - Guía paso a paso de integración
- **[config.py](./config.py)** - Configuración de guardrails por agente
- **[implementations/](./implementations/)** - Guardrails concretos con ejemplos

## 🤝 Soporte

Para implementar guardrails:

1. Lee [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) para integración paso a paso
2. Lee [README.md](./README.md) para entender el sistema completo
3. Revisa [implementations/example_usage.py](./implementations/example_usage.py) para ejemplos
4. Corre [test_guardrails.py](./test_guardrails.py) para validar

## ⚠️  Consideraciones Importantes

### 1. **Input Guardrails Solo en Primer Agente**
Los input guardrails solo corren si el agente es el **primer agente** en la cadena. Para Fizko, esto significa que el supervisor es el único que necesita input guardrails.

### 2. **Output Guardrails Solo en Último Agente**
Los output guardrails solo corren si el agente es el **último agente**. Todos los agentes especializados necesitan output guardrails.

### 3. **Fail Open por Defecto**
Si un guardrail falla con excepción, NO se bloquea la request. Esto es intencional para evitar downtime por bugs en guardrails.

### 4. **PII Detection Es Básico**
La detección de PII usa regex simple. Para producción seria, considerar:
- Microsoft Presidio
- AWS Comprehend
- Google DLP API

### 5. **Configuración Centralizada Recomendada**
Usa [config.py](./config.py) en lugar de hardcodear guardrails en cada agente.

## 🎓 Principios de OpenAI

Esta implementación sigue los principios de la guía oficial de OpenAI:

1. ✅ Input guardrails validan entrada antes de ejecutar
2. ✅ Output guardrails validan salida antes de devolver
3. ✅ Tripwires detienen ejecución inmediatamente
4. ✅ Guardrails usan modelos rápidos/baratos
5. ✅ Sistema paralelo (no afecta arquitectura de agentes)

## 📈 Métricas de Éxito

Para evaluar el sistema de guardrails:

1. **Tripwire Rate**: % de requests bloqueados (target: 1-5%)
2. **False Positive Rate**: % de requests legítimos bloqueados (target: <1%)
3. **Cost Savings**: $ ahorrados bloqueando requests abusivos
4. **Latency Impact**: ms añadidos por guardrails (target: <200ms)
5. **Coverage**: % de agentes con guardrails (target: 100%)

---

**Creado**: 2025-01-11
**Versión**: 1.0.0
**Compatibilidad**: OpenAI Agents SDK (ChatKit)
