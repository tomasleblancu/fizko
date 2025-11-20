# Sticky Agents - Guía de Logging y Debugging

## 🎯 Overview

Este documento explica cómo usar los logs mejorados de sticky agents para rastrear y debuggear el comportamiento del sistema.

---

## 📋 Tags de Logging

Todos los logs de sticky agents usan el prefijo `[STICKY AGENT]` o `[HANDOFF]` para facilitar el filtrado.

### Símbolos

| Emoji | Significado | Acción |
|-------|-------------|---------|
| 🎯 | Agente activo encontrado | Usando agente especializado (sticky) |
| 👔 | Sin agente activo | Usando supervisor |
| ✅ | Agente guardado | Nuevo tracking o actualización |
| 🧹 | Agente limpiado | Volviendo al supervisor |
| 🔄 | Usando agente activo | Continuando con agente persistente |
| 📍 | Tracking guardado | Handoff completado y guardado |
| 🗑️ | Tracking eliminado | Return-to-supervisor ejecutado |
| ⚪ | Nada que limpiar | Ya estaba en supervisor |
| ⚠️ | Error/Warning | Algo falló |

---

## 🔍 Flujos de Log Típicos

### Flujo 1: Primera Conversación (Handoff)

```log
# Usuario envía: "muestra mis facturas"

👔 [STICKY AGENT] Using supervisor (no active agent) | Thread: abc123def456... | Channel: web
  ↓ Supervisor decide hacer handoff
📄 [HANDOFF] Supervisor → Tax Documents | Reason: User wants tax documents | Thread: abc123def456... | Tools: 12
  ↓ SessionManager guarda
✅ [STICKY AGENT] New: tax_documents_agent | Thread: abc123def456... | Total tracked: 1
📍 [HANDOFF] Tracking tax_documents_agent as active for thread
```

**Interpretación:**
1. Primera llamada → supervisor (no hay agente activo)
2. Supervisor hace handoff a Tax Documents Agent
3. SessionManager guarda `tax_documents_agent` como activo
4. Ahora hay 1 thread con agente activo

---

### Flujo 2: Mensaje Subsecuente (Sticky)

```log
# Usuario envía: "cuántas facturas tengo?"

🎯 [STICKY AGENT] Active: tax_documents_agent | Thread: abc123def456... | Total tracked: 1
  ↓ SessionManager encontró agente activo
🔄 [STICKY AGENT] Using active agent: Tax Documents Expert | Thread: abc123def456... | Channel: web
  ↓ Runner usa el agente activo (NO supervisor)
```

**Interpretación:**
1. SessionManager encuentra `tax_documents_agent` activo
2. Runner usa directamente el Tax Documents Agent
3. **NO pasa por supervisor** → sticky agents funcionando ✅

---

### Flujo 3: Return to Supervisor (Manual)

```log
# Usuario ejecuta comando /supervisor (cuando se implemente)

🧹 [STICKY AGENT] Cleared: tax_documents_agent → supervisor | Thread: abc123def456... | Total tracked: 0
🔄 [HANDOFF] Agent → Supervisor | Reason: User requested | Thread: abc123def456...
🗑️ [HANDOFF] Cleared active agent, back to supervisor
```

**Interpretación:**
1. SessionManager limpia el agente activo
2. Handoff de vuelta al supervisor
3. Total de threads tracked baja a 0

---

### Flujo 4: Return to Supervisor (Automático)

```log
# Agente especializado detecta cambio de tema

🔄 [HANDOFF] Agent → Supervisor | Reason: Topic change detected | Thread: abc123def456...
🧹 [STICKY AGENT] Cleared: tax_documents_agent → supervisor | Thread: abc123def456... | Total tracked: 0
🗑️ [HANDOFF] Cleared active agent, back to supervisor
```

**Interpretación:**
- Solo ocurre si `enabled=True` en `create_return_handoff()`
- Actualmente **deshabilitado** por defecto

---

### Flujo 5: Sin Cambio (Ya en Supervisor)

```log
# Intento de limpiar cuando ya está en supervisor

⚪ [STICKY AGENT] Nothing to clear (already supervisor) | Thread: abc123def456...
```

**Interpretación:**
- Intento de limpiar un thread que ya está en supervisor
- No es un error, solo una operación no-op

