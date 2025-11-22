# Form29 Draft Generation Tasks

Este módulo contiene las tareas de Celery para la generación automatizada de drafts de F29 (declaración mensual de IVA).

## Tareas Disponibles

### 1. `generate_f29_drafts_all_companies`

Genera drafts de F29 para todas las empresas con suscripciones activas.

**Uso:**
```python
from app.infrastructure.celery.tasks.form29 import generate_f29_drafts_all_companies

# Generar drafts para mes anterior (auto-detect)
result = generate_f29_drafts_all_companies.delay()

# Generar drafts para período específico
result = generate_f29_drafts_all_companies.delay(
    period_year=2025,
    period_month=1,
    auto_calculate=True
)
```

**Retorna:**
```python
{
    "success": bool,
    "period_year": int,
    "period_month": int,
    "total_companies": int,
    "created": int,
    "skipped": int,
    "errors": int,
    "error_details": List[Dict],
    "execution_time_seconds": float
}
```

### 2. `generate_f29_draft_for_company`

Genera draft de F29 para una empresa específica.

**Uso:**
```python
from app.infrastructure.celery.tasks.form29 import generate_f29_draft_for_company

result = generate_f29_draft_for_company.delay(
    company_id="uuid-here",
    period_year=2025,
    period_month=10,
    auto_calculate=True
)
```

**Retorna:**
```python
{
    "success": bool,
    "company_id": str,
    "period_year": int,
    "period_month": int,
    "created": bool,
    "form29_id": str (opcional),
    "error": str (opcional),
    "execution_time_seconds": float
}
```

## Arquitectura

```
Celery Task (drafts.py)
    ↓
Form29DraftService (form29_draft_service.py)
    ↓
├─→ TaxSummaryService (tax_summary_service.py)
│   └─→ Obtiene IVA, PPM, retenciones, etc.
└─→ F29Repository (f29.py)
    └─→ CRUD de drafts en tabla form29
```

## Campos Calculados

Los drafts de F29 incluyen todos los campos necesarios para el widget de cálculo de impuesto:

### Ventas
- `total_sales`: Ventas totales (con IVA)
- `taxable_sales`: Ventas afectas (sin IVA)
- `exempt_sales`: Ventas exentas
- `sales_tax`: IVA débito fiscal (IVA cobrado)

### Compras
- `total_purchases`: Compras totales (con IVA)
- `taxable_purchases`: Compras afectas (sin IVA)
- `purchases_tax`: IVA crédito fiscal (IVA pagado)

### Cálculo de IVA
- `iva_to_pay`: IVA a pagar (= sales_tax)
- `iva_credit`: IVA crédito (= purchases_tax)
- `net_iva`: IVA neto (débito - crédito - crédito mes anterior + fuera de plazo)
- `previous_month_credit`: Crédito del mes anterior
- `overdue_iva_credit`: IVA fuera de plazo (no recuperable)

### Componentes Adicionales del Impuesto
- `ppm`: Pago Provisional Mensual (0.125% del ingreso neto)
- `retencion`: Retención de honorarios
- `reverse_charge_withholding`: Retención Cambio de Sujeto (código 46)
- `impuesto_trabajadores`: Impuesto de trabajadores (futuro)

## Migración de Base de Datos

**Importante:** Antes de ejecutar las tareas, aplicar la migración:

```bash
# Aplicar migración en Supabase
# Archivo: backend/supabase/migrations/20251122100000_add_tax_components_to_form29.sql
```

Esta migración agrega las columnas:
- `overdue_iva_credit`
- `ppm`
- `retencion`
- `reverse_charge_withholding`
- `impuesto_trabajadores`

## Programación con Celery Beat

Para ejecutar automáticamente cada mes:

```python
# En celery beat schedule
from celery.schedules import crontab

beat_schedule = {
    'generate-f29-drafts-monthly': {
        'task': 'form29.generate_drafts_all_companies',
        'schedule': crontab(day_of_month='1', hour='2', minute='0'),  # 1ro de cada mes a las 2am
        'args': (),  # Auto-detect previous month
    },
}
```

## Notas Importantes

1. **Revisiones**: Los drafts soportan múltiples revisiones por período. Si ya existe un draft, se crea una nueva revisión.

2. **Suscripciones**: Solo se procesan empresas con `subscriptions.status = 'active'`.

3. **Cálculo automático**: Por defecto, los valores se calculan automáticamente desde los documentos tributarios. Se puede desactivar con `auto_calculate=False`.

4. **Validación**: Los drafts se crean con `validation_status='pending'`. Se pueden validar posteriormente con `Form29DraftService.validate_draft()`.

5. **Estados del draft**:
   - `draft`: Borrador inicial
   - `validated`: Pasó validaciones
   - `confirmed`: Usuario confirmó, listo para enviar
   - `submitted`: Enviado al SII
   - `paid`: Pago confirmado
   - `cancelled`: Cancelado/supersedido

## Troubleshooting

### Error: "No companies with active subscriptions found"
**Solución:** Verificar que existan empresas con suscripciones activas en la tabla `subscriptions`.

### Error: "Missing column 'ppm'"
**Solución:** Ejecutar la migración `20251122100000_add_tax_components_to_form29.sql`.

### Draft con valores en 0
**Posibles causas:**
1. No existen documentos tributarios para el período
2. Los documentos no tienen `accounting_date` en el período
3. Error en el cálculo (revisar logs)

**Debug:**
```python
# Verificar que existen documentos
from app.services.tax_summary_service import TaxSummaryService

service = TaxSummaryService(supabase_client)
iva_summary = await service.get_iva_summary(company_id, "2025-01")
print(iva_summary)  # Ver sales_count, purchases_count
```
