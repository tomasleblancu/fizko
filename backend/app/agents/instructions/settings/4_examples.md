# Ejemplos de Uso

## Ejemplo 1: Listar notificaciones

**Usuario:** "Muéstrame mis notificaciones"

**Tú:** Utilizas `list_notifications` y muestras una lista clara del estado de cada notificación.

## Ejemplo 2: Desactivar todas las notificaciones

**Usuario:** "Desactiva todas las notificaciones"

**Tú:** Utilizas `edit_notification` con `action="disable_all"` y confirmas que todas las notificaciones han sido desactivadas.

## Ejemplo 3: Silenciar notificación específica

**Usuario:** "Quiero silenciar los recordatorios de F29"

**Tú:** Utilizas `edit_notification` con `action="mute"` y `template_name="F29"` para silenciar esa notificación específica.
