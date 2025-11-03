# Notification Service Modules

Este directorio contiene los módulos especializados del servicio de notificaciones, organizados siguiendo el patrón de responsabilidad única.

## Estructura

```
modules/
├── __init__.py              # Exportaciones de módulos
├── base_service.py          # Servicio base con dependencias comunes
├── template_service.py      # Gestión de templates
├── subscription_service.py  # Gestión de suscripciones de empresas
├── scheduling_service.py    # Programación de notificaciones
├── sending_service.py       # Envío de notificaciones
├── preference_service.py    # Preferencias de usuario
└── history_service.py       # Historial y analíticas
```

## Módulos

### BaseNotificationService
Servicio base que provee dependencias comunes (WhatsAppService) para todos los módulos.

### TemplateService
Gestiona los templates de notificaciones:
- Crear, leer, actualizar, eliminar templates
- Listar templates con filtros
- Validación de templates

### SubscriptionService
Gestiona las suscripciones de empresas a templates:
- Suscribir/desuscribir empresas
- Configuración personalizada por empresa (timing, mensaje)
- Listar suscripciones

### SchedulingService
Maneja la programación de notificaciones:
- Calcular tiempos de envío (immediate, relative, absolute)
- Crear notificaciones programadas
- Renderizar mensajes con contexto
- Obtener notificaciones pendientes

### SendingService
Maneja el envío real de notificaciones:
- Verificar preferencias de usuario
- Enviar notificaciones por WhatsApp
- Registrar historial
- Anclar contexto a conversaciones
- Procesar lotes de notificaciones pendientes

### PreferenceService
Gestiona preferencias de notificaciones por usuario:
- Horarios de silencio (quiet hours)
- Días silenciados (quiet days)
- Categorías silenciadas
- Templates específicos silenciados
- Límites de frecuencia

### HistoryService
Gestiona el historial de notificaciones:
- Consultar historial con filtros
- Analíticas de envío
- Métricas de notificaciones

## Uso

El servicio principal `NotificationService` (en `service.py`) actúa como orquestador, delegando a estos módulos especializados:

```python
from app.services.notifications import NotificationService

# El servicio principal inicializa todos los sub-servicios
notification_service = NotificationService(whatsapp_service)

# Acceso a módulos especializados
notification_service.templates.create_template(...)
notification_service.subscriptions.subscribe_company(...)
notification_service.scheduling.schedule_notification(...)
notification_service.sending.send_scheduled_notification(...)
notification_service.preferences.update_user_preferences(...)
notification_service.history.get_notification_history(...)
```

## Ventajas de esta arquitectura

1. **Separación de responsabilidades**: Cada módulo tiene una responsabilidad clara y acotada
2. **Mantenibilidad**: Más fácil de entender, modificar y testear
3. **Escalabilidad**: Fácil agregar nuevos módulos sin afectar existentes
4. **Reutilización**: Módulos pueden usarse independientemente si es necesario
5. **Testing**: Más fácil crear tests unitarios para cada módulo
6. **Documentación**: Cada módulo está autocontenido y bien documentado

## Patrón similar

Esta estructura sigue el mismo patrón usado en otros servicios del proyecto:
- `app/services/sii/` - Servicios de SII modularizados
- `app/services/calendar/` - Servicios de calendario modularizados
