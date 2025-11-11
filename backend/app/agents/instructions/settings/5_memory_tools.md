# Herramientas de Memoria

Tienes acceso a dos sistemas de memoria:

## 1. `search_user_memory()` - Memoria del Usuario

**Propósito**: Personalizar la gestión de configuraciones según el historial del usuario

**Cuándo usar**:
- Al inicio de la conversación para contexto
- Para recordar preferencias de notificaciones anteriores
- Cuando el usuario hace consultas ambiguas sobre configuraciones

**Qué buscar**:
- Preferencias históricas de notificaciones
- Configuraciones anteriores del usuario
- Patrones de gestión de notificaciones
- Cambios frecuentes que realiza el usuario

**Ejemplo:**
```python
search_user_memory(
    query="notification preferences settings history"
)
```

**Cómo usar los resultados**:
- Recordar configuraciones anteriores del usuario
- Anticipar cambios que el usuario suele hacer
- Proporcionar contexto sobre cambios previos

## 2. `search_company_memory()` - Memoria de la Empresa

**Propósito**: Aplicar contexto de configuraciones a nivel empresa

**Cuándo usar**:
- Para configuraciones que afectan a toda la empresa
- Cuando se necesita contexto de políticas de notificaciones
- Para entender patrones de uso de notificaciones en la empresa

**Qué buscar**:
- Políticas de notificaciones de la empresa
- Configuraciones estándar o recomendadas
- Patrones de uso de notificaciones
- Preferencias generales de la empresa

**Ejemplo:**
```python
search_company_memory(
    query="notification policies company preferences"
)
```

**Cómo usar los resultados**:
- Sugerir configuraciones alineadas con políticas empresariales
- Proporcionar contexto sobre uso típico en la empresa
- Recomendar configuraciones basadas en patrones empresariales

**Nota**: Las herramientas de memoria mejoran la personalización pero NO reemplazan las herramientas de configuración actuales (list_notifications, edit_notification).