---

## 🛠️ Comandos de Filtrado

### Ver solo logs de sticky agents

```bash
# Logs en producción (Railway)
railway logs --filter="STICKY AGENT"

# Logs en desarrollo local
tail -f logs/app.log | grep "STICKY AGENT"

# Ver solo handoffs
tail -f logs/app.log | grep "HANDOFF"
```

### Rastrear un thread específico

```bash
# Reemplaza abc123def456 con tu thread_id
tail -f logs/app.log | grep "abc123def456"
```

### Ver estadísticas

```bash
# Contar threads activos actuales
grep "Total tracked:" logs/app.log | tail -1

# Contar handoffs por tipo
grep "[HANDOFF] Supervisor →" logs/app.log | wc -l  # Handoffs desde supervisor
grep "[HANDOFF] Agent →" logs/app.log | wc -l       # Returns a supervisor
```

---

## 🧪 Cómo Testear Sticky Agents

### Test Manual 1: Verificar Sticky Behavior

1. **Primera conversación** (debe usar supervisor):
   ```
   Usuario: "muestra mis facturas"
   Logs esperados:
   - 👔 [STICKY AGENT] Using supervisor (no active agent)
   - 📄 [HANDOFF] Supervisor → Tax Documents
   - ✅ [STICKY AGENT] New: tax_documents_agent
   ```

2. **Segunda conversación** (debe usar agente activo):
   ```
   Usuario: "cuántas tengo?"
   Logs esperados:
   - 🎯 [STICKY AGENT] Active: tax_documents_agent
   - 🔄 [STICKY AGENT] Using active agent: Tax Documents Expert
   ```

3. **Verificación**:
   - ✅ Si vez "Using active agent" → sticky agents funcionando
   - ❌ Si vez "Using supervisor" → sticky agents NO funcionando

---

### Test Manual 2: Verificar Persistencia Across Restart

1. **Antes de restart:**
   ```bash
   # Enviar mensaje que cause handoff
   curl -X POST /chatkit -d '{"text": "muestra mis facturas"}'

   # Verificar en logs
   grep "New: tax_documents_agent" logs/app.log
   ```

2. **Reiniciar servidor:**
   ```bash
   # Railway
   railway restart

   # Local
   kill $(lsof -ti:8089)
   ./dev.sh
   ```

3. **Después de restart:**
   ```bash
   # Enviar segundo mensaje en mismo thread
   curl -X POST /chatkit -d '{"thread_id": "SAME_ID", "text": "cuántas?"}'

   # Verificar en logs
   grep "Using active agent" logs/app.log  # ✅ Con Redis
   grep "Using supervisor" logs/app.log    # ❌ Sin Redis (estado perdido)
   ```

**Resultado esperado:**
- ❌ **Actualmente:** "Using supervisor" (se perdió en restart)
- ✅ **Con Redis:** "Using active agent" (persistió)

---

### Test Manual 3: Multi-Threading

```bash
# Enviar mensajes a diferentes threads simultáneamente

# Thread 1
curl -X POST /chatkit -d '{"thread_id": "thread-1", "text": "muestra facturas"}' &

# Thread 2
curl -X POST /chatkit -d '{"thread_id": "thread-2", "text": "ayúdame con F29"}' &

# Verificar en logs
grep "Total tracked:" logs/app.log | tail -2

# Debería mostrar:
# Total tracked: 1  (después de thread-1)
# Total tracked: 2  (después de thread-2)
```

---

## 🐛 Troubleshooting

### Problema 1: Sticky Agents No Funcionan

**Síntomas:**
```log
👔 [STICKY AGENT] Using supervisor (no active agent)
👔 [STICKY AGENT] Using supervisor (no active agent)
👔 [STICKY AGENT] Using supervisor (no active agent)
```

**Posibles causas:**
1. ❌ Handoffs nunca se ejecutan (supervisor no transfiere)
2. ❌ SessionManager no guarda correctamente
3. ❌ Thread IDs diferentes entre llamadas

**Debug:**
```bash
# 1. Verificar si hay handoffs
grep "[HANDOFF] Supervisor →" logs/app.log

# 2. Verificar si se guardan agentes
grep "✅ [STICKY AGENT] New:" logs/app.log

# 3. Verificar thread IDs
grep "Thread:" logs/app.log | cut -d' ' -f5 | sort | uniq
```

