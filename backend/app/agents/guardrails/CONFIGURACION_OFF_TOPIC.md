# Configuración: Bloquear Temas Fuera de Scope

## 🎯 Objetivo

Bloquear preguntas que NO están relacionadas con:
- ✅ Impuestos chilenos (IVA, F29, DTE, etc.)
- ✅ Contabilidad empresarial
- ✅ Remuneraciones y payroll
- ✅ Finanzas de empresas

Bloquear preguntas sobre:
- ❌ Tareas escolares / homework
- ❌ Entretenimiento (películas, juegos, etc.)
- ❌ Matemáticas/ciencias no relacionadas a impuestos
- ❌ Cultura general no empresarial
- ❌ Programación (excepto integración con Fizko)

---

## 🛠️ Implementación

He agregado **dos capas de detección** en [abuse_detection.py](implementations/abuse_detection.py:73-109):

### Capa 1: Prompt Injection (Heurísticas) - Bloqueo Inmediato

Detecta intentos obvios de manipulación y bloquea inmediatamente:
- "ignore previous instructions"
- "disregard your instructions"
- "pretend to be"
- etc.

**Acción**: Bloquea inmediatamente sin consultar AI (es obvio y grave)

### Capa 2: Keywords Off-Topic (Bloqueo Rápido)

Detecta keywords sospechosas y **BLOQUEA INMEDIATAMENTE** (sin consultar AI):

```python
off_topic_keywords = [
    # Homework/Academic (incluye plurales)
    ("tarea", "tareas", "homework", "exam", "examen", "exámenes", "test", "prueba", "pruebas"),

    # Math/Science (incluye plurales y variaciones sin tilde)
    ("ecuación", "ecuaciones", "equation", "equations", "álgebra", "algebra", "matemática", "matemáticas", "mathematics"),

    # Entertainment (incluye plurales)
    ("película", "películas", "movie", "movies", "serie", "series", "juego", "juegos", "game", "games", "videojuego", "videojuegos"),

    # Creative writing (incluye plurales)
    ("poema", "poemas", "poem", "poems", "cuento", "cuentos", "story", "stories", "novela", "novelas", "novel", "novels"),

    # Programming (incluye variaciones sin tilde y más keywords)
    ("código python", "codigo python", "código java", "codigo java", "python code", "java code", "javascript", "programar", "programación", "programacion", "programming"),

    # General knowledge (incluye variaciones sin tilde)
    ("capital de", "capital of", "quién fue", "quien fue", "who was", "quiénes fueron", "who were"),

    # Recipes/Cooking (nueva categoría)
    ("receta", "recetas", "recipe", "recipes", "cocinar", "cocina", "cooking", "cook", "preparar comida", "ingredientes", "ingredients"),
]
```

**Nota importante:** Los keywords incluyen variaciones con/sin tilde y singular/plural porque Python hace matching exacto de caracteres.

**Lógica:**
- Si encuentra 1+ keywords → **BLOQUEA INMEDIATAMENTE** (sin llamar AI)
- Si encuentra 0 keywords → Pasa a Capa 3 (AI check)

**Ventajas:**
- ⚡ Ultra rápido (< 1ms) - no gasta tiempo ni dinero en AI
- 💰 Gratis (no usa API)
- 🎯 Bloquea casos obvios instantáneamente

**Desventajas:**
- ⚠️ Necesita mantenimiento manual de keywords
- ⚠️ Solo detecta lo que está en la lista

### Capa 3: AI-based Detection (~200ms) - **FALLBACK para casos sin keywords**

Usa gpt-4.1-nano para clasificar si el request es apropiado.

**⚠️ OPTIMIZACIÓN**: Esta capa solo se ejecuta si **NO** se detectaron keywords. Si hay keywords, bloqueamos inmediatamente sin gastar en API.

```python
USE_AI_CHECK = True  # ⚠️ Adds ~200ms latency

# Load instructions from file
# __file__ is in: app/agents/guardrails/implementations/abuse_detection.py
# Need to go up to: app/agents/instructions/guardrails/ABUSE_DETECTION_AI_CHECK.md
instructions_path = Path(__file__).parent.parent.parent / "instructions" / "guardrails" / "ABUSE_DETECTION_AI_CHECK.md"
with open(instructions_path, "r", encoding="utf-8") as f:
    instructions = f.read()

abuse_check_agent = Agent(
    name="Abuse Detection",
    instructions=instructions,  # Loaded from ABUSE_DETECTION_AI_CHECK.md
    model="gpt-4.1-nano",  # Fast and cheap model
    output_type=AbuseCheckOutput,
)
```

