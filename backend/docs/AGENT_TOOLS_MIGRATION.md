# Agent Tools Migration to Supabase Repositories

Este documento guía la migración de todos los agent tools desde SQLAlchemy a Supabase con patrón de repositorios.

## Patrón de Migración

### Antes (SQLAlchemy)
```python
from sqlalchemy import select, and_
from app.config.database import AsyncSessionLocal
from app.db.models import SalesDocument

async with AsyncSessionLocal() as session:
    stmt = select(SalesDocument).where(
        and_(
            SalesDocument.company_id == UUID(company_id),
            SalesDocument.folio == folio
        )
    )
    result = await session.execute(stmt)
    doc = result.scalar_one_or_none()
```

### Después (Repositorios Supabase)
```python
from app.agents.tools.utils import get_supabase

supabase = get_supabase()
doc = await supabase.documents.get_sales_document(document_id)
```

## Repositorios Disponibles

### 1. ContactsRepository
**Acceso**: `supabase.contacts`

**Métodos**:
- `get_by_rut(company_id, rut)` - Obtener contacto por RUT
- `get_by_id(contact_id)` - Obtener contacto por ID
- `get_sales_summary(contact_id)` - Resumen de ventas
- `get_purchase_summary(contact_id)` - Resumen de compras
- `get_top_clients(company_id, limit=5)` - Top clientes
- `get_top_providers(company_id, limit=5)` - Top proveedores

### 2. DocumentsRepository
**Acceso**: `supabase.documents`

**Métodos**:
- `get_sales_document(document_id, include_contact=True)` - Documento de venta
- `get_purchase_document(document_id, include_contact=True)` - Documento de compra
- `search_documents(company_id, document_type, rut, folio, start_date, end_date, limit)` - **Búsqueda avanzada**
- `get_recent_sales(company_id, limit=10)` - Ventas recientes
- `get_recent_purchases(company_id, limit=10)` - Compras recientes
- `get_documents_by_type(company_id, document_type, tipo_dte, limit)` - Por tipo de DTE

### 3. TaxSummariesRepository
**Acceso**: `supabase.tax_summaries`

**Métodos**:
- `get_tax_summary(company_id, period)` - Resumen completo (IVA + ingresos + gastos)
- `get_iva_summary(company_id, period)` - Resumen IVA
- `get_revenue_summary(company_id, period)` - Resumen ingresos
- `get_expense_summary(company_id, period)` - Resumen gastos
- `get_monthly_revenue_trend(company_id, months=6)` - Tendencia mensual

### 4. ExpensesRepository
**Acceso**: `supabase.expenses`

**Métodos**:
- `create(company_id, ...)` - Crear gasto
- `list(company_id, status, category, date_from, date_to, limit, offset)` - Listar gastos
- `get_summary(company_id, date_from, date_to, category, status)` - Resumen
- `get_by_id(expense_id)` - Obtener por ID

### 5. F29Repository
**Acceso**: `supabase.f29`

**Métodos**:
- `get_form_by_id(form_id)` - Formulario por ID
- `get_forms_by_company(company_id, limit, status)` - Formularios de empresa
- `get_form_by_period(company_id, period)` - Por período (YYYYMM)
- `get_latest_form(company_id)` - Formulario más reciente
- `get_pending_forms(company_id, limit)` - Pendientes
- `get_overdue_forms(company_id, limit)` - Vencidos
- `get_payment_history(company_id, limit)` - Historial de pagos

### 6. PeopleRepository
**Acceso**: `supabase.people`

**Métodos**:
- `get_person_by_id(person_id)` - Persona por ID
- `get_person_by_rut(company_id, rut)` - Persona por RUT
- `get_people_by_company(company_id, status, limit)` - Personas de empresa
- `get_active_employees(company_id, limit)` - Empleados activos
- `get_employee_count(company_id)` - Conteo de empleados
- `get_payroll_summary(company_id, period)` - Resumen de nómina
- `search_people(company_id, query, limit)` - Buscar personas

### 7. NotificationsRepository
**Acceso**: `supabase.notifications`

