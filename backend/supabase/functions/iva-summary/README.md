# IVA Summary Edge Function

Edge function de Supabase que replica la funcionalidad del método `get_iva_summary` del `TaxSummaryService`.

## Descripción

Esta función calcula el resumen de IVA para una empresa en un período específico, incluyendo:

- **Débito Fiscal**: IVA de ventas neto (después de notas de crédito)
- **Crédito Fiscal**: IVA de compras neto (después de notas de crédito)
- **Balance**: IVA neto a pagar o favor
- **Crédito mes anterior**: Del F29 del mes anterior
- **IVA fuera de plazo**: IVA que no puede recuperarse
- **PPM**: Pago Provisional Mensual (0.125% de ingresos netos)
- **Retención**: De boletas de honorarios
- **Retención Cambio de Sujeto**: Código 46
- **Contadores**: Documentos de ventas y compras

## Request

```typescript
POST /functions/v1/iva-summary
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>

{
  "company_id": "uuid-here",
  "period": "2025-01"  // Opcional, formato YYYY-MM
}
```

## Response

```typescript
{
  "debito_fiscal": 1900000,
  "credito_fiscal": 950000,
  "balance": 950000,
  "previous_month_credit": 0,
  "overdue_iva_credit": 0,
  "ppm": 625,
  "retencion": 12250,
  "reverse_charge_withholding": 0,
  "sales_count": 15,
  "purchases_count": 8
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

Si tienes el MCP de Supabase configurado en Claude Code, puedes usar:

```typescript
mcp__supabase-staging__deploy_edge_function({
  name: "iva-summary",
  files: [
    {
      name: "index.ts",
      content: "..." // contenido del archivo
    }
  ]
})
```

## Testing Local

Requiere Deno instalado:

```bash
# Instalar Deno
brew install deno  # macOS
# o seguir instrucciones en https://deno.land/

# Servir localmente
cd backend
supabase functions serve iva-summary

# Hacer request de prueba
curl -X POST http://localhost:54321/functions/v1/iva-summary \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "your-company-id",
    "period": "2025-01"
  }'
```

## Ventajas sobre el endpoint Python

1. **Rendimiento**: Ejecuta más cerca de la base de datos
2. **Escalabilidad**: Auto-escala con tráfico
3. **Costo**: Pay-per-execution (no siempre corriendo)
4. **Latencia**: Menor latencia al evitar saltos de red
5. **Deployment**: Deploy independiente del backend principal

## Lógica de Negocio

### Documentos de Ventas (Débito Fiscal)

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

### Documentos de Compras (Crédito Fiscal)

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

## Autenticación

Usa JWT de Supabase Auth. La función valida que:
1. El header `Authorization` esté presente
2. El token sea válido
3. El usuario esté autenticado

## Environment Variables

La función usa las siguientes variables (auto-configuradas en Supabase):
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

## Comparación con Python Service

Esta función replica exactamente la lógica de:
- `backend/app/services/tax_summary_service.py:TaxSummaryService.get_iva_summary()`

Diferencias:
- **Lenguaje**: TypeScript/Deno vs Python
- **Ejecución**: Edge runtime vs FastAPI
- **Dependencias**: Supabase client vs SQLAlchemy + custom repos
- **Performance**: ~50-100ms vs ~200-500ms (estimado)
