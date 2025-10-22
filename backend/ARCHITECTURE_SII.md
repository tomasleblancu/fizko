# Arquitectura del Módulo SII

## 🏗️ Diseño de Capas

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│              Llama a endpoints de FastAPI                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Routers (app/routers/)                  │
│     - Autenticación, validación, permisos                    │
│     - Usa dependency injection para obtener servicios        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           Service Layer (app/services/sii_service.py)        │
│  - Obtiene credenciales desde DB                             │
│  - Reutiliza cookies almacenadas                             │
│  - Maneja errores y reintentos                               │
│  - Guarda cookies actualizadas en DB                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│      Integration Layer (app/integrations/sii/)               │
│              ⚠️ AGNÓSTICO DE BASE DE DATOS ⚠️                 │
│  - SIIClient: Cliente principal                              │
│  - Authenticator: Login y cookies                            │
│  - Extractors: Contribuyente, DTEs, F29                      │
│  - Todo en MEMORIA (sin DB)                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  SII Portal (Selenium)                       │
│          Interacción con https://sii.cl                      │
└─────────────────────────────────────────────────────────────┘
```

## 📂 Estructura de Archivos

```
backend/
├── app/
│   ├── routers/
│   │   └── sii.py                    # Endpoints REST de FastAPI
│   │
│   ├── services/
│   │   └── sii_service.py           # ✅ CAPA DE SERVICIO (conecta SII con DB)
│   │
│   ├── integrations/
│   │   └── sii/                     # ✅ MÓDULO SII (agnóstico de DB)
│   │       ├── client.py            # Cliente principal
│   │       ├── core/                # Componentes core
│   │       ├── extractors/          # Extractores de datos
│   │       └── tests/               # Tests del módulo
│   │
│   └── models/
│       └── session.py               # Modelo DB de sesiones
```

## 🔄 Flujo de Datos

### Ejemplo: Extraer información del contribuyente

```python
# 1. Usuario hace request al frontend
GET /api/sii/contribuyente?session_id=123

