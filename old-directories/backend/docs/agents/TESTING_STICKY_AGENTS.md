# Testing Sticky Agents - Guía Práctica

## 🎯 Objetivo

Esta guía te muestra cómo verificar que los sticky agents están funcionando correctamente en tu entorno local o producción.

---

## 🚀 Quick Start

### Opción 1: Script Automatizado (Recomendado)

```bash
# Desde el directorio backend/
./scripts/test_sticky_agents.sh

# O contra producción
./scripts/test_sticky_agents.sh https://api.fizko.ai
```

El script enviará 4 mensajes de prueba y te dirá qué buscar en los logs.

---

### Opción 2: Test Manual

#### Paso 1: Preparar logs

```bash
# Terminal 1: Ver logs en tiempo real
tail -f logs/app.log | grep --color=always "STICKY AGENT\|HANDOFF"
```

#### Paso 2: Enviar primer mensaje

```bash
# Terminal 2: Enviar request
curl -X POST http://localhost:8089/chatkit \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "test-123",
    "text": "muestra mis facturas del mes pasado"
  }'
```

**Logs esperados:**
```
👔 [STICKY AGENT] Using supervisor (no active agent) | Thread: test-123 | Channel: web
📄 [HANDOFF] Supervisor → Tax Documents | Reason: User wants tax documents | Thread: test-123 | Tools: 12
✅ [STICKY AGENT] New: tax_documents_agent | Thread: test-123 | Total tracked: 1
```

✅ **Interpretación:** Supervisor hizo handoff y guardó el agente activo.

---

#### Paso 3: Enviar segundo mensaje (CRÍTICO)

```bash
curl -X POST http://localhost:8089/chatkit \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "test-123",
    "text": "cuántas facturas tengo?"
  }'
```

**Logs esperados (✅ Funcionando):**
```
🎯 [STICKY AGENT] Active: tax_documents_agent | Thread: test-123 | Total tracked: 1
🔄 [STICKY AGENT] Using active agent: Tax Documents Expert | Thread: test-123 | Channel: web
```

**Logs NO deseados (❌ No funcionando):**
```
👔 [STICKY AGENT] Using supervisor (no active agent) | Thread: test-123 | Channel: web
```

---

#### Paso 4: Verificar persistencia

```bash
# Reiniciar el servidor
pkill -f "uvicorn\|gunicorn" && ./dev.sh

# Esperar 5 segundos para que inicie
sleep 5

# Enviar otro mensaje en el mismo thread
curl -X POST http://localhost:8089/chatkit \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "test-123",
    "text": "otra pregunta"
  }'
```

**Logs esperados (❌ Sin Redis - Estado perdido):**
```
👔 [STICKY AGENT] Using supervisor (no active agent) | Thread: test-123
```

**Logs esperados (✅ Con Redis - Estado persiste):**
```
🎯 [STICKY AGENT] Active: tax_documents_agent | Thread: test-123
```

---

## 📊 Verificación de Métricas

### Ver threads activos

```bash
# Último estado de threads tracked
grep "Total tracked:" logs/app.log | tail -1
```

**Output esperado:**
```
Total tracked: 5
```

---

### Ver sticky agent hit rate

```bash
# Ver últimos 50 requests
grep "\[STICKY AGENT\] Using" logs/app.log | tail -50
```

**Análisis:**
- Si ves más `🔄 Using active agent` que `👔 Using supervisor` → ✅ Funcionando
- Si ves solo `👔 Using supervisor` → ❌ No funciona

**Hit rate esperado:** >40% de "Using active agent" (indica que sticky agents funcionan)

---

### Ver distribución de handoffs

```bash
# Contar handoffs por agente
grep "\[HANDOFF\] Supervisor →" logs/app.log | \
  awk -F'→' '{print $2}' | awk '{print $1}' | \
  sort | uniq -c | sort -rn
```

**Output ejemplo:**
```
   45 Tax Documents
   23 Monthly Taxes
   12 Payroll
    8 General Knowledge
    5 Settings
```

---

## 🐛 Troubleshooting

### Problema 1: "Using supervisor" en todos los mensajes

**Síntoma:**
```log
👔 [STICKY AGENT] Using supervisor (no active agent)
👔 [STICKY AGENT] Using supervisor (no active agent)
👔 [STICKY AGENT] Using supervisor (no active agent)
```

