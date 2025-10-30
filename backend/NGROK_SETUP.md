# 🌐 ngrok Setup - Desarrollo Local con Webhooks

Guía para configurar ngrok en Docker Compose y recibir webhooks de servicios externos (Kapso, SII, etc.) en tu entorno de desarrollo local.

---

## 📋 Requisitos Previos

1. **Cuenta de ngrok** (gratuita)
   - Registrarse en: https://dashboard.ngrok.com/signup
   - Verificar email

2. **Obtener Auth Token**
   - Dashboard: https://dashboard.ngrok.com/get-started/your-authtoken
   - Copiar tu authtoken (ejemplo: `2abc...xyz`)

---

## 🚀 Setup

### 1️⃣ Agregar Token al `.env`

Edita `backend/.env` y agrega tu token de ngrok:

```bash
# ========================================
# NGROK (Development - Webhooks)
# ========================================
NGROK_AUTHTOKEN=2abc...xyz  # ← Pegar tu token aquí
```

### 2️⃣ Iniciar ngrok con Docker Compose

**Opción A: Solo ngrok**
```bash
cd backend
docker-compose --profile dev up ngrok
```

**Opción B: Todo el stack (backend + workers + flower + ngrok)**
```bash
docker-compose --profile dev --profile monitoring up
```

**Opción C: En background**
```bash
docker-compose --profile dev --profile monitoring up -d
```

### 3️⃣ Obtener la URL Pública

Una vez iniciado, ngrok generará una URL pública. Hay 3 formas de obtenerla:

**A. Dashboard Web de ngrok** (Recomendado)
```
http://localhost:4040
```
- Ver requests en tiempo real
- Inspeccionar payloads
- Replay requests

**B. Ver logs de Docker**
```bash
docker-compose logs ngrok | grep "started tunnel"
```

**C. API de ngrok**
```bash
curl http://localhost:4040/api/tunnels | jq '.tunnels[0].public_url'
```

Ejemplo de URL generada:
```
https://abc123-def-456.ngrok-free.app
```

---

## 🔧 Configuración en Servicios Externos

### Kapso (WhatsApp)

1. **Ir a Kapso Dashboard**: https://app.kapso.ai
2. **Configurar webhook**:
   ```
   URL: https://TU-URL-NGROK.ngrok-free.app/api/whatsapp/webhook
   Secret: (ya configurado en .env como KAPSO_WEBHOOK_SECRET)
   ```

### Otros Servicios

Para otros webhooks, usa la misma base URL:
```
https://TU-URL-NGROK.ngrok-free.app/api/...
```

---

## 🔍 Monitoreo

### Dashboard de ngrok
```
http://localhost:4040
```

Funcionalidades:
- ✅ Ver todos los requests HTTP en tiempo real
- ✅ Inspeccionar headers, body, response
- ✅ Replay requests (útil para debugging)
- ✅ Estadísticas de uso

### Logs de Docker
```bash
# Ver logs de ngrok
docker-compose logs -f ngrok

# Ver logs del backend (para ver webhooks recibidos)
docker-compose logs -f backend
```

---

## 📝 Configuración Avanzada

### Múltiples Túneles

Edita `backend/ngrok.yml` para agregar más túneles:

```yaml
tunnels:
  backend:
    proto: http
    addr: backend:8000
    schemes:
      - https

  flower:  # ← Agregar Flower
    proto: http
    addr: flower:5555
    schemes:
      - https
```

Luego reinicia ngrok:
```bash
docker-compose restart ngrok
```

### Dominio Custom (Plan Pago)

Si tienes plan de pago de ngrok, puedes usar un dominio fijo:

```yaml
tunnels:
  backend:
    proto: http
    addr: backend:8000
    domain: fizko-backend.ngrok.app  # ← Tu dominio reservado
```

---

## 🐛 Troubleshooting

### Error: "authentication failed"
- **Causa**: Token inválido o no configurado
- **Solución**: Verificar `NGROK_AUTHTOKEN` en `.env`

### Error: "tunnel not found"
- **Causa**: Backend no está corriendo
- **Solución**:
  ```bash
  docker-compose up backend
  docker-compose up ngrok
  ```

### Warning: "You are visiting this site..."
- **Causa**: Página de advertencia de ngrok (normal en plan free)
- **Solución**: Los webhooks automáticos (como Kapso) pasan esta advertencia automáticamente. Si necesitas evitarla completamente, considera el plan de pago.

### Puerto 4040 ya en uso
- **Causa**: Ya tienes ngrok corriendo fuera de Docker
- **Solución**:
  ```bash
  # Detener ngrok local
  pkill ngrok

  # O cambiar el puerto en docker-compose.yml
  ports:
    - "4041:4040"  # Usar otro puerto
  ```

---

## 🔐 Seguridad

### ⚠️ Importantes

1. **NO commitear** el authtoken en el repositorio
   - Siempre usar variable de entorno
   - `.env` está en `.gitignore`

2. **Validar webhooks** siempre con signature
   - El backend valida `KAPSO_WEBHOOK_SECRET`
   - Ver: `app/routers/whatsapp/main.py`

3. **Solo para desarrollo local**
   - ngrok NO debe usarse en producción
   - En producción usa dominios reales con HTTPS

---

## 📚 Recursos

- [ngrok Documentation](https://ngrok.com/docs)
- [ngrok Docker Image](https://hub.docker.com/r/ngrok/ngrok)
- [Kapso Webhooks](https://app.kapso.ai/docs/webhooks)
- [Backend Webhook Endpoint](../app/routers/whatsapp/main.py)

---

## 🎯 Comandos Útiles

```bash
# Iniciar todo el stack con ngrok
docker-compose --profile dev --profile monitoring up

# Solo backend + ngrok
docker-compose up backend ngrok

# Detener ngrok
docker-compose stop ngrok

# Ver URL de ngrok
curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url'

# Reiniciar ngrok (nueva URL)
docker-compose restart ngrok
```

---

**Última actualización**: 2025-10-30
