# 🔧 Admin Task Manager

Gestor de tareas Celery integrado en el panel de administración de Fizko.

## 📍 Ubicación

```
URL: http://localhost:5171/admin/task-manager
Ruta: /admin/task-manager
Componente: frontend/src/pages/AdminTaskManager.tsx
```

## ✨ Características

### 1. **Tareas Programadas** (Tab Principal)

Administra tareas periódicas ejecutadas por Celery Beat:

- ✅ **Crear tareas** con dos tipos de programación:
  - **Intervalo**: Ejecutar cada N minutos/horas/días
  - **Crontab**: Ejecutar en horarios específicos (expresiones cron)
- ✅ **Ver todas las tareas** con estado (activa/pausada)
- ✅ **Pausar/Activar tareas** con un clic
- ✅ **Ejecutar tareas manualmente** (fuera de programación)
- ✅ **Eliminar tareas** programadas
- ✅ **Monitoreo**: Ver última ejecución y total de ejecuciones
- ✅ **Multi-tenancy**: Cada compañía ve solo sus tareas (RLS)

**Tarjetas de información muestran:**
- Nombre y descripción de la tarea
- Horario de ejecución (intervalo o cron)
- Cola asignada (high, default, low)
- Estado (activa/pausada)
- Estadísticas (total de ejecuciones, última ejecución)

### 2. **Cola de Tareas** (Monitoreo en tiempo real)

Vista en tiempo real del estado de Celery:

- 📊 **Dashboard con métricas**:
  - Tareas activas (en ejecución)
  - Tareas en cola (esperando)
  - Workers disponibles
- 📋 **Lista de tareas activas** con:
  - Nombre de la tarea
  - Estado (PENDING, STARTED, SUCCESS, FAILURE)
  - Worker asignado
  - Task ID
- ⚡ **Auto-refresh** cada 5 segundos

> **Nota**: Este tab requiere implementar `GET /api/tasks/active` en el backend para consultar el estado de Celery workers.

### 3. **Historial** (Ejecuciones pasadas)

Visualiza el historial completo de ejecuciones:

- 📜 **Lista de ejecuciones** con:
  - Estado (éxito, fallo, pendiente)
  - Fechas de inicio y fin
  - Duración de la ejecución
  - Worker que ejecutó la tarea
- 🔍 **Vista expandible** con:
  - Resultado JSON completo
  - Stack trace de errores (si falló)
  - Task ID único
- 💬 **Diálogo de detalles** para inspección profunda

> **Nota**: Actualmente muestra placeholder. Requiere implementar `GET /api/tasks/history` en el backend.

## 🎨 Interfaz de Usuario

### Diseño
- **Tabs navegables**: 3 pestañas (Tareas Programadas, Cola, Historial)
- **Cards interactivas**: Hover effects y animaciones suaves
- **Badges de estado**: Colores semánticos (verde=activo, rojo=error, azul=ejecutando)
- **Responsive**: Grid adaptativo para móvil, tablet y desktop
- **Gradients**: Diseño moderno con gradientes azul/índigo

### Componentes UI Utilizados
- `Card`, `CardHeader`, `CardContent` - Contenedores
- `Badge` - Estados y etiquetas
- `Button` - Acciones (activar, pausar, eliminar, ejecutar)
- `Dialog` - Modales para crear tareas y ver detalles
- `Tabs` - Navegación principal
- `Input`, `Textarea`, `Select` - Formularios
- `Loader2` - Indicadores de carga
- Iconos de `lucide-react`

## 📁 Estructura de Archivos

```
frontend/src/
├── pages/
│   └── AdminTaskManager.tsx                    # Página principal con tabs
├── components/admin/task-manager/
│   ├── ScheduledTasksTab.tsx                   # Tab 1: Tareas programadas (CRUD)
│   ├── CreateTaskDialog.tsx                    # Modal para crear tareas
│   ├── TaskQueueTab.tsx                        # Tab 2: Monitoreo en tiempo real
│   └── TaskHistoryTab.tsx                      # Tab 3: Historial de ejecuciones
```

## 🔌 Integración con Backend

### Endpoints Utilizados

#### ✅ Implementados (funcionando)

