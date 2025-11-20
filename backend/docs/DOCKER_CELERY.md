# Docker Compose con Celery - Backend V2

Guía para ejecutar Backend V2 con Celery usando Docker Compose.

## 🚀 Quick Start

```bash
# 1. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 2. Levantar todos los servicios
docker-compose up -d

# 3. Ver logs
docker-compose logs -f celery-worker
docker-compose logs -f celery-beat
```

## 📦 Servicios Incluidos

### 1. **backend** - FastAPI (puerto 8000)
Servidor web principal con endpoints REST.

```bash
# Ver logs
docker-compose logs -f backend

# Reiniciar
docker-compose restart backend
```

### 2. **celery-worker** - Worker de Celery
Procesa tareas SII en background (scraping, sincronización).

```bash
# Ver logs
docker-compose logs -f celery-worker

# Escalar workers (más capacidad)
docker-compose up -d --scale celery-worker=3

# Reiniciar
docker-compose restart celery-worker
```

### 3. **celery-beat** - Scheduler
Programa tareas periódicas (syncs automáticos).

```bash
# Ver logs
docker-compose logs -f celery-beat

# Reiniciar
docker-compose restart celery-beat
```

### 4. **redis** - Message Broker (puerto 6379)
Cola de mensajes para Celery.

```bash
# Ver logs
docker-compose logs -f redis

# Conectarse a Redis CLI
docker-compose exec redis redis-cli

# Ver tareas en cola
docker-compose exec redis redis-cli LLEN celery
```

### 5. **ngrok** - Tunnel público (puerto 4040)
Para webhooks en desarrollo.

```bash
# Ver URL pública
open http://localhost:4040
```

## ⚙️ Variables de Entorno Requeridas

### Para FastAPI y Worker

```bash
# Supabase (requerido)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_ANON_KEY=eyJ...

# OpenAI (para agentes)
OPENAI_API_KEY=sk-...

# Redis (auto-configurado en Docker)
REDIS_URL=redis://redis:6379/0
```

### Solo para Beat Scheduler

```bash
# PostgreSQL dedicado para Beat scheduler
# IMPORTANTE: Usar una DB dedicada en Railway (NO Supabase)
# Railway provee PostgreSQL gratis para proyectos pequeños
DATABASE_URL=postgresql://user:pass@containers-us-west-xxx.railway.app:5432/railway

# Notas:
# - DATABASE_URL es SOLO para el Beat scheduler (sqlalchemy-celery-beat)
# - Las tareas usan Supabase client (SUPABASE_URL), NO DATABASE_URL
# - Usar DB dedicada evita conflictos con tablas de aplicación
# - Railway auto-gestiona backups y escalamiento
```

## 🔧 Comandos Útiles

### Iniciar/Detener Servicios

```bash
# Levantar todos los servicios
docker-compose up -d

# Levantar servicios específicos
docker-compose up -d backend celery-worker

# Detener todo
docker-compose down

# Detener y eliminar volúmenes (limpia Redis data)
docker-compose down -v
```

### Logs y Debugging

```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f celery-worker

# Ver últimas 100 líneas
docker-compose logs --tail=100 celery-worker

# Ver logs con timestamps
docker-compose logs -f --timestamps celery-worker
```

### Ejecutar Comandos

```bash
# Shell interactivo en worker
docker-compose exec celery-worker bash

# Ejecutar tarea manualmente
docker-compose exec celery-worker python -c "
from app.infrastructure.celery.tasks.sii import sync_documents
result = sync_documents.delay('company-id', months=1)
print(f'Task ID: {result.id}')
"

# Ver Python packages instalados
docker-compose exec celery-worker pip list

# Ejecutar tests
docker-compose exec backend pytest tests/ -v
```

### Monitoring

```bash
# Ver estado de Redis
docker-compose exec redis redis-cli INFO

# Ver tareas pendientes en cola 'low'
docker-compose exec redis redis-cli LLEN low

# Ver tareas pendientes en cola 'default'
docker-compose exec redis redis-cli LLEN default

# Vaciar todas las colas (limpiar tareas pendientes)
docker-compose exec redis redis-cli FLUSHALL
```

### Rebuild y Update

```bash
# Rebuild imágenes (después de cambiar pyproject.toml)
docker-compose build

# Rebuild sin cache (forzar reinstalación completa)
docker-compose build --no-cache

# Rebuild y reiniciar
docker-compose up -d --build
```

## 📊 Configuración de Workers

### Escalar Workers

Para manejar más carga, puedes escalar los workers:

```bash
# Escalar a 3 workers
docker-compose up -d --scale celery-worker=3

# Verificar
docker-compose ps
```