**Métodos**:
- `get_by_id(notification_id, include_template)` - Por ID
- `get_by_company(company_id, limit, status)` - Por empresa
- `get_pending(company_id, limit)` - Pendientes
- `get_template_by_code(template_code)` - Plantilla por código
- `get_all_templates()` - Todas las plantillas
- `get_recent_by_template(company_id, template_code, limit)` - Por plantilla

### 8. CalendarRepository
**Acceso**: `supabase.calendar`

**Métodos**:
- `get_event_by_id(event_id, include_template, include_tasks, include_history)` - Evento por ID
- `get_events_by_company(company_id, limit, status, include_template)` - Eventos de empresa
- `get_upcoming_events(company_id, days_ahead, limit)` - Próximos eventos
- `get_event_template_by_code(template_code)` - Plantilla por código
- `get_all_event_templates()` - Todas las plantillas
- `get_event_tasks(event_id)` - Tareas del evento
- `get_event_history(event_id, limit)` - Historial del evento

### 9. CompaniesRepository
**Acceso**: `supabase.companies`

**Métodos**:
- `get_by_id(company_id)` - Empresa por ID
- `get_by_rut(rut)` - Empresa por RUT
- `get_all(limit)` - Todas las empresas
- `search_by_name(query, limit)` - Buscar por nombre

## Guía de Migración por Tool

### 1. documentos_tributarios_tools.py ✅ COMPLETADO

**Cambios**:
```python
# ANTES
from app.config.database import AsyncSessionLocal
from app.db.models import PurchaseDocument, SalesDocument

async with AsyncSessionLocal() as session:
    purchase_stmt = select(PurchaseDocument).where(...)
    # ... 50+ líneas de queries

# DESPUÉS
from app.agents.tools.utils import get_supabase

supabase = get_supabase()
doc_results = await supabase.documents.search_documents(
    company_id=company_id,
    document_type=document_type,
    rut=rut,
    folio=folio,
    start_date=start_date,
    end_date=end_date,
    limit=limit
)
```

**Líneas reducidas**: ~130 → ~100

### 2. expense_tools.py ✅ COMPLETADO

**Repositorio necesario**: ✅ `ExpensesRepository` creado

**Tools migrados**:
- `create_expense()` - Usa `supabase.expenses.create()`
- `get_expenses()` - Usa `supabase.expenses.list()`
- `get_expense_summary()` - Usa `supabase.expenses.get_summary()`

**Patrón**:
```python
# ANTES
from app.config.database import AsyncSessionLocal
from app.repositories.expenses import ExpenseRepository  # SQLAlchemy

async with AsyncSessionLocal() as session:
    repo = ExpenseRepository(session)
    expense = await repo.create(...)

# DESPUÉS
from app.agents.tools.utils import get_supabase

supabase = get_supabase()
expense = await supabase.expenses.create(
    company_id=company_id,
    created_by_user_id=user_id,
    expense_category=category,
    ...
)
```

### 3. f29_tools.py ✅ COMPLETADO (solo limpieza)

**Estado**: Solo contenía funciones de cálculo matemático (IVA, PPM), sin acceso a DB.

**Cambios**: Eliminado import innecesario de `AsyncSessionLocal`

**Ejemplo**:
```python
supabase = get_supabase()

# Get all forms
forms = await supabase.f29.get_forms_by_company(
    company_id=company_id,
    limit=12,
    status="pending"
)

# Get by period
form = await supabase.f29.get_form_by_period(
    company_id=company_id,
    period="202501"
)
```

### 4. payroll_tools.py ✅ COMPLETADO

**Repositorio extendido**: ✅ `PeopleRepository` - Agregados métodos `create()` y `update()`

**Tools migrados**:
- `get_people()` - Usa `supabase.people.get_people_by_company()`
- `get_person()` - Usa `supabase.people.get_person_by_id()` y `get_person_by_rut()`
- `create_person()` - Usa `supabase.people.create()`
- `update_person()` - Usa `supabase.people.update()`

