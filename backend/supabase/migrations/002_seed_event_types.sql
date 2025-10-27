-- Seed: Initial Event Types for Chilean Tax System
-- Description: Tipos de eventos tributarios principales para Chile
-- Author: Claude
-- Date: 2025-10-27

-- ============================================================================
-- IMPUESTOS MENSUALES
-- ============================================================================

-- F29: Declaración Mensual de IVA
INSERT INTO event_types (code, name, description, category, authority, is_mandatory, applies_to_regimes, default_recurrence, metadata)
VALUES (
    'f29',
    'Declaración Mensual F29',
    'Declaración y pago mensual de IVA (Impuesto al Valor Agregado)',
    'impuesto_mensual',
    'SII',
    true,
    '["pro_pyme", "general", "14ter"]'::jsonb,
    '{
        "frequency": "monthly",
        "interval": 1,
        "day_of_month": 12,
        "months": [1,2,3,4,5,6,7,8,9,10,11,12],
        "business_days_adjustment": true,
        "advance_days": 5
    }'::jsonb,
    '{
        "url": "https://www.sii.cl/servicios_online/declaracion_mensual_iva.html",
        "form_number": "29",
        "requires_electronic_signature": true
    }'::jsonb
);

-- PPM (Pago Provisional Mensual)
INSERT INTO event_types (code, name, description, category, authority, is_mandatory, applies_to_regimes, default_recurrence, metadata)
VALUES (
    'ppm',
    'Pago Provisional Mensual (PPM)',
    'Pago mensual a cuenta del impuesto a la renta anual',
    'impuesto_mensual',
    'SII',
    true,
    '["pro_pyme", "general"]'::jsonb,
    '{
        "frequency": "monthly",
        "interval": 1,
        "day_of_month": 12,
        "months": [1,2,3,4,5,6,7,8,9,10,11,12],
        "business_days_adjustment": true,
        "advance_days": 5
    }'::jsonb,
    '{
        "url": "https://www.sii.cl/preguntas_frecuentes/renta/001_002_3707.htm",
        "calculation_type": "percentage_of_income",
        "default_percentage": 0.5
    }'::jsonb
);

-- ============================================================================
-- IMPUESTOS ANUALES
-- ============================================================================

-- F22: Declaración Anual de Impuesto a la Renta
INSERT INTO event_types (code, name, description, category, authority, is_mandatory, applies_to_regimes, default_recurrence, metadata)
VALUES (
    'f22',
    'Declaración Anual de Renta (F22)',
    'Declaración anual del Impuesto a la Renta para empresas',
    'impuesto_anual',
    'SII',
    true,
    '["pro_pyme", "general", "14ter"]'::jsonb,
    '{
        "frequency": "annual",
        "interval": 1,
        "day_of_month": 30,
        "months": [4],
        "business_days_adjustment": true,
        "advance_days": 15
    }'::jsonb,
    '{
        "url": "https://www.sii.cl/destacados/renta/renta.html",
        "form_number": "22",
        "requires_electronic_signature": true,
        "tax_year_offset": -1
    }'::jsonb
);

-- Declaración Jurada Anual sobre Inversiones
INSERT INTO event_types (code, name, description, category, authority, is_mandatory, applies_to_regimes, default_recurrence, metadata)
VALUES (
    'dj_inversiones',
    'Declaración Jurada Anual - Inversiones',
    'Declaración anual sobre inversiones y retiros',
    'impuesto_anual',
    'SII',
    false,
    '["pro_pyme", "general"]'::jsonb,
    '{
        "frequency": "annual",
        "interval": 1,
        "day_of_month": 31,
        "months": [3],
        "business_days_adjustment": true,
        "advance_days": 10
    }'::jsonb,
    '{
        "url": "https://www.sii.cl/servicios_online/declaraciones_juradas.html",
        "applies_if": "tiene_inversiones"
    }'::jsonb
);

-- ============================================================================
-- PREVISIÓN SOCIAL
-- ============================================================================

-- Previred: Cotizaciones Previsionales
INSERT INTO event_types (code, name, description, category, authority, is_mandatory, applies_to_regimes, default_recurrence, metadata)
VALUES (
    'previred',
    'Pago Cotizaciones Previred',
    'Pago mensual de cotizaciones previsionales de trabajadores',
    'prevision',
    'Previred',
    false,
    '["all"]'::jsonb,
    '{
        "frequency": "monthly",
        "interval": 1,
        "day_of_month": 10,
        "months": [1,2,3,4,5,6,7,8,9,10,11,12],
        "business_days_adjustment": true,
        "advance_days": 3
    }'::jsonb,
    '{
        "url": "https://www.previred.com/",
        "applies_if": "tiene_empleados",
        "requires_electronic_signature": false,
        "payment_required": true
    }'::jsonb
);