# 2. Router recibe el request
# app/routers/sii.py
@router.get("/contribuyente")
async def get_contribuyente(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    # 3. Instanciar servicio
    service = SIIService(db)

    # 4. Servicio obtiene credenciales de DB y usa módulo SII
    info = await service.extract_contribuyente(session_id)

    # 5. Retornar resultado
    return info
```

### Flujo Interno del Servicio:

```python
# En SIIService.extract_contribuyente():

# 1. Obtener credenciales desde DB
creds = await self.get_stored_credentials(session_id)
# → SELECT * FROM sessions WHERE id = session_id

# 2. Usar módulo SII (AGNÓSTICO de DB)
with SIIClient(
    tax_id=creds["rut"],
    password=creds["password"],
    cookies=creds.get("cookies")  # Reutilizar cookies de DB
) as client:
    # 3. Login solo si no hay cookies
    if not creds.get("cookies"):
        client.login()
        new_cookies = client.get_cookies()

        # 4. Guardar cookies en DB
        await self.save_cookies(session_id, new_cookies)

    # 5. Extraer datos usando módulo SII
    info = client.get_contribuyente()

    # 6. Actualizar cookies en DB
    await self.save_cookies(session_id, client.get_cookies())

    return info
```

## 🎯 Uso desde Routers

### Ejemplo 1: Endpoint Simple

```python
# app/routers/sii.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.sii import SIIService
from app.database import get_db

router = APIRouter(prefix="/api/sii", tags=["SII"])

@router.get("/contribuyente")
async def get_contribuyente(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Obtiene información del contribuyente"""
    service = SIIService(db)
    return await service.extract_contribuyente(session_id)
```

### Ejemplo 2: Con Autenticación de Usuario

```python
from app.auth import get_current_user
from app.models import User

@router.get("/compras/{periodo}")
async def get_compras(
    periodo: str,
    tipo_doc: str = "33",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtiene DTEs de compra del período especificado"""

    # Obtener sesión activa del usuario
    session = await get_active_session(db, current_user.id)

    # Usar servicio
    service = SIIService(db)
    result = await service.extract_compras(
        session_id=session.id,
        periodo=periodo,
        tipo_doc=tipo_doc
    )

    return result
```

### Ejemplo 3: Con Background Task

```python
from fastapi import BackgroundTasks

@router.post("/sync")
async def sync_sii_data(
    session_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Sincroniza datos del SII en background"""

    async def sync_task():
        service = SIIService(db)

        # Extraer todo
        await service.extract_contribuyente(session_id)
        await service.extract_compras(session_id, "202510")
        await service.extract_ventas(session_id, "202510")
        await service.extract_f29_lista(session_id, "2024")

    background_tasks.add_task(sync_task)

    return {"status": "syncing", "session_id": session_id}
```

## 🔑 Ventajas de esta Arquitectura

### ✅ Separación de Responsabilidades

- **Módulo SII**: Solo se preocupa de interactuar con el SII
- **Servicio**: Maneja la lógica de negocio y persistencia
- **Router**: Maneja HTTP, validación, autenticación

### ✅ Testeable

- **Módulo SII**: Tests sin DB (como ya tienes)
- **Servicio**: Mock del DB en tests
- **Router**: Tests de integración completos

### ✅ Reutilizable

```python
# Usar en router
service = SIIService(db)
info = await service.extract_contribuyente(session_id)

# Usar en background task
async def my_task(db):
    service = SIIService(db)
    await service.extract_compras(session_id, periodo)

# Usar en CLI
async def cli_command():
    async with get_db_session() as db:
        service = SIIService(db)
        result = await service.extract_f29_lista(session_id, "2024")
```

### ✅ Manejo de Cookies Inteligente

1. **Primera vez**: Login → Guardar cookies en DB
2. **Siguientes veces**: Reutilizar cookies de DB (no RPA)
3. **Si cookies expiran**: Auto-retry con login fresco

## 🚀 Ejemplo Completo de Uso

```python
# Frontend hace request
const response = await fetch('/api/sii/compras/202510');
const data = await response.json();

# Backend (app/routers/sii.py)
@router.get("/compras/{periodo}")
async def get_compras(
    periodo: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Obtener sesión activa del usuario
    session = await get_user_active_session(db, current_user.id)

    # 2. Usar servicio
    service = SIIService(db)
    result = await service.extract_compras(
        session_id=session.id,
        periodo=periodo
    )

    # 3. El servicio:
    #    - Obtiene credenciales de DB
    #    - Reutiliza cookies de DB
    #    - Usa módulo SII (agnóstico)
    #    - Guarda cookies actualizadas
    #    - Retorna datos

    return result
```

## 📊 Diagrama de Secuencia

```
Usuario → Frontend → Router → Service → SII Module → SII Portal
                                  ↓
                                 DB
```

1. Usuario solicita datos
2. Router valida permisos
3. Service obtiene credenciales de DB
4. Service usa módulo SII con cookies de DB
5. Módulo SII extrae datos del portal
6. Service guarda cookies actualizadas en DB
7. Service retorna datos
8. Router retorna JSON al frontend

## 🎓 Mejores Prácticas

### ✅ DO

- Usar `SIIService` en routers y background tasks
- Guardar cookies en DB para reutilización
- Manejar errores en la capa de servicio
- Usar dependency injection

### ❌ DON'T

- No importar `SIIClient` directamente en routers
- No poner lógica de DB en el módulo SII
- No poner lógica de negocio en el módulo SII
- No crear clientes SII sin cerrarlos (usar `with`)

## 📝 Próximos Pasos

1. ✅ Módulo SII implementado (agnóstico de DB)
2. ✅ Service layer implementado
3. ⏳ Crear routers en `app/routers/sii.py`
4. ⏳ Implementar background tasks para sync
5. ⏳ Agregar caching de datos extraídos
6. ⏳ Implementar rate limiting para SII

---

**Nota**: El módulo SII (`app/integrations/sii/`) NUNCA debe importar nada de `app.models`, `app.database`, o `sqlalchemy`. Debe permanecer 100% agnóstico de la base de datos.