**Mejoras**:
- ~494 líneas reducidas a código más limpio
- Eliminadas dependencias SQLAlchemy (select, UUID, AsyncSessionLocal)
- Mejor manejo de campos opcionales con helper `to_float()`

**Ejemplo**:
```python
supabase = get_supabase()

# Get employees
employees = await supabase.people.get_active_employees(
    company_id=company_id,
    limit=100
)

# Get person by RUT
person = await supabase.people.get_person_by_rut(
    company_id=company_id,
    rut="12345678-9"
)
```

### 5. notification_tools.py ⏳ PENDIENTE

**Tools a migrar**:
- `get_notifications()` - Usar `supabase.notifications.get_by_company()`
- `get_pending_notifications()` - Usar `supabase.notifications.get_pending()`

**Ejemplo**:
```python
supabase = get_supabase()

# Get company notifications
notifications = await supabase.notifications.get_by_company(
    company_id=company_id,
    limit=50,
    status="pending"
)

# Get pending only
pending = await supabase.notifications.get_pending(
    company_id=company_id,
    limit=100
)
```

### 6. sii_general_tools.py ✅ COMPLETADO

**Repositorio extendido**: ✅ `CompaniesRepository` - Agregado join con `company_tax_info`

**Tools migrados**:
- `get_company_info()` - Usa `supabase.companies.get_by_id(include_tax_info=True)`

**Mejoras**:
- Eliminadas dependencias SQLAlchemy (select, UUID, AsyncSessionLocal)
- Join automático con `company_tax_info` en el repositorio

### 7. remuneraciones_tools.py ✅ COMPLETADO (solo limpieza)

**Estado**: Solo contenía funciones de cálculo de nómina (salario, AFP, impuestos), sin acceso a DB.

**Cambios**: Eliminado import innecesario de `AsyncSessionLocal`

### 8. operacion_renta_tools.py ✅ COMPLETADO (ya limpio)

**Estado**: Solo contenía funciones de cálculo fiscal anual. Ya no tenía imports de SQLAlchemy.

## Widget Tools

Los widget tools probablemente necesiten migración también. Revisar:

- `tax_widget_tools.py` → Usar `supabase.tax_summaries`, `supabase.documents`
- `payroll_widget_tools.py` → Usar `supabase.people`
- `subscription_widget_tools.py` → Probablemente no necesita DB

## Feedback Tools

`feedback_tools.py` usa tabla `feedback` que podría no estar en Supabase aún.

**Opciones**:
1. Crear `FeedbackRepository` si la tabla existe
2. Migrar tabla feedback a Supabase
3. Dejar como está si es solo local

## Checklist de Migración

Para cada tool file:

- [ ] **1. Leer archivo actual**
  ```bash
  cat backend-v2/app/agents/tools/[category]/[file].py
  ```

- [ ] **2. Identificar queries SQLAlchemy**
  - Buscar `AsyncSessionLocal`
  - Buscar `select()`, `and_()`, `desc()`
  - Buscar modelos importados (`from app.db.models import ...`)

- [ ] **3. Mapear a repositorios**
  - ¿Qué repositorio necesita?
  - ¿Los métodos ya existen?
  - ¿Necesita extender el repositorio?

- [ ] **4. Actualizar imports**
  ```python
  # Remover
  from app.config.database import AsyncSessionLocal
  from app.db.models import ...
  from sqlalchemy import ...

  # Agregar
  from app.agents.tools.utils import get_supabase
  ```

- [ ] **5. Reemplazar código**
  ```python
  # Remover
  async with AsyncSessionLocal() as session:
      # queries...

  # Agregar
  supabase = get_supabase()
  result = await supabase.[repository].[method](...)
  ```

- [ ] **6. Ajustar formato de respuesta**
  - Repositorios retornan `dict` en vez de objetos ORM
  - Usar `.get()` en vez de acceso directo a atributos
  - Manejar `None` defensivamente

- [ ] **7. Probar**
  - Verificar sintaxis Python
  - Probar con datos reales si es posible

## Ejemplo Completo de Migración