---

### Problema 2: Se Pierde el Estado

**Síntomas:**
```log
# Antes del restart
🎯 [STICKY AGENT] Active: tax_documents_agent

[SERVER RESTART]

# Después del restart
👔 [STICKY AGENT] Using supervisor (no active agent)
```

**Causa:**
- SessionManager solo usa memoria (sin Redis/DB)

**Solución:**
- Implementar persistencia (ver [STICKY_AGENTS_STATUS.md](./STICKY_AGENTS_STATUS.md#fase-1-persistencia))

---

### Problema 3: Total Tracked Sigue Creciendo

**Síntomas:**
```log
Total tracked: 50
Total tracked: 100
Total tracked: 500
```

**Causa:**
- Memory leak: threads nunca se limpian

**Debug:**
```bash
# Ver threads únicos
grep "Thread:" logs/app.log | cut -d' ' -f5 | sort | uniq | wc -l

# Ver cuántos deberían estar activos (usuarios concurrentes)
```

**Solución:**
- Implementar TTL en SessionManager
- O usar Redis con `ex=86400` (24h auto-cleanup)

---

## 📊 Métricas a Monitorear

### 1. Sticky Agent Hit Rate

```bash
# Total de requests
total=$(grep "\[STICKY AGENT\] Using" logs/app.log | wc -l)

# Requests que usaron sticky agents
sticky=$(grep "🔄 \[STICKY AGENT\] Using active agent" logs/app.log | wc -l)

# Hit rate
echo "scale=2; $sticky * 100 / $total" | bc
# Objetivo: >40% (indica que sticky agents funcionan)
```

### 2. Average Threads Tracked

```bash
grep "Total tracked:" logs/app.log | awk '{print $NF}' | \
  awk '{sum+=$1; count++} END {print sum/count}'

# Objetivo: <100 para un sistema pequeño
```

### 3. Handoff Distribution

```bash
# Por agente
grep "\[HANDOFF\] Supervisor →" logs/app.log | \
  awk -F'→' '{print $2}' | awk '{print $1}' | sort | uniq -c | sort -rn

# Ejemplo output:
#   45 Tax Documents
#   23 Monthly Taxes
#   12 Payroll
#    8 General Knowledge
```

---

## 🎓 Ejemplo Real de Debugging Session

```bash
# Paso 1: Verificar que sticky agents están habilitados
tail -f logs/app.log | grep "STICKY AGENT"

# Paso 2: Enviar mensaje de test
curl -X POST http://localhost:8089/chatkit \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "test-thread-sticky-123",
    "text": "muestra mis facturas de este mes"
  }'

# Logs esperados:
# 👔 [STICKY AGENT] Using supervisor (no active agent) | Thread: test-thread-... | Channel: web
# 📄 [HANDOFF] Supervisor → Tax Documents | Reason: User wants tax documents | Thread: test-thread-... | Tools: 12
# ✅ [STICKY AGENT] New: tax_documents_agent | Thread: test-thread-... | Total tracked: 1

# Paso 3: Enviar segundo mensaje (mismo thread)
curl -X POST http://localhost:8089/chatkit \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "test-thread-sticky-123",
    "text": "cuántas facturas son?"
  }'

# Logs esperados (STICKY):
# 🎯 [STICKY AGENT] Active: tax_documents_agent | Thread: test-thread-... | Total tracked: 1
# 🔄 [STICKY AGENT] Using active agent: Tax Documents Expert | Thread: test-thread-... | Channel: web

# ✅ SI VES ESTOS LOGS → STICKY AGENTS FUNCIONAN!
```

---

## 📚 Referencias

- **Estado actual:** [STICKY_AGENTS_STATUS.md](./STICKY_AGENTS_STATUS.md)
- **Diseño completo:** [STICKY_AGENTS_DESIGN.md](./STICKY_AGENTS_DESIGN.md)
- **Código fuente:**
  - [session_manager.py](../../app/agents/orchestration/session_manager.py)
  - [runner.py](../../app/agents/runner.py)
  - [handoff_factory.py](../../app/agents/orchestration/handoff_factory.py)
