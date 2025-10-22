# Análisis de Respuestas F29 y Diseño de Modelos

## 📊 Resultados de las Pruebas

### Test 1: `get_f29_lista(anio="2024")`

**Resultado:** ✅ **12 formularios extraídos exitosamente**

**Estructura de cada formulario:**
```json
{
  "folio": "7904207766",
  "period": "2024-01",
  "contributor": "77794858-K",
  "submission_date": "09/05/2024",
  "status": "Vigente",
  "amount": 42443,
  "id_interno_sii": "775148628"
}
```

**Tipos de datos:**
- `folio`: `str` - Número de folio del formulario (único por formulario)
- `period`: `str` - Formato "YYYY-MM" (ej: "2024-01")
- `contributor`: `str` - RUT del contribuyente
- `submission_date`: `str` - Formato "DD/MM/YYYY"
- `status`: `str` - Estado del formulario ("Vigente", "Rectificado", etc.)
- `amount`: `int` - Monto en pesos chilenos (entero, sin decimales)
- `id_interno_sii`: `str` - **OPCIONAL** - ID interno del SII necesario para descargar PDF

**⚠️ Observación Importante:**
- **9 de 12 formularios** tienen `id_interno_sii`
- **3 formularios (2024-03, 2024-04, 2024-12)** NO tienen `id_interno_sii`
- Sin `id_interno_sii` **NO se puede descargar el PDF**

---

### Test 2: `get_f29_compacto(folio, id_interno_sii)`

**Resultado:** ⚠️ **PDF descargado pero con error**

```
✅ PDF downloaded: 12,135 bytes
📄 Title: "Ha ocurrido un error al imprimir PDF"
```

**Análisis:**
- El método descarga un PDF válido (12KB)
- El PDF contiene un mensaje de error del SII
- Posibles causas:
  1. Sesión expiró antes de generar el PDF
  2. Parámetros incorrectos (folio vs id_interno)
  3. Formulario no está disponible para descarga
  4. Necesita permisos especiales en el portal SII

---

## 🎯 Diseño de Modelos de Datos

Basado en los resultados reales, propongo **2 opciones**:

---

### Opción 1: Tabla Separada `form29_sii_downloads` (RECOMENDADA)

**Ventajas:**
- ✅ Separa F29 "calculados localmente" de F29 "descargados del SII"
- ✅ Permite almacenar múltiples versiones (rectificaciones)
- ✅ Mejor para auditoría y trazabilidad
- ✅ Puede relacionar F29 del SII con F29 local