**Instrucciones:** [app/agents/instructions/guardrails/ABUSE_DETECTION_AI_CHECK.md](../instructions/guardrails/ABUSE_DETECTION_AI_CHECK.md)

**Ventaja de usar archivo externo:**
- ✏️ Fácil de actualizar sin tocar código
- 📝 Se adapta automáticamente a nuevos agentes/features
- 🔍 Más fácil de revisar y mejorar

**Ventajas:**
- 🎯 Mucho más preciso que keywords
- 🧠 Entiende contexto y matices
- ✅ Detecta casos edge sin keywords obvios
- 🔄 Se adapta automáticamente a nuevos casos

**Desventajas:**
- ⏱️ Añade ~200ms de latencia (solo cuando NO hay keywords)
- 💰 Cuesta dinero (gpt-4.1-nano: ~$0.30 por millón de tokens, pero solo se usa cuando keywords no detectan nada)

---

## 📊 Recomendaciones

### Configuración Actual (Optimizada para Producción)

**Estrategia híbrida con 3 capas:**

1. **Prompt injection** → Bloqueo inmediato (< 1ms)
2. **Keywords detectados** → Bloqueo inmediato (< 1ms, sin gastar en API)
3. **Sin keywords** → AI check (200ms + costo API)

**Por qué esta es la mejor estrategia:**
1. ✅ **Rápido**: Mayoría de casos off-topic se bloquean en < 1ms con keywords
2. ✅ **Barato**: AI solo se usa cuando keywords no detectan nada (< 10% de casos)
3. ✅ **Completo**: AI detecta casos edge sin keywords obvios
4. ✅ **Balanceado**: Lo mejor de heurísticas + AI

**Monitorear logs:**
```bash
# Ver keywords detectados (bloqueos rápidos)
grep "🚨 Abuse detection: Off-topic request detected" logs/backend.log

# Ver decisiones del AI (casos sin keywords)
grep "🚨 Abuse detection (AI)" logs/backend.log
```

**Métricas importantes:**
- 📊 % de bloqueos por keywords vs AI (objetivo: 90% keywords, 10% AI)
- ⏱️ Latencia promedio de guardrail (objetivo: < 50ms promedio)
- 💰 Costo API por mes (objetivo: < $5 con la optimización actual)

---

## ✏️ Cómo Agregar Más Keywords (Recomendado)

**💡 ESTRATEGIA**: Agregar keywords para los casos **MÁS COMUNES** de off-topic. El AI se encarga del resto.

Edita [abuse_detection.py](implementations/abuse_detection.py:75-90):

```python
off_topic_keywords = [
    # Existing groups...

    # ⭐ NUEVO: Agregar tu categoría
    ("keyword1", "keyword2", "keyword3"),
]
```

**Cuándo agregar keywords:**
- ✅ Detectas un patrón off-topic que aparece frecuentemente en logs
- ✅ Quieres bloquear instantáneamente sin gastar en AI
- ✅ El keyword es muy obvio (ej: "receta", "película")

**Cuándo NO agregar keywords:**
- ❌ Casos muy raros o edge cases (el AI los detecta)
- ❌ Keywords demasiado generales que causan false positives
- ❌ Intentar cubrir todas las variaciones posibles (usa AI para eso)

**Ejemplos buenos para agregar:**
```python
# Sports (común en plataformas)
("fútbol", "futbol", "soccer", "basketball", "deporte", "deportes", "partido", "partidos"),

# Health (común)
("enfermedad", "enferm", "disease", "medicina", "medicine", "síntoma", "sintoma"),
```

---

## 🧪 Testing

### Test Manual

```bash
cd backend
.venv/bin/python
```

```python
# Test off-topic detection
from app.agents.guardrails.implementations import abuse_detection_guardrail
from agents import Agent, RunContextWrapper

ctx = RunContextWrapper(context={})
agent = Agent(name="Test", instructions="Test")

# Should BLOCK (2 keywords: "tarea" + "matemática")
result = await abuse_detection_guardrail(
    ctx, agent,
    "Ayúdame con mi tarea de matemáticas"
)
print(result.tripwire_triggered)  # True

# Should PASS (tax-related)
result = await abuse_detection_guardrail(
    ctx, agent,
    "¿Cómo calculo el IVA?"
)
print(result.tripwire_triggered)  # False
```

### Test en Staging