**Diagnóstico:**

```bash
# 1. Verificar si hay handoffs
grep "[HANDOFF] Supervisor →" logs/app.log | tail -5

# Si NO hay handoffs → supervisor no está transfiriendo
# Si HAY handoffs → problema en SessionManager
```

**Solución:**
- Si no hay handoffs: Verificar prompts del supervisor
- Si hay handoffs: Verificar que SessionManager.set_active_agent() se llama

---

### Problema 2: Thread IDs diferentes

**Síntoma:**
```log
✅ [STICKY AGENT] New: tax_documents_agent | Thread: abc123...
👔 [STICKY AGENT] Using supervisor | Thread: xyz789...  # Thread diferente!
```

**Diagnóstico:**
```bash
# Ver thread IDs únicos
grep "Thread:" logs/app.log | awk '{print $5}' | sort | uniq
```

**Solución:**
- Asegurarse de usar el mismo `thread_id` en todas las requests
- En ChatKit: el frontend debe mantener el thread_id
- En WhatsApp: usar el mismo `conversation_id`

---

### Problema 3: Total tracked crece sin límite

**Síntoma:**
```log
Total tracked: 500
Total tracked: 1000
Total tracked: 5000
```

**Causa:**
- Memory leak: threads nunca se limpian
- Sin TTL en SessionManager

**Solución:**
- Implementar Redis con TTL de 24h
- O implementar cleanup manual periódico

---

## 🎯 Criterios de Éxito

### ✅ Funcionando correctamente

1. **Primera conversación:**
   - ✅ Supervisor hace handoff
   - ✅ SessionManager guarda agente activo
   - ✅ Total tracked incrementa

2. **Conversaciones subsecuentes:**
   - ✅ Usa agente activo (no supervisor)
   - ✅ Total tracked se mantiene
   - ✅ Thread ID consistente

3. **Performance:**
   - ✅ Hit rate >40%
   - ✅ Latencia reducida en mensajes subsecuentes

### ❌ NO funcionando

1. **Síntomas:**
   - ❌ Siempre usa supervisor
   - ❌ No hay logs de "Active: [agent]"
   - ❌ Total tracked siempre 0

2. **Posibles causas:**
   - Handoffs no se ejecutan
   - SessionManager no guarda
   - Thread IDs diferentes

---

## 📝 Checklist de Testing

Antes de marcar como "funcionando", verificar:

- [ ] Primer mensaje usa supervisor
- [ ] Handoff se ejecuta y guarda
- [ ] Segundo mensaje usa agente activo (sticky)
- [ ] Tercer mensaje también usa agente activo
- [ ] Total tracked incrementa correctamente
- [ ] Thread ID es consistente
- [ ] Logs muestran `🔄 Using active agent`
- [ ] Hit rate >40% en conversaciones reales

**Con persistencia (Redis/DB):**
- [ ] Estado sobrevive restart del servidor
- [ ] Estado sobrevive deploy
- [ ] Funciona en multi-instancia

---

## 🔬 Testing Avanzado

### Test de Carga

```bash
# Generar 100 threads con conversaciones
for i in {1..100}; do
  curl -s -X POST http://localhost:8089/chatkit \
    -H "Content-Type: application/json" \
    -d "{
      \"thread_id\": \"load-test-$i\",
      \"text\": \"muestra facturas\"
    }" &
done

# Esperar a que terminen
wait

# Verificar total tracked
grep "Total tracked:" logs/app.log | tail -1
# Debería mostrar ~100
```

### Test de Persistencia

```bash
# Script para testear restart
./scripts/test_sticky_agents.sh
sleep 5
docker restart fizko-backend  # O reiniciar manualmente
sleep 10
./scripts/test_sticky_agents.sh

# Comparar logs antes/después del restart
```

---

## 📚 Referencias

- **Guía de logs:** [STICKY_AGENTS_LOGGING.md](./STICKY_AGENTS_LOGGING.md)
- **Estado actual:** [STICKY_AGENTS_STATUS.md](./STICKY_AGENTS_STATUS.md)
- **Diseño completo:** [STICKY_AGENTS_DESIGN.md](./STICKY_AGENTS_DESIGN.md)