**Migración SQL:**
```sql
-- =====================================================================
-- F29 SII Downloads - Registro de formularios descargados del SII
-- =====================================================================

CREATE TABLE IF NOT EXISTS form29_sii_downloads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- Opcional: relacionar con F29 calculado localmente
    form29_id UUID REFERENCES form29(id) ON DELETE SET NULL,

    -- Datos del SII (tal como vienen en la respuesta)
    sii_folio TEXT NOT NULL,
    sii_id_interno TEXT,  -- NULLABLE - no siempre viene

    -- Período
    period_year INTEGER NOT NULL,
    period_month INTEGER NOT NULL,
    period_display TEXT NOT NULL,  -- Formato "YYYY-MM" del SII

    -- Información del formulario
    contributor_rut TEXT NOT NULL,
    submission_date DATE,  -- Convertir "DD/MM/YYYY" -> DATE
    status TEXT NOT NULL,  -- Vigente, Rectificado, Anulado
    amount_cents INTEGER NOT NULL,  -- Monto en pesos (sin decimales)

    -- PDF descargado
    pdf_storage_url TEXT,  -- URL en storage (ej: Supabase Storage)
    pdf_download_status TEXT DEFAULT 'pending',  -- pending, downloaded, error
    pdf_download_error TEXT,
    pdf_downloaded_at TIMESTAMPTZ,

    -- Metadatos adicionales
    extra_data JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    -- Constraints
    CONSTRAINT form29_sii_downloads_company_folio_unique
        UNIQUE (company_id, sii_folio),
    CONSTRAINT form29_sii_downloads_period_month_check
        CHECK (period_month >= 1 AND period_month <= 12),
    CONSTRAINT form29_sii_downloads_status_check
        CHECK (status = ANY (ARRAY['Vigente'::text, 'Rectificado'::text, 'Anulado'::text])),
    CONSTRAINT form29_sii_downloads_pdf_status_check
        CHECK (pdf_download_status = ANY (ARRAY['pending'::text, 'downloaded'::text, 'error'::text]))
);

-- Índices
CREATE INDEX IF NOT EXISTS ix_form29_sii_downloads_company_period
    ON form29_sii_downloads(company_id, period_year, period_month);

CREATE INDEX IF NOT EXISTS ix_form29_sii_downloads_folio
    ON form29_sii_downloads(sii_folio);

CREATE INDEX IF NOT EXISTS ix_form29_sii_downloads_status
    ON form29_sii_downloads(company_id, status);

-- Trigger para updated_at
CREATE TRIGGER update_form29_sii_downloads_updated_at
    BEFORE UPDATE ON form29_sii_downloads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- RLS Policies
ALTER TABLE form29_sii_downloads ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view form29 sii downloads via sessions"
    ON form29_sii_downloads FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.company_id = form29_sii_downloads.company_id
        AND sessions.user_id = auth.uid()
        AND sessions.is_active = true
    ));

CREATE POLICY "Users can manage form29 sii downloads via sessions"
    ON form29_sii_downloads FOR ALL
    USING (EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.company_id = form29_sii_downloads.company_id
        AND sessions.user_id = auth.uid()
        AND sessions.is_active = true
    ));

-- Comentarios
COMMENT ON TABLE form29_sii_downloads IS 'F29 forms downloaded from SII portal';
COMMENT ON COLUMN form29_sii_downloads.sii_folio IS 'Folio number from SII (unique per form)';
COMMENT ON COLUMN form29_sii_downloads.sii_id_interno IS 'Internal SII ID required for PDF download (may be null)';
COMMENT ON COLUMN form29_sii_downloads.amount_cents IS 'Amount in Chilean pesos (integer, no decimals)';
COMMENT ON COLUMN form29_sii_downloads.pdf_storage_url IS 'URL to PDF file in storage (e.g., Supabase Storage)';
```

**Modelo Python (SQLAlchemy):**
```python
"""Form 29 SII downloads model - tracks F29 forms downloaded from SII."""

from datetime import datetime, date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Text, Date, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .company import Company
    from .form29 import Form29


class Form29SIIDownload(Base):
    """Form 29 SII Download - Tracks F29 forms downloaded from SII portal.

    This table stores F29 forms as they appear in the SII portal,
    separate from locally calculated F29 forms.
    """

    __tablename__ = "form29_sii_downloads"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("companies.id")
    )

    # Optional link to local F29
    form29_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("form29.id"), nullable=True
    )

    # SII data (as returned from API)
    sii_folio: Mapped[str] = mapped_column(Text)
    sii_id_interno: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Period
    period_year: Mapped[int] = mapped_column(Integer)
    period_month: Mapped[int] = mapped_column(Integer)
    period_display: Mapped[str] = mapped_column(Text)  # "YYYY-MM" format

    # Form information
    contributor_rut: Mapped[str] = mapped_column(Text)
    submission_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(Text)  # Vigente, Rectificado, Anulado
    amount_cents: Mapped[int] = mapped_column(Integer, server_default=text("0"))

    # PDF download tracking
    pdf_storage_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pdf_download_status: Mapped[str] = mapped_column(
        Text, server_default=text("'pending'::text")
    )  # pending, downloaded, error
    pdf_download_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pdf_downloaded_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    # Additional data
    extra_data: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, server_default=text("'{}'::jsonb")
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )

    __table_args__ = (
        UniqueConstraint(
            "company_id", "sii_folio",
            name="form29_sii_downloads_company_folio_unique"
        ),
        CheckConstraint(
            "period_month >= 1 AND period_month <= 12",
            name="form29_sii_downloads_period_month_check",
        ),
        CheckConstraint(
            "status = ANY (ARRAY['Vigente'::text, 'Rectificado'::text, 'Anulado'::text])",
            name="form29_sii_downloads_status_check",
        ),
        CheckConstraint(
            "pdf_download_status = ANY (ARRAY['pending'::text, 'downloaded'::text, 'error'::text])",
            name="form29_sii_downloads_pdf_status_check",
        ),
        Index("ix_form29_sii_downloads_company_period", "company_id", "period_year", "period_month"),
        Index("ix_form29_sii_downloads_folio", "sii_folio"),
        Index("ix_form29_sii_downloads_status", "company_id", "status"),
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="form29_sii_downloads")
    form29: Mapped[Optional["Form29"]] = relationship("Form29", back_populates="sii_download")
```

