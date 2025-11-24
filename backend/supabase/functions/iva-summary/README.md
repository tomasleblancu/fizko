# IVA Summary Edge Function

Edge function de Supabase que replica la funcionalidad del `TaxSummaryService` de Next.js.

## Descripción

Esta función calcula el resumen de IVA para una empresa en un período específico, incluyendo:

- **Total Revenue**: Ingresos totales del período
- **Total Expenses**: Gastos totales del período
- **IVA Collected**: IVA de ventas neto (después de notas de crédito)
- **IVA Paid**: IVA de compras neto (después de notas de crédito)
- **Net IVA**: Balance de IVA (collected - paid)
- **Previous Month Credit**: Del F29 del mes anterior
- **Overdue IVA Credit**: IVA que no puede recuperarse
- **PPM**: Pago Provisional Mensual (0.125% de ingresos netos)
- **Retención**: De boletas de honorarios
- **Reverse Charge Withholding**: Retención Cambio de Sujeto (Código 46)
- **Monthly Tax**: Impuesto mensual total a pagar
- **Generated F29**: Formulario 29 generado para el período
- **Form29 SII Download**: Formulario 29 descargado del SII

## Request

Soporta tanto GET como POST:

### GET Request
```bash
GET /functions/v1/iva-summary?companyId=uuid-here&period=2025-10
Authorization: Bearer <JWT_TOKEN>
```

### POST Request
```typescript
POST /functions/v1/iva-summary
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>

{
  "company_id": "uuid-here",
  "period": "2025-10"  // Opcional, formato YYYY-MM
}
```

## Response

El formato de respuesta coincide exactamente con el endpoint de Next.js `/api/tax-summary`:

```typescript
{
  "id": "company-id-2025-10",
  "company_id": "uuid-here",
  "period_start": "2025-10-01T00:00:00.000Z",
  "period_end": "2025-11-01T00:00:00.000Z",
  "total_revenue": 10000000,
  "total_expenses": 5000000,
  "iva_collected": 1900000,
  "iva_paid": 950000,
  "net_iva": 950000,
  "income_tax": 0,
  "previous_month_credit": null,
  "overdue_iva_credit": 0,
  "ppm": 625,
  "retencion": 12250,
  "reverse_charge_withholding": null,
  "impuesto_trabajadores": null,
  "monthly_tax": 962875,
  "generated_f29": {
    "id": "...",
    "company_id": "...",
    "period_year": 2025,
    "period_month": 10,
    "total_sales": 11900000,
    "taxable_sales": 10000000,
    "exempt_sales": 0,
    "sales_tax": 1900000,
    "total_purchases": 5950000,
    "taxable_purchases": 5000000,
    "purchases_tax": 950000,
    "iva_to_pay": 950000,
    "iva_credit": 0,
    "net_iva": 950000,
    "status": "saved",
    "extra_data": null,
    "submitted_at": null,
    "created_at": "2025-10-15T10:30:00.000Z",
    "updated_at": "2025-10-15T10:30:00.000Z"
  },
  "form29_sii_download": null,
  "created_at": "2025-10-15T12:00:00.000Z",
  "updated_at": "2025-10-15T12:00:00.000Z"
}
```

## Deployment

### Opción 1: Usando Supabase CLI

```bash
cd backend

# Deploy la función
supabase functions deploy iva-summary

# Ver logs
supabase functions logs iva-summary
```

### Opción 2: Usando el MCP de Supabase

Si tienes el MCP de Supabase configurado en Claude Code, puedes deployar los archivos directamente.

## Testing Local

Requiere Deno instalado:

```bash
# Instalar Deno
brew install deno  # macOS
# o seguir instrucciones en https://deno.land/

# Servir localmente
cd backend
supabase functions serve iva-summary

# Hacer request de prueba (GET)
curl "http://localhost:54321/functions/v1/iva-summary?companyId=4dd964b5-7718-452a-8c41-39d993de5d6d&period=2025-10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Hacer request de prueba (POST)
curl -X POST http://localhost:54321/functions/v1/iva-summary \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "4dd964b5-7718-452a-8c41-39d993de5d6d",
    "period": "2025-10"
  }'
```

## Testing en Producción

```bash
# Usando el endpoint de Supabase
curl "https://your-project.supabase.co/functions/v1/iva-summary?companyId=4dd964b5-7718-452a-8c41-39d993de5d6d&period=2025-10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Ventajas sobre el endpoint Python/FastAPI

1. **Rendimiento**: Ejecuta más cerca de la base de datos
2. **Escalabilidad**: Auto-escala con tráfico
3. **Costo**: Pay-per-execution (no siempre corriendo)
4. **Latencia**: Menor latencia al evitar saltos de red
5. **Deployment**: Deploy independiente del backend principal
6. **Compatible**: Mismo formato de respuesta que Next.js endpoint

## Lógica de Negocio

### Documentos de Ventas (IVA Collected)

**Positivos:**
- factura_venta
- boleta
- boleta_exenta
- factura_exenta
- comprobante_pago
- liquidacion_factura
- nota_debito_venta

**Negativos (restan):**
- nota_credito_venta

### Documentos de Compras (IVA Paid)

**Positivos:**
- factura_compra
- factura_exenta_compra
- liquidacion_factura
- nota_debito_compra
- declaracion_ingreso

**Negativos (restan):**
- nota_credito_compra

### Cálculos Especiales

- **PPM**: `net_revenue * 0.00125` (0.125%)
- **IVA fuera de plazo**: Suma de `overdue_iva_credit` de todos los documentos
- **Crédito anterior**: Busca en `form29` (saved/paid) o `form29_sii_downloads` (Vigente)
- **Retención**: Suma de `recipient_retention` de `honorarios_receipts` tipo "received"
- **Retención Cambio de Sujeto**: Suma de `tax_amount` de `purchase_documents` con código 46
- **Monthly Tax**: Fórmula chilena: `max(0, iva_collected - iva_paid - previous_month_credit) + overdue_iva_credit + ppm + retencion + reverse_charge_withholding`

## Autenticación

Usa JWT de Supabase Auth. La función valida que:
1. El header `Authorization` esté presente
2. El token sea válido
3. El usuario esté autenticado

## Environment Variables

La función usa las siguientes variables (auto-configuradas en Supabase):
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

## Comparación con Next.js Service

Esta función replica exactamente la lógica de:
- `frontend/src/services/tax/tax-summary.service.ts:TaxSummaryService.calculateSummary()`

**Formato de respuesta idéntico** al endpoint de Next.js:
- `frontend/src/app/api/tax-summary/route.ts`

Diferencias:
- **Lenguaje**: TypeScript/Deno vs TypeScript/Next.js
- **Ejecución**: Supabase Edge runtime vs Next.js API routes
- **Dependencias**: Supabase client nativo vs Supabase client + Next.js
- **Performance**: ~50-100ms vs ~200-500ms (estimado)
- **Deployment**: Supabase vs Vercel

## Files Structure

```
iva-summary/
├── index.ts           # Main handler (GET & POST support)
├── types.ts           # TypeScript interfaces
├── calculations.ts    # IVA calculation logic
├── documents.ts       # Database query functions
├── helpers.ts         # Utility functions
├── example-usage.ts   # Usage examples
└── README.md          # This file
```