### Archivo: `get_documents` en `documentos_tributarios_tools.py`

**ANTES** (~130 líneas):
```python
from sqlalchemy import select, and_, desc
from app.config.database import AsyncSessionLocal
from app.db.models import PurchaseDocument, SalesDocument

@function_tool(strict_mode=False)
async def get_documents(...) -> dict[str, Any]:
    async with AsyncSessionLocal() as session:
        # Query purchases
        purchase_conditions = [PurchaseDocument.company_id == UUID(company_id)]
        if rut:
            purchase_conditions.append(PurchaseDocument.sender_rut == rut)
        if folio:
            purchase_conditions.append(PurchaseDocument.folio == folio)
        if start_dt:
            purchase_conditions.append(PurchaseDocument.issue_date >= start_dt)

        purchase_stmt = (
            select(PurchaseDocument)
            .where(and_(*purchase_conditions))
            .order_by(desc(PurchaseDocument.issue_date))
            .limit(min(limit, 100))
        )

        purchase_result = await session.execute(purchase_stmt)
        purchases = purchase_result.scalars().all()

        # Process purchases...
        results["purchase_documents"] = [
            {
                "id": str(doc.id),
                "document_type": doc.document_type,
                # ... 10+ fields
            }
            for doc in purchases
        ]

        # Same for sales (another 50 lines)...
```

**DESPUÉS** (~100 líneas):
```python
from app.agents.tools.utils import get_supabase

@function_tool(strict_mode=False)
async def get_documents(...) -> dict[str, Any]:
    supabase = get_supabase()

    # Single call to repository
    doc_results = await supabase.documents.search_documents(
        company_id=company_id,
        document_type=document_type,
        rut=rut,
        folio=folio,
        start_date=start_date,
        end_date=end_date,
        limit=min(limit, 100)
    )

    # Process results
    purchases = doc_results.get("purchase_documents", [])
    sales = doc_results.get("sales_documents", [])

    # Format for agent
    results["purchase_documents"] = [
        {
            "id": doc.get("id"),
            "document_type": doc.get("document_type") or doc.get("tipo_dte"),
            # ... handle field variations
        }
        for doc in purchases
    ]
```

**Beneficios**:
- ✅ 30% menos código
- ✅ Sin imports de SQLAlchemy
- ✅ Sin manejo de sesiones
- ✅ Más legible
- ✅ Lógica de DB centralizada en repositorio

## Recursos

- **Repositorios**: [backend-v2/app/repositories/](../app/repositories/)
- **SupabaseClient**: [backend-v2/app/config/supabase.py](../app/config/supabase.py)
- **Utils**: [backend-v2/app/agents/tools/utils.py](../app/agents/tools/utils.py)
- **Documentación**: [backend-v2/docs/UI_TOOLS_SUPABASE.md](UI_TOOLS_SUPABASE.md)

## Próximos Pasos

1. ✅ **Completado**: `documentos_tributarios_tools.py`
2. ✅ **Completado**: `expense_tools.py`
3. ✅ **Completado**: `f29_tools.py` (limpieza)
4. ✅ **Completado**: `payroll_tools.py`
5. ✅ **Completado**: `sii_general_tools.py`
6. ✅ **Completado**: `remuneraciones_tools.py` (limpieza)
7. ✅ **Completado**: `operacion_renta_tools.py` (ya limpio)
8. ⏳ **Pendiente**: `notification_tools.py` (requiere migrar `notification_service` primero)
9. ⏳ **Pendiente**: Widget tools
10. ⏳ **Pendiente**: `feedback_tools.py` (si tiene tabla en Supabase)

### 10. FeedbackRepository ✅ NUEVO
**Acceso**: `supabase.feedback`

**Métodos**:
- `create(profile_id, category, priority, title, feedback, ...)` - Crear feedback
- `update(feedback_id, **kwargs)` - Actualizar feedback
- `get_by_id(feedback_id, profile_id)` - Obtener por ID
- `list_by_profile(profile_id, status, limit)` - Listar por usuario

