# Seed Scripts con Docker

Guía para ejecutar seed scripts usando Docker.

## 🐳 Prerequisitos

1. **Imagen Docker construida**:
   ```bash
   cd backend
   docker build -t fizko-backend .
   ```

2. **Variables de entorno configuradas** en `backend/.env`:
   ```bash
   STAGING_SUPABASE_URL=https://xxx.supabase.co
   STAGING_SUPABASE_SERVICE_KEY=eyJhbG...
   PROD_SUPABASE_URL=https://yyy.supabase.co
   PROD_SUPABASE_SERVICE_KEY=eyJhbG...
   ```

## 🚀 Uso Básico

### Sintaxis General

```bash
docker run --rm --env-file backend/.env fizko-backend seed <command> [options]
```

**Flags importantes:**
- `--rm` - Elimina el contenedor después de ejecutar (limpieza automática)
- `--env-file backend/.env` - Carga variables de entorno desde archivo
- `fizko-backend` - Nombre de la imagen Docker (ajustar según tu build)

## 📝 Ejemplos Comunes

### 1. Dry Run (Siempre Primero!)

```bash
# Ver qué se sincronizaría sin aplicar cambios
docker run --rm --env-file backend/.env fizko-backend seed \
  notification-templates --to production --dry-run
```

### 2. Sincronizar Notification Templates

```bash
# Dry run
docker run --rm --env-file backend/.env fizko-backend seed \
  notification-templates --to production --dry-run

# Aplicar cambios
docker run --rm --env-file backend/.env fizko-backend seed \
  notification-templates --to production
```

### 3. Sincronizar Event Templates

```bash
docker run --rm --env-file backend/.env fizko-backend seed \
  event-templates --to production --dry-run
```

### 4. Sincronizar Templates Específicos

```bash
docker run --rm --env-file backend/.env fizko-backend seed \
  notification-templates \
  --to production \
  --codes f29_reminder,daily_summary \
  --dry-run
```

### 5. Sincronizar Todo

```bash
docker run --rm --env-file backend/.env fizko-backend seed \
  all --to production --dry-run
```

### 6. Comando Genérico (Cualquier Tabla)

```bash
docker run --rm --env-file backend/.env fizko-backend seed sync \
  --table brain_contexts \
  --unique-key context_id \
  --to production \
  --dry-run
```

### 7. Modo Verbose (Ver Detalles)

```bash
docker run --rm --env-file backend/.env fizko-backend seed \
  notification-templates \
  --to production \
  --verbose \
  --dry-run
```

## 🔧 Alternativas de Ejecución

### Opción 1: Docker Run (Recomendado)

```bash
docker run --rm --env-file backend/.env fizko-backend seed <command>
```

**Ventajas:**
- ✅ Limpio - contenedor se elimina automáticamente
- ✅ Reproducible
- ✅ No requiere contenedor corriendo

### Opción 2: Docker Exec (Si ya tienes contenedor corriendo)

```bash
# Si tu backend ya está corriendo
docker exec fizko-backend-container python -m scripts.seed notification-templates --to production --dry-run
```

**Ventajas:**
- ✅ Más rápido (no inicia nuevo contenedor)
- ✅ Usa el mismo entorno del contenedor corriendo

**Desventajas:**
- ❌ Requiere contenedor corriendo
- ❌ Debes pasar el comando completo `python -m scripts.seed`

### Opción 3: Docker Compose

Si usas `docker-compose.yml`:

```bash
docker-compose run --rm backend seed notification-templates --to production --dry-run
```

**Ventajas:**
- ✅ Usa la configuración de docker-compose
- ✅ Variables de entorno definidas en compose file

## 🐛 Troubleshooting

### Error: "Missing Supabase config"

**Problema**: Variables de entorno no se están pasando al contenedor.

**Soluciones:**

1. Verificar que `.env` existe y tiene las variables:
   ```bash
   grep STAGING_SUPABASE backend/.env
   grep PROD_SUPABASE backend/.env
   ```

2. Pasar variables explícitamente:
   ```bash
   docker run --rm \
     -e STAGING_SUPABASE_URL="https://xxx.supabase.co" \
     -e STAGING_SUPABASE_SERVICE_KEY="eyJhbG..." \
     -e PROD_SUPABASE_URL="https://yyy.supabase.co" \
     -e PROD_SUPABASE_SERVICE_KEY="eyJhbG..." \
     fizko-backend seed notification-templates --to production --dry-run
   ```

### Error: "Connection timeout" o "Network error"

**Problema**: Contenedor no puede conectarse a Supabase.

**Soluciones:**

1. Verificar conectividad desde el contenedor:
   ```bash
   docker run --rm fizko-backend bash -c "curl -I https://xxx.supabase.co"
   ```

2. Verificar que no hay firewall bloqueando:
   - Docker debe tener acceso a internet
   - Supabase debe ser accesible desde tu máquina

### Error: "Image not found"

**Problema**: La imagen Docker no está construida.

**Solución:**
```bash
cd backend
docker build -t fizko-backend .
```

### Script no encuentra módulos

**Problema**: Los scripts no se copiaron a la imagen.

**Solución**: Reconstruir imagen (el Dockerfile ya está actualizado):
```bash
cd backend
docker build --no-cache -t fizko-backend .
```

## 💡 Tips

1. **Siempre usa `--dry-run` primero**:
   ```bash
   docker run --rm --env-file backend/.env fizko-backend seed \
     notification-templates --to production --dry-run
   ```

2. **Usa `--verbose` para debugging**:
   ```bash
   docker run --rm --env-file backend/.env fizko-backend seed \
     notification-templates --to production --verbose --dry-run
   ```

3. **Guarda los comandos en un script** para reutilización:
   ```bash
   # backend/sync-to-prod.sh
   #!/bin/bash
   docker run --rm --env-file backend/.env fizko-backend seed all --to production "$@"

   # Uso:
   ./backend/sync-to-prod.sh --dry-run
   ./backend/sync-to-prod.sh  # live
   ```

4. **Ver logs completos**:
   Docker ya muestra todos los logs por defecto. Si necesitas guardarlos:
   ```bash
   docker run --rm --env-file backend/.env fizko-backend seed \
     notification-templates --to production --dry-run 2>&1 | tee sync-log.txt
   ```

## 🔐 Seguridad

1. **No commitees el `.env`** con service keys de producción
2. **Usa secrets de CI/CD** para automatización
3. **Rota las service keys** periódicamente
4. **Limita permisos** de service keys si es posible en Supabase

## 📚 Ver Más

- [README.md](README.md) - Documentación completa
- [QUICKSTART.md](QUICKSTART.md) - Guía rápida
- [EXAMPLES.md](EXAMPLES.md) - Más ejemplos