-- ============================================================================
-- ADUANAS
-- ============================================================================

-- Declaración de Importación
INSERT INTO event_types (code, name, description, category, authority, is_mandatory, applies_to_regimes, default_recurrence, metadata)
VALUES (
    'declaracion_importacion',
    'Declaración de Importación',
    'Declaración aduanera para mercancías importadas',
    'aduanas',
    'Aduana',
    false,
    '["all"]'::jsonb,
    '{
        "frequency": "custom",
        "interval": 1,
        "business_days_adjustment": false,
        "advance_days": 2
    }'::jsonb,
    '{
        "url": "https://www.aduana.cl/declaracion-de-importacion/aduana/2007-02-28/105031.html",
        "applies_if": "realiza_importaciones",
        "requires_customs_agent": true
    }'::jsonb
);

-- ============================================================================
-- OTROS EVENTOS
-- ============================================================================

-- Actualización de Nómina de Empleados
INSERT INTO event_types (code, name, description, category, authority, is_mandatory, applies_to_regimes, default_recurrence, metadata)
VALUES (
    'actualizacion_nomina',
    'Actualización Nómina de Empleados',
    'Mantener actualizada la nómina de empleados en el SII',
    'laboral',
    'SII',
    false,
    '["all"]'::jsonb,
    '{
        "frequency": "monthly",
        "interval": 1,
        "day_of_month": 15,
        "months": [1,2,3,4,5,6,7,8,9,10,11,12],
        "business_days_adjustment": false,
        "advance_days": 5
    }'::jsonb,
    '{
        "url": "https://www.sii.cl/servicios_online/actualizacion_nomina.html",
        "applies_if": "tiene_empleados"
    }'::jsonb
);

-- Libro de Compras y Ventas
INSERT INTO event_types (code, name, description, category, authority, is_mandatory, applies_to_regimes, default_recurrence, metadata)
VALUES (
    'libro_compras_ventas',
    'Libro de Compras y Ventas',
    'Registro electrónico de compras y ventas en el SII',
    'impuesto_mensual',
    'SII',
    true,
    '["pro_pyme", "general", "14ter"]'::jsonb,
    '{
        "frequency": "monthly",
        "interval": 1,
        "day_of_month": 12,
        "months": [1,2,3,4,5,6,7,8,9,10,11,12],
        "business_days_adjustment": true,
        "advance_days": 5
    }'::jsonb,
    '{
        "url": "https://www.sii.cl/servicios_online/libro_compras_ventas.html",
        "integrated_with": "f29",
        "automatic_from_documents": true
    }'::jsonb
);

-- ============================================================================
-- DEPENDENCIAS ENTRE EVENTOS
-- ============================================================================

-- F22 depende de que F29 esté completo para todo el año
INSERT INTO event_dependencies (event_type_id, depends_on_event_type_id, dependency_type, description)
SELECT
    (SELECT id FROM event_types WHERE code = 'f22'),
    (SELECT id FROM event_types WHERE code = 'f29'),
    'requires_data',
    'La declaración anual F22 requiere que todos los F29 del año estén completados';

-- F29 depende de que el Libro de Compras y Ventas esté actualizado
INSERT INTO event_dependencies (event_type_id, depends_on_event_type_id, dependency_type, description)
SELECT
    (SELECT id FROM event_types WHERE code = 'f29'),
    (SELECT id FROM event_types WHERE code = 'libro_compras_ventas'),
    'suggests',
    'Se recomienda tener actualizado el Libro de Compras y Ventas antes de hacer el F29';

-- ============================================================================
-- VERIFICACIÓN
-- ============================================================================

-- Contar event_types insertados
DO $$
DECLARE
    event_count INTEGER;
    dep_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO event_count FROM event_types;
    SELECT COUNT(*) INTO dep_count FROM event_dependencies;

    RAISE NOTICE 'Seed completado:';
    RAISE NOTICE '  - % tipos de eventos creados', event_count;
    RAISE NOTICE '  - % dependencias creadas', dep_count;
END $$;