1. Deploy a staging
2. Probar casos:
   - ✅ "¿Cuándo vence el F29?" → PASA
   - ❌ "Ayúdame con mi tarea de matemáticas" → BLOQUEA
   - ❌ "Recomiéndame una película" → BLOQUEA
   - ✅ "¿Cómo registro un gasto?" → PASA

---

## 📈 Monitoreo en Producción

### Logs a Revisar

```bash
# Ver requests bloqueados
grep "🚨 Abuse detection: Off-topic" logs/backend.log

# Ver todas las detecciones
grep "🚨 Abuse detection" logs/backend.log

# Contar detecciones por tipo
grep "🚨 Abuse detection" logs/backend.log | cut -d: -f5 | sort | uniq -c
```

### Métricas Importantes

1. **Off-topic Block Rate**: % de requests bloqueados por ser off-topic
   - Target: 2-5% (si es más, ajustar keywords)

2. **False Positive Rate**: % de requests legítimos bloqueados
   - Target: < 1%
   - Calcular revisando logs manualmente

3. **Latency Impact**:
   - Solo heurísticas: < 1ms (negligible)
   - Con AI check: ~200ms (noticeable pero aceptable)

---

## ⚙️ Configuración Avanzada

### Ajustar Sensibilidad

```python
# MUY estricto (menos false negatives, más false positives) - ACTUAL
if len(off_topic_matches) >= 1:  # Bloquea con 1 keyword ⭐ CONFIGURACIÓN ACTUAL
    tripwire_triggered=True

# Más permisivo (menos false positives, más false negatives)
if len(off_topic_matches) >= 3:  # Requiere 3 keywords
    tripwire_triggered=True

# Balanced (anterior default)
if len(off_topic_matches) >= 2:  # Requiere 2 keywords
    tripwire_triggered=True
```

### Solo AI Check (Sin Heurísticas)

Si prefieres solo AI y no heurísticas:

```python
# Comentar todo el bloque de heurísticas
# off_topic_keywords = [...]

# Habilitar AI check
USE_AI_CHECK = True
```

**Pros**: Más preciso, menos false positives
**Cons**: Más lento, más caro

---

## 🚨 Troubleshooting

### Problema: Muchos False Positives

**Síntoma**: Requests legítimos siendo bloqueados

**Solución**:
1. Revisar qué keywords están disparando:
   ```bash
   grep "Off-topic request detected" logs/backend.log
   ```

2. Opciones:
   - Remover keywords problemáticos
   - Aumentar umbral (1 → 2 o 3 matches)
   - Confiar más en AI check (las heurísticas solo son primera línea)

### Problema: Requests Off-Topic No Bloqueados

**Síntoma**: Usuarios hacen preguntas fuera de scope y pasan

**Solución**:
1. Identificar keywords comunes en esos requests
2. Agregar esos keywords a `off_topic_keywords`
3. O habilitar `USE_AI_CHECK = True`

### Problema: Latencia Alta

**Síntoma**: Requests tardan mucho (> 500ms)

**Solución**:
- Deshabilitar AI check: `USE_AI_CHECK = False`
- Usar solo heurísticas

---

## 📝 Ejemplos de Configuración

### Configuración Estricta (Bloquea más)

```python
# Requiere solo 1 keyword
if len(off_topic_matches) >= 1:
    tripwire_triggered=True

# + AI check habilitado
USE_AI_CHECK = True
```

**Uso**: Plataformas con alto riesgo de abuso

### Configuración Permisiva (Bloquea menos)

```python
# Requiere 3 keywords
if len(off_topic_matches) >= 3:
    tripwire_triggered=True

# Sin AI check
USE_AI_CHECK = False
```

**Uso**: Fase de testing, evitar false positives

### Configuración Balanced (Anterior Default)

```python
# Requiere 2 keywords
if len(off_topic_matches) >= 2:
    tripwire_triggered=True

# AI check opcional
USE_AI_CHECK = True  # Para casos ambiguos
```

**Uso**: Producción después de validación inicial

---

## ✅ Estado Actual

- ✅ **Heurísticas**: Implementadas y activas
- ✅ **AI check**: Habilitado
- ✅ **Keywords**: 6 categorías configuradas
- ✅ **Umbral**: **1 match** para bloquear (ajustado después de testing en producción)

**Próximos pasos recomendados:**

1. Deploy a staging
2. Monitorear por 1 semana
3. Ajustar keywords según datos
4. Deploy a producción

---

**Actualizado**: 2025-01-11
**Archivo**: [abuse_detection.py](implementations/abuse_detection.py)
