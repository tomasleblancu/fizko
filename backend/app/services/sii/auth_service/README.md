# SII Auth Service (Modularizado)

Servicio de autenticación con el SII y setup inicial de empresas, organizado en módulos especializados para mejor mantenibilidad.

## Estructura

```
auth_service/
├── __init__.py           # Clase principal SIIAuthService
├── sii_auth.py          # Autenticación con el SII
├── setup.py             # Setup de Company, Tax Info, Session y Profile
├── memories.py          # Gestión de memorias en Mem0
├── events.py            # Eventos tributarios y notificaciones
└── README.md            # Este archivo
```

## Módulos

### `__init__.py` - Clase Principal

**Clase:** `SIIAuthService`

Orquesta el flujo completo de autenticación y setup:

1. ✅ Crear perfil de usuario
2. 🔐 Autenticar con el SII
3. 🏢 Setup de Company
4. 📋 Setup de CompanyTaxInfo
5. 🔑 Setup de Session
6. 📅 Activar eventos obligatorios
7. 🔔 Asignar notificaciones automáticas
8. 🧠 Guardar memorias en Mem0
9. 🚀 Disparar tareas de sincronización

**Uso:**
```python
from app.services.sii.auth_service import SIIAuthService

service = SIIAuthService(db)
result = await service.login_and_setup(
    rut="12345678-9",
    password="password",
    user_id=user_id,
    user_data=user_data
)
```

---

### `sii_auth.py` - Autenticación SII

**Función:** `authenticate_sii(rut, password)`

Maneja la autenticación con el SII usando Selenium:
- Login con credenciales
- Extracción de información del contribuyente (incluye datos extendidos: cumplimiento, observaciones, representantes, socios, timbrajes)
- Obtención de cookies de sesión

**Returns:**
```python
{
    "contribuyente_info": dict,  # Información completa del contribuyente
    "cookies": list              # Cookies de sesión SII
}
```

---

### `setup.py` - Setup de Entidades

Funciones para crear/actualizar entidades de base de datos:

#### `ensure_profile(db, user_id, user_data)`
Crea o retorna el perfil del usuario.

#### `setup_company(db, rut, password, sii_data)`
Crea o actualiza la compañía.

**Returns:** `(Company, action)` donde action es "creada" o "actualizada"

#### `setup_tax_info(db, company_id, sii_data)`
Crea o actualiza la información tributaria.

**Returns:** `(CompanyTaxInfo, action)`

#### `setup_session(db, user_id, company_id, password, sii_cookies)`
Crea o actualiza la sesión del usuario con la compañía.

**Returns:** `(Session, action)`

#### `check_needs_initial_setup(db, company_id)`
Verifica si la empresa necesita configuración inicial.

**Returns:** `bool`

---

### `memories.py` - Gestión de Memorias

**Función:** `save_onboarding_memories(...)`

Guarda información en Mem0 para uso de los agentes AI:

#### Memorias de Empresa (12 tipos)

1. **company_basic_info** - Información básica (RUT, nombre)
2. **company_tax_regime** - Régimen tributario
3. **company_activity** - Actividad económica principal
4. **company_start_date** - Fecha de inicio de actividades
5. **company_address** - Dirección registrada
6. **company_fizko_join_date** - Fecha de incorporación a Fizko
7. **company_tax_compliance_status** - Estado de cumplimiento tributario
8. **company_tax_compliance_issues** - Incumplimientos (si los hay)
9. **company_sii_alerts** - Observaciones y alertas del SII
10. **company_legal_representatives** - Representantes legales
11. **company_shareholders** - Socios y composición societaria
12. **company_authorized_documents** - Documentos autorizados (timbrajes)

#### Memorias de Usuario (3 tipos)

1. **user_company_join_{company_id}** - Vinculación con empresa
2. **user_role_{company_id}** - Rol en la empresa
3. **user_full_name** / **user_phone** - Información del perfil

**Sistema de UPDATE/CREATE:**
- Si ya existe una memoria con el mismo slug, se actualiza
- Si no existe, se crea nueva
- Usa CompanyBrain y UserBrain para rastrear memorias

