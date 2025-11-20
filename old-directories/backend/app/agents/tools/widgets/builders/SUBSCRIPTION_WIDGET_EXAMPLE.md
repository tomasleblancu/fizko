# Subscription Upgrade Widget - Usage Example

## Overview

The subscription upgrade widget displays when a user tries to access a feature that requires a higher plan tier. It shows a professional card with plan information, benefits, and action buttons.

## Visual Structure

```
┌────────────────────────────────────────────────┐
│  🔒 Nómina                                    │
│  Esta funcionalidad está disponible           │
│  en el Plan Pro                                │
│                                                │
│  Plan actual: Starter                          │
│                                                │
│  ────────────────────────────────────────     │
│                                                │
│  Con el Plan Pro podrás:                       │
│    ✓ Gestión completa de empleados            │
│    ✓ Liquidaciones de sueldo automatizadas    │
│    ✓ Cálculo de imposiciones (AFP, Salud)     │
│    ✓ Contratos y finiquitos digitales         │
│    ✓ Reportes de nómina personalizados        │
│                                                │
│  ────────────────────────────────────────     │
│                                                │
│  [ Ver Planes ]  [ Más Tarde ]                │
└────────────────────────────────────────────────┘
```

## Usage in Supervisor Agent

When the supervisor detects a subscription block response:

```python
# Received blocking response from specialized agent
blocking_response = {
    "blocked": true,
    "blocked_item": "payroll",
    "display_name": "Nómina",
    "plan_required": "pro",
    "benefits": [
        "Gestión completa de empleados",
        "Liquidaciones de sueldo automatizadas",
        "Cálculo de imposiciones (AFP, Salud, AFC)",
        "Contratos y finiquitos digitales",
        "Reportes de nómina personalizados"
    ]
}

# Supervisor calls the widget tool
await show_subscription_upgrade(
    blocked_item="payroll",
    display_name="Nómina",
    plan_required="pro",
    benefits=[
        "Gestión completa de empleados",
        "Liquidaciones de sueldo automatizadas",
        "Cálculo de imposiciones (AFP, Salud, AFC)",
        "Contratos y finiquitos digitales",
        "Reportes de nómina personalizados"
    ]
)

# Then provides brief empathetic text
"Entiendo que necesitas ayuda con la gestión de tu personal.
He mostrado información sobre el Plan Pro que incluye esta funcionalidad.
¿Hay algo más en lo que pueda ayudarte? 😊"
```

## Button Actions

- **"Ver Planes"**: Opens `/configuracion/suscripcion` in the same window
- **"Más Tarde"**: Sends message "No, gracias. Prefiero continuar con mi plan actual."

## WhatsApp Fallback

For channels without widget support (like WhatsApp), the tool returns `copy_text`:

```
🔒 Nómina

Esta funcionalidad está disponible en el Plan Pro.
Tu plan actual: Starter

Con el Plan Pro podrás:
  ✓ Gestión completa de empleados
  ✓ Liquidaciones de sueldo automatizadas
  ✓ Cálculo de imposiciones (AFP, Salud, AFC)
  ✓ Contratos y finiquitos digitales
  ✓ Reportes de nómina personalizados

¿Te gustaría conocer más sobre los planes disponibles?
Puedes verlos en: Configuración > Suscripción
```

## Styling

- **Border**: Blue color to indicate informational nature
- **Padding**: Large for comfortable spacing
- **Buttons**: Primary (Ver Planes) and Secondary (Más Tarde)
- **Icons**: ✓ for benefits, 🔒 for locked feature
- **Dividers**: Separate sections for better readability

## Integration Points

1. **Supervisor Agent**: Detects blocking response and calls widget tool
2. **ChatKit UI**: Renders the widget with interactive buttons
3. **Settings Page**: Receives user when they click "Ver Planes"
4. **Analytics**: Can track upgrade widget impressions and clicks (future)
