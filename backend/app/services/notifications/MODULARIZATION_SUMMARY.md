# Modularización del Servicio de Notificaciones

## Resumen

El servicio de notificaciones ha sido refactorizado de un archivo monolítico de 1225 líneas a una arquitectura modular con responsabilidades claramente separadas.

## Antes vs Después

### Antes (Monolítico)
```
notifications/
├── service.py (1225 líneas - TODO EN UNO)
├── helpers.py
├── calendar_integration.py
├── scheduler.py
└── __init__.py
```

**Problemas:**
- ❌ Un archivo gigante difícil de mantener
- ❌ Múltiples responsabilidades mezcladas
- ❌ Difícil de testear unitariamente
- ❌ Difícil de entender el flujo
- ❌ Acoplamiento alto entre componentes

### Después (Modular)
```
notifications/
├── service.py (280 líneas - ORQUESTADOR)
├── modules/
│   ├── base_service.py (25 líneas)
│   ├── template_service.py (260 líneas)
│   ├── subscription_service.py (135 líneas)
│   ├── scheduling_service.py (215 líneas)
│   ├── sending_service.py (440 líneas)
│   ├── preference_service.py (155 líneas)
│   └── history_service.py (65 líneas)
├── helpers.py
├── calendar_integration.py
├── scheduler.py
└── __init__.py
```

**Ventajas:**
- ✅ Separación clara de responsabilidades
- ✅ Cada módulo tiene un propósito específico
- ✅ Más fácil de testear (tests unitarios por módulo)
- ✅ Mejor organización y mantenibilidad
- ✅ Acoplamiento bajo entre módulos
- ✅ Escalable - fácil agregar nuevos módulos

## Módulos Creados

### 1. BaseNotificationService
- **Responsabilidad**: Proveer dependencias comunes
- **Tamaño**: 25 líneas
- **Contiene**: WhatsAppService, logger

### 2. TemplateService
- **Responsabilidad**: CRUD de templates de notificaciones
- **Tamaño**: 260 líneas
- **Métodos**:
  - `get_template()` - Obtener template por ID o código
  - `list_templates()` - Listar con filtros
  - `create_template()` - Crear nuevo
  - `update_template()` - Actualizar existente
  - `delete_template()` - Eliminar (con validaciones)

### 3. SubscriptionService
- **Responsabilidad**: Gestión de suscripciones empresa-template
- **Tamaño**: 135 líneas
- **Métodos**:
  - `subscribe_company()` - Suscribir empresa
  - `unsubscribe_company()` - Desuscribir empresa
  - `get_company_subscriptions()` - Listar suscripciones

### 4. SchedulingService
- **Responsabilidad**: Programación y timing de notificaciones
- **Tamaño**: 215 líneas
- **Métodos**:
  - `schedule_notification()` - Programar notificación
  - `get_pending_notifications()` - Obtener pendientes
  - `_calculate_scheduled_time()` - Calcular timing
  - `_render_message()` - Renderizar template

### 5. SendingService
- **Responsabilidad**: Envío real de notificaciones por WhatsApp
- **Tamaño**: 440 líneas
- **Métodos**:
  - `send_scheduled_notification()` - Enviar una notificación
  - `process_pending_notifications()` - Procesar lote
  - `_check_user_preferences()` - Verificar preferencias
  - `_generate_notification_context()` - Generar contexto para agente

### 6. PreferenceService
- **Responsabilidad**: Gestión de preferencias de usuario
- **Tamaño**: 155 líneas
- **Métodos**:
  - `get_user_preferences()` - Obtener preferencias
  - `update_user_preferences()` - Actualizar preferencias

### 7. HistoryService
- **Responsabilidad**: Historial y analíticas
- **Tamaño**: 65 líneas
- **Métodos**:
  - `get_notification_history()` - Consultar historial con filtros

## Servicio Principal (Orquestador)

El `NotificationService` principal ahora actúa como un **orquestador** que:
- Inicializa todos los sub-servicios
- Delega llamadas a módulos especializados
- Mantiene la API pública consistente (backward compatible)

```python
class NotificationService:
    def __init__(self, whatsapp_service):
        self.templates = TemplateService(whatsapp_service)
        self.subscriptions = SubscriptionService(whatsapp_service)
        self.scheduling = SchedulingService(whatsapp_service)
        self.sending = SendingService(whatsapp_service)
        self.preferences = PreferenceService(whatsapp_service)
        self.history = HistoryService(whatsapp_service)

    # Métodos públicos delegan a sub-servicios
    async def get_template(self, db, template_id):
        return await self.templates.get_template(db, template_id)
```

## Compatibilidad

✅ **100% backward compatible** - Todos los imports y llamadas existentes siguen funcionando:

```python
# Esto sigue funcionando igual que antes
from app.services.notifications import NotificationService

notification_service = NotificationService(whatsapp_service)
await notification_service.get_template(db, template_id="...")
await notification_service.schedule_notification(...)
```

## Patrón Consistente

Esta modularización sigue el mismo patrón usado en otros servicios del proyecto:
- ✅ `app/services/sii/` - Servicios de SII
- ✅ `app/services/calendar/` - Servicios de calendario
- ✅ `app/services/notifications/` - Servicios de notificaciones (ahora)

## Testing

La arquitectura modular facilita el testing:

```python
# Antes: Difícil testear funcionalidad específica
# Después: Tests unitarios por módulo

def test_template_creation():
    template_service = TemplateService(mock_whatsapp)
    # Test solo la lógica de templates

def test_user_preferences():
    preference_service = PreferenceService(mock_whatsapp)
    # Test solo la lógica de preferencias
```

## Métricas

- **Líneas antes**: 1225 líneas en 1 archivo
- **Líneas después**: ~1295 líneas en 8 archivos (incluye documentación adicional)
- **Archivos creados**: 8 nuevos módulos
- **Archivos modificados**: 1 (service.py)
- **Archivos eliminados**: 0 (backward compatible)
- **Tests afectados**: 0 (API pública sin cambios)

## Próximos Pasos

1. Crear tests unitarios para cada módulo
2. Agregar métricas y observabilidad
3. Implementar límites de frecuencia en PreferenceService
4. Expandir analíticas en HistoryService