---

### `events.py` - Eventos y Notificaciones

#### `activate_mandatory_events(db, company_id)`
Activa todos los eventos tributarios obligatorios para la empresa.

**Returns:** `List[str]` - Códigos de eventos activados

#### `assign_auto_notifications(db, company_id, is_new_company)`
Asigna notificaciones con auto-asignación activada (solo para empresas nuevas).

**Returns:** `List[str]` - Códigos de notificaciones asignadas

#### `trigger_sync_tasks(company_id)`
Dispara tareas de Celery en background:
- sync_company_calendar
- sync_documents (últimos 3 meses)
- sync_f29 (año actual)

---

## Flujo de Ejecución

```
┌─────────────────────────────────────────┐
│ 1. ensure_profile()                     │
│    Crear perfil si no existe            │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ 2. authenticate_sii()                   │
│    Login + extracción de datos SII      │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ 3. setup_company()                      │
│    Crear/actualizar Company             │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ 4. setup_tax_info()                     │
│    Crear/actualizar CompanyTaxInfo      │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ 5. setup_session()                      │
│    Crear/actualizar Session             │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ 6. activate_mandatory_events()          │
│    Activar eventos tributarios          │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ 7. assign_auto_notifications()          │
│    Asignar notificaciones (solo nuevas) │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ 8. db.commit() + refresh()              │
│    Guardar todos los cambios            │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ 9. save_onboarding_memories()           │
│    Guardar en Mem0 para AI              │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ 10. trigger_sync_tasks()                │
│     Disparar Celery (solo nuevas)       │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ 11. check_needs_initial_setup()         │
│     Verificar si necesita setup         │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ 12. _build_response()                   │
│     Construir respuesta JSON            │
└─────────────────────────────────────────┘
```

---

## Beneficios de la Modularización

### ✅ Separación de Responsabilidades
Cada módulo tiene una responsabilidad clara y específica.

### ✅ Mantenibilidad
Es más fácil encontrar y modificar código relacionado con una funcionalidad específica.

### ✅ Testabilidad
Cada módulo puede testearse de forma independiente.

### ✅ Reutilización
Las funciones pueden usarse en otros contextos sin importar toda la clase.

### ✅ Legibilidad
El código es más fácil de entender al estar organizado por dominio.

### ✅ Escalabilidad
Agregar nuevas funcionalidades es más simple sin afectar otros módulos.

---

## Debugging

Para debugging de módulos específicos, ajustar el nivel de log:

```python
import logging

# Log específico por módulo
logging.getLogger("app.services.sii.auth_service.memories").setLevel(logging.DEBUG)
logging.getLogger("app.services.sii.auth_service.events").setLevel(logging.DEBUG)
```

Cada módulo usa su propio logger:
- `[SII Auth Service]` - Clase principal
- `[Setup]` - Módulo setup
- `[Memories]` - Módulo memories
- `[Events]` - Módulo events

---

## Desarrollo

### Agregar Nueva Funcionalidad

1. **Identificar el módulo apropiado** (o crear uno nuevo)
2. **Agregar la función** al módulo
3. **Importar en `__init__.py`** si es necesario
4. **Invocar desde `login_and_setup()`**
5. **Documentar en este README**

### Ejemplo: Agregar Nueva Memoria

```python
# En memories.py
def _add_extended_sii_memories(memories, contribuyente_info):
    # Agregar nueva memoria
    nueva_info = contribuyente_info.get('nueva_info')
    if nueva_info:
        memories.append({
            "slug": "company_nueva_info",
            "category": "company_info",
            "content": f"Nueva información: {nueva_info}"
        })
```

---

## Referencias

- **Router que usa este servicio:** [app/routers/sii/auth.py](../../routers/sii/auth.py)
- **Integración SII:** [app/integrations/sii/](../../integrations/sii/)
- **Modelos de datos:** [app/db/models/](../../db/models/)
- **Repositorios de Brain:** [app/repositories/brain.py](../../repositories/brain.py)