### Configurar Concurrency

En `docker-compose.yml` o via variables de entorno:

```yaml
celery-worker:
  environment:
    - CELERY_CONCURRENCY=4  # 4 tareas simultáneas por worker
    - CELERY_LOG_LEVEL=debug  # Más detalle en logs
```

O al iniciar:

```bash
CELERY_CONCURRENCY=4 docker-compose up -d celery-worker
```

## 🐛 Troubleshooting

### Worker no procesa tareas

```bash
# 1. Verificar que Redis está funcionando
docker-compose exec redis redis-cli ping
# Debe retornar: PONG

# 2. Ver logs del worker
docker-compose logs -f celery-worker

# 3. Verificar que las tareas están en cola
docker-compose exec redis redis-cli LLEN low
docker-compose exec redis redis-cli LLEN default

# 4. Reiniciar worker
docker-compose restart celery-worker
```

### Beat no programa tareas

```bash
# 1. Verificar DATABASE_URL configurado
docker-compose exec celery-beat env | grep DATABASE_URL

# 2. Ver logs de Beat
docker-compose logs -f celery-beat

# 3. Verificar conexión a PostgreSQL
docker-compose exec celery-beat bash -c \
  'psql $DATABASE_URL -c "SELECT * FROM celery_schema.celery_periodictask LIMIT 5;"'

# 4. Reiniciar Beat
docker-compose restart celery-beat
```

### Redis connection refused

```bash
# 1. Verificar que Redis está corriendo
docker-compose ps redis

# 2. Ver logs de Redis
docker-compose logs redis

# 3. Reiniciar Redis
docker-compose restart redis

# 4. Si sigue fallando, recrear container
docker-compose rm -f redis
docker-compose up -d redis
```

### Worker crashes con OOM (Out of Memory)

```bash
# Reducir concurrency en docker-compose.yml
environment:
  - CELERY_CONCURRENCY=1  # Menos tareas simultáneas

# O aumentar memoria del container
deploy:
  resources:
    limits:
      memory: 2G  # Aumentar a 2GB
```

### Tareas muy lentas

```bash
# Ver tareas activas
docker-compose exec redis redis-cli LLEN celery

# Ver tareas que están ejecutándose ahora
docker-compose logs --tail=50 celery-worker | grep "Task"

# Aumentar timeout
environment:
  - CELERY_TASK_TIME_LIMIT=3600  # 1 hora
```

## 📈 Producción

### Recomendaciones

1. **Usar servicios externos** (no containers):
   - **PostgreSQL (Beat)**: Railway PostgreSQL (dedicado para scheduler)
   - **Redis**: Upstash Redis (gratis hasta 10K comandos/día)
   - **Supabase**: Para datos de aplicación (separado de Beat)

2. **Variables de entorno** en `.env`:
   ```bash
   # PostgreSQL dedicado para Beat (Railway)
   DATABASE_URL=postgresql://user:pass@containers-us-west-xxx.railway.app:5432/railway

   # Redis externo (Upstash)
   REDIS_URL=redis://:password@us1-xxx.upstash.io:6379

   # Supabase (datos de aplicación)
   SUPABASE_URL=https://xxx.supabase.co
   SUPABASE_SERVICE_KEY=eyJ...
   ```

   **¿Por qué DB dedicada para Beat?**
   - Aislamiento: Evita conflictos con tablas de aplicación
   - Simplicidad: No necesita RLS ni políticas de Supabase
   - Railway: Provee PostgreSQL gratis con backups automáticos
   - Escalamiento: Fácil migrar a DB más grande si crece

3. **Escalar workers** según carga:
   ```bash
   docker-compose up -d --scale celery-worker=5
   ```

4. **Monitoring** con Flower:
   ```yaml
   flower:
     image: mher/flower
     command: celery --broker=$REDIS_URL flower --port=5555
     ports:
       - "5555:5555"
     environment:
       - CELERY_BROKER_URL=$REDIS_URL
   ```

5. **Logs centralizados**:
   - CloudWatch, Datadog, o Sentry
   - Capturar stderr/stdout de containers

### Deployment

Para producción, considera usar orquestadores:

- **Railway**: Deploy directo desde GitHub
- **Render**: Deploy de containers con auto-scaling
- **AWS ECS/Fargate**: Escalamiento empresarial
- **Kubernetes**: Para control total

## 🔗 Referencias

- [docker-compose.yml](docker-compose.yml) - Configuración de servicios
- [Dockerfile](Dockerfile) - Imagen de containers
- [docker-entrypoint.sh](docker-entrypoint.sh) - Entry point
- [Celery README](app/infrastructure/celery/README.md) - Documentación de tareas