```typescript
// Tareas Programadas
GET    /api/scheduled-tasks              // Listar tareas
POST   /api/scheduled-tasks              // Crear tarea
PUT    /api/scheduled-tasks/{id}         // Actualizar tarea
DELETE /api/scheduled-tasks/{id}         // Eliminar tarea
POST   /api/scheduled-tasks/{id}/enable  // Activar tarea
POST   /api/scheduled-tasks/{id}/disable // Pausar tarea
POST   /api/scheduled-tasks/{id}/run-now // Ejecutar manualmente
GET    /api/scheduled-tasks/{id}/executions // Historial de una tarea específica
```

#### 🚧 Pendientes (placeholder)

```typescript
// Cola en tiempo real
GET /api/tasks/active              // Tareas activas en Celery workers

// Historial global
GET /api/tasks/history             // Todas las ejecuciones recientes
```

### Formato de Datos

**Tarea Programada (ScheduledTask):**
```typescript
interface ScheduledTask {
  id: number;
  name: string;                    // "sync-docs-hourly"
  task: string;                    // "sii.sync_documents"
  schedule_type: string;           // "interval" | "crontab"
  schedule_display: string;        // "Every 30 minutes"
  enabled: boolean;
  last_run_at: string | null;
  total_run_count: number;
  queue: string | null;            // "high" | "default" | "low"
  description: string | null;
}
```

**Crear Tarea (Request):**
```typescript
// Ejemplo: Intervalo
{
  "name": "sync-docs-hourly",
  "task": "sii.sync_documents",
  "schedule_type": "interval",
  "interval_every": 1,
  "interval_period": "hours",
  "kwargs": {"session_id": "uuid", "months": 1},
  "queue": "low",
  "enabled": true,
  "description": "Sincroniza documentos cada hora"
}

// Ejemplo: Crontab (diario a las 00:00)
{
  "name": "daily-sync",
  "task": "sii.sync_documents",
  "schedule_type": "crontab",
  "crontab_minute": "0",
  "crontab_hour": "0",
  "crontab_day_of_week": "*",
  "crontab_day_of_month": "*",
  "crontab_month_of_year": "*",
  "crontab_timezone": "America/Santiago",
  "kwargs": {"session_id": "uuid", "months": 1},
  "queue": "low",
  "enabled": true
}
```

## 🚀 Cómo Usar

### 1. Acceder al Task Manager

```bash
# Navega a la URL en tu navegador
http://localhost:5171/admin/task-manager
```

### 2. Crear una Tarea Programada

1. Haz clic en **"Nueva Tarea"**
2. Completa el formulario:
   - **Nombre**: Identificador único (ej: `sync-docs-hourly`)
   - **Tarea Celery**: Selecciona la tarea (ej: `sii.sync_documents`)
   - **Descripción**: Opcional, describe qué hace
   - **Cola**: Elige prioridad (high, default, low)
3. Configura la programación:
   - **Tab Intervalo**: Ejecutar cada N minutos/horas/días
   - **Tab Crontab**: Horarios específicos (cron)
4. **Argumentos (JSON)**: Parámetros que recibirá la tarea
5. Clic en **"Crear Tarea"**

### 3. Gestionar Tareas

- **Pausar**: Clic en botón "Pausar" (la tarea no se ejecutará)
- **Activar**: Clic en "Activar" (reanuda la programación)
- **Ejecutar Ahora**: Clic en ▶️ (ejecuta fuera de horario)
- **Eliminar**: Clic en 🗑️ (elimina permanentemente)

### 4. Monitorear Ejecuciones

- **Tab "Cola de Tareas"**: Ver tareas ejecutándose ahora
- **Tab "Historial"**: Ver ejecuciones pasadas
  - Expandir para ver resultado JSON
  - Ver errores con stack trace completo

## 🔧 Configuración

### Environment Variables (Frontend)

Ya configurado en `lib/config.ts`:
```typescript
export const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8089';
```

### React Query

Configurado con:
- **staleTime**: 5 minutos (tareas programadas no cambian frecuentemente)
- **refetchInterval**:
  - Tareas programadas: 10 segundos
  - Cola en tiempo real: 5 segundos
  - Historial: 15 segundos

### Toasts (Notificaciones)