---

### Opción 2: Usar `extra_data` en tabla existente `form29`

**Ventajas:**
- ✅ No requiere nueva tabla
- ✅ Implementación más rápida

**Desventajas:**
- ❌ Mezcla datos calculados con datos del SII
- ❌ Dificulta queries y búsquedas
- ❌ No permite almacenar múltiples versiones
- ❌ Menos auditable

**Ejemplo de `extra_data`:**
```json
{
  "sii_data": {
    "folio": "7904207766",
    "id_interno": "775148628",
    "contributor": "77794858-K",
    "submission_date": "09/05/2024",
    "status": "Vigente",
    "amount": 42443,
    "pdf_url": "https://storage.supabase.co/..."
  }
}
```

---

## 🔍 Observaciones del PDF Download

**Problema detectado:** El PDF descargado contiene un error del SII.

**Posibles soluciones:**

1. **Revisar el método de descarga:**
   - Verificar que la sesión esté activa antes de descargar
   - Agregar delays entre login y descarga
   - Usar un navegador real en lugar de headless para debugging

2. **Implementar reintentos:**
   ```python
   async def download_f29_pdf_with_retry(
       session_id: int,
       folio: str,
       id_interno_sii: str,
       max_retries: int = 3
   ):
       for attempt in range(max_retries):
           try:
               pdf = await download_f29_pdf(...)
               if is_valid_pdf(pdf):
                   return pdf
               await asyncio.sleep(5)
           except Exception as e:
               if attempt == max_retries - 1:
                   raise
               await asyncio.sleep(10)
   ```

3. **Validar PDF antes de guardar:**
   ```python
   def is_valid_f29_pdf(pdf_bytes: bytes) -> bool:
       """Check if PDF is valid F29 (not an error page)"""
       if b"error" in pdf_bytes.lower():
           return False
       if b"Ha ocurrido un error" in pdf_bytes:
           return False
       return True
   ```

---

## 📋 Recomendaciones Finales

### ✅ Implementar Opción 1: Tabla Separada

**Razones:**
1. Mejor separación de concerns
2. Permite auditoría completa
3. Facilita reconciliación entre F29 SII vs F29 local
4. Más escalable para futuras features

### 🔧 Mejoras al Servicio de Descarga

1. **Agregar validación de PDF**
2. **Implementar retry logic**
3. **Guardar PDFs en Supabase Storage**
4. **Agregar logging detallado**
5. **Crear job async para descargas batch**

### 📊 Campos Adicionales Sugeridos

- `reconciliation_status`: `reconciled`, `mismatch`, `pending`
- `reconciliation_notes`: JSONB con detalles de diferencias
- `last_sync_at`: Timestamp de última sincronización con SII

---

## 🚀 Próximos Pasos

1. ✅ Crear migración `010_add_form29_sii_downloads.sql`
2. ✅ Crear modelo Python `Form29SIIDownload`
3. ✅ Actualizar relaciones en modelos existentes
4. ✅ Crear servicio para guardar descargas del SII
5. ✅ Implementar endpoint para sincronización
6. ✅ Agregar validación de PDFs
7. ✅ Implementar almacenamiento en Supabase Storage

---

**Fecha:** 2025-01-22
**Autor:** Análisis basado en tests reales contra SII