Utiliza `sonner` para feedback visual:
- ✅ **Success**: Tarea creada/actualizada/eliminada
- ❌ **Error**: Fallos de API o validación
- ℹ️ **Info**: Tarea ejecutada manualmente

## 🎯 Casos de Uso

### Caso 1: Sincronización Horaria de Documentos

```typescript
// Crear tarea que sincroniza cada hora
{
  name: "sync-docs-hourly-company-123",
  task: "sii.sync_documents",
  schedule_type: "interval",
  interval_every: 1,
  interval_period: "hours",
  kwargs: {
    "session_id": "company-session-uuid",
    "months": 1
  },
  queue: "low"
}
```

### Caso 2: Reporte Diario a Medianoche

```typescript
// Crear tarea cron para las 00:00 todos los días
{
  name: "daily-report-midnight",
  task: "reports.generate_daily",
  schedule_type: "crontab",
  crontab_minute: "0",
  crontab_hour: "0",
  crontab_timezone: "America/Santiago",
  kwargs: {
    "company_id": "123",
    "report_type": "daily_summary"
  },
  queue: "default"
}
```

### Caso 3: Sincronización de Fin de Mes

```typescript
// Ejecutar el último día de cada mes a las 23:00
{
  name: "month-end-sync",
  task: "sii.sync_documents",
  schedule_type: "crontab",
  crontab_minute: "0",
  crontab_hour: "23",
  crontab_day_of_month: "28-31",  // Últimos días del mes
  crontab_timezone: "America/Santiago",
  kwargs: {
    "session_id": "uuid",
    "months": 1
  },
  queue: "high"  // Alta prioridad para cierre de mes
}
```

## 🐛 Troubleshooting

### "No hay tareas programadas"

- ✅ Verifica que Celery Beat esté corriendo: `./start_beat.sh`
- ✅ Verifica que la migración RLS esté aplicada
- ✅ Verifica que tengas una sesión activa con una compañía

### "Error: Failed to fetch tasks"

- ✅ Verifica que el backend esté corriendo (puerto 8089)
- ✅ Verifica el JWT token en el AuthContext
- ✅ Revisa la consola del navegador para errores de CORS
- ✅ Verifica permisos RLS en Supabase

### "Task with name 'X' already exists"

- ✅ Cada tarea debe tener un nombre único por compañía
- ✅ Usa nombres descriptivos: `sync-docs-hourly-company-123`
- ✅ Considera incluir el company_id en el nombre

### Tareas no se ejecutan

- ✅ Verifica que la tarea esté **habilitada** (badge verde)
- ✅ Verifica que Celery Worker esté corriendo: `./start_celery.sh`
- ✅ Verifica que Celery Beat esté corriendo: `./start_beat.sh`
- ✅ Revisa los logs del worker para errores

## 🔮 Próximas Mejoras

### Backend Pendiente
- [ ] Implementar `GET /api/tasks/active` (Celery inspect)
- [ ] Implementar `GET /api/tasks/history` (query global)
- [ ] Agregar filtros por fecha/estado en historial
- [ ] Implementar búsqueda/filtrado de tareas
- [ ] Agregar paginación para listas grandes

### Frontend Pendiente
- [ ] Editar tareas existentes (actualmente solo crear/eliminar)
- [ ] Vista de calendario para programación visual
- [ ] Gráficos de éxito/fallo por tarea
- [ ] Exportar historial a CSV/Excel
- [ ] Notificaciones en tiempo real (WebSockets)
- [ ] Búsqueda y filtros avanzados
- [ ] Modo oscuro

### Optimizaciones
- [ ] Virtual scrolling para listas largas
- [ ] Lazy loading de ejecuciones antiguas
- [ ] Caché optimista para acciones rápidas
- [ ] Polling inteligente (solo cuando tab visible)

## 📚 Referencias

- [Celery Beat Documentation](https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html)
- [Backend: CELERY_BEAT.md](../backend/CELERY_BEAT.md)
- [Backend: CELERY_STRUCTURE.md](../backend/CELERY_STRUCTURE.md)
- [Crontab Guru](https://crontab.guru/) - Generador de expresiones cron

---

**Desarrollado para Fizko** | Versión 1.0.0 | Octubre 2024
