-- ==============================================================================
-- SEED: Datos de Prueba para Calendario Tributario
-- ==============================================================================
-- Este script crea eventos de prueba para una empresa existente
--
-- IMPORTANTE: Reemplaza el company_id con el ID de tu empresa
--
-- Para ejecutar:
-- 1. Ve a Supabase SQL Editor
-- 2. Copia y pega este script
-- 3. Reemplaza '6aac42e9-a605-40d3-b15a-01b9eab5269f' con tu company_id
-- 4. Ejecuta el script
-- ==============================================================================

-- CONFIGURACIÓN: Reemplaza esto con tu company_id
\set company_id '6aac42e9-a605-40d3-b15a-01b9eab5269f'

-- ==============================================================================
-- PASO 1: Crear Event Rules (Reglas de recurrencia por empresa)
-- ==============================================================================

-- Regla para F29 (Declaración Mensual IVA - vence día 12 de cada mes)
INSERT INTO event_rules (company_id, event_type_id, is_active, recurrence_config)
SELECT
    '6aac42e9-a605-40d3-b15a-01b9eab5269f'::uuid,
    id,
    true,
    '{"frequency": "monthly", "day_of_month": 12, "business_days_adjustment": "after"}'::jsonb
FROM event_types WHERE code = 'f29'
ON CONFLICT DO NOTHING;

-- Regla para F22 (Declaración Anual Renta - vence 30 de abril)
INSERT INTO event_rules (company_id, event_type_id, is_active, recurrence_config)
SELECT
    '6aac42e9-a605-40d3-b15a-01b9eab5269f'::uuid,
    id,
    true,
    '{"frequency": "annual", "day_of_month": 30, "month_of_year": 4, "business_days_adjustment": "after"}'::jsonb
FROM event_types WHERE code = 'f22'
ON CONFLICT DO NOTHING;

-- Regla para Previred (Cotizaciones Previsionales - vence día 10 de cada mes)
INSERT INTO event_rules (company_id, event_type_id, is_active, recurrence_config)
SELECT
    '6aac42e9-a605-40d3-b15a-01b9eab5269f'::uuid,
    id,
    true,
    '{"frequency": "monthly", "day_of_month": 10, "business_days_adjustment": "after"}'::jsonb
FROM event_types WHERE code = 'previred'
ON CONFLICT DO NOTHING;

-- ==============================================================================
-- PASO 2: Crear Calendar Events (Instancias concretas de eventos)
-- ==============================================================================

-- F29 Octubre 2025 (vence 12-Nov-2025)
INSERT INTO calendar_events (
    event_rule_id,
    company_id,
    event_type_id,
    title,
    description,
    due_date,
    period_start,
    period_end,
    status,
    auto_generated
)
SELECT
    er.id,
    '6aac42e9-a605-40d3-b15a-01b9eab5269f'::uuid,
    et.id,
    'Declaración Mensual F29 - Octubre 2025',
    'Declaración y pago IVA correspondiente al período tributario de octubre 2025',
    '2025-11-12'::date,
    '2025-10-01'::date,
    '2025-10-31'::date,
    'pending'::event_status,
    true
FROM event_types et
JOIN event_rules er ON er.event_type_id = et.id
WHERE et.code = 'f29'
  AND er.company_id = '6aac42e9-a605-40d3-b15a-01b9eab5269f'::uuid
ON CONFLICT DO NOTHING;

-- F29 Noviembre 2025 (vence 12-Dic-2025)
INSERT INTO calendar_events (
    event_rule_id,
    company_id,
    event_type_id,
    title,
    description,
    due_date,
    period_start,
    period_end,
    status,
    auto_generated
)
SELECT
    er.id,
    '6aac42e9-a605-40d3-b15a-01b9eab5269f'::uuid,
    et.id,
    'Declaración Mensual F29 - Noviembre 2025',
    'Declaración y pago IVA correspondiente al período tributario de noviembre 2025',
    '2025-12-12'::date,
    '2025-11-01'::date,
    '2025-11-30'::date,
    'pending'::event_status,
    true
FROM event_types et
JOIN event_rules er ON er.event_type_id = et.id
WHERE et.code = 'f29'
  AND er.company_id = '6aac42e9-a605-40d3-b15a-01b9eab5269f'::uuid
ON CONFLICT DO NOTHING;

-- Previred Octubre 2025 (vence 10-Nov-2025)
INSERT INTO calendar_events (
    event_rule_id,
    company_id,
    event_type_id,
    title,
    description,
    due_date,
    period_start,
    period_end,
    status,
    auto_generated
)
SELECT
    er.id,
    '6aac42e9-a605-40d3-b15a-01b9eab5269f'::uuid,
    et.id,
    'Declaración y Pago Previred - Octubre 2025',
    'Declaración y pago cotizaciones previsionales correspondientes a octubre 2025',
    '2025-11-10'::date,
    '2025-10-01'::date,
    '2025-10-31'::date,
    'pending'::event_status,
    true
FROM event_types et
JOIN event_rules er ON er.event_type_id = et.id
WHERE et.code = 'previred'
  AND er.company_id = '6aac42e9-a605-40d3-b15a-01b9eab5269f'::uuid
ON CONFLICT DO NOTHING;

-- Previred Noviembre 2025 (vence 10-Dic-2025)
INSERT INTO calendar_events (
    event_rule_id,
    company_id,
    event_type_id,
    title,
    description,
    due_date,
    period_start,
    period_end,
    status,
    auto_generated
)
SELECT
    er.id,
    '6aac42e9-a605-40d3-b15a-01b9eab5269f'::uuid,
    et.id,
    'Declaración y Pago Previred - Noviembre 2025',
    'Declaración y pago cotizaciones previsionales correspondientes a noviembre 2025',
    '2025-12-10'::date,
    '2025-11-01'::date,
    '2025-11-30'::date,
    'pending'::event_status,
    true
FROM event_types et
JOIN event_rules er ON er.event_type_id = et.id
WHERE et.code = 'previred'
  AND er.company_id = '6aac42e9-a605-40d3-b15a-01b9eab5269f'::uuid
ON CONFLICT DO NOTHING;

-- F22 AT 2024 (vence 30-Abr-2025) - OVERDUE para pruebas
INSERT INTO calendar_events (
    event_rule_id,
    company_id,
    event_type_id,
    title,
    description,
    due_date,
    period_start,
    period_end,
    status,
    auto_generated
)
SELECT
    er.id,
    '6aac42e9-a605-40d3-b15a-01b9eab5269f'::uuid,
    et.id,
    'Declaración Renta Año Tributario 2024 (F22)',
    'Declaración anual de impuesto a la renta correspondiente al AT 2024',
    '2025-04-30'::date,
    '2024-01-01'::date,
    '2024-12-31'::date,
    'overdue'::event_status,
    true
FROM event_types et
JOIN event_rules er ON er.event_type_id = et.id
WHERE et.code = 'f22'
  AND er.company_id = '6aac42e9-a605-40d3-b15a-01b9eab5269f'::uuid
ON CONFLICT DO NOTHING;

-- ==============================================================================
-- VERIFICACIÓN: Ver los eventos creados
-- ==============================================================================

SELECT
    ce.title,
    ce.due_date,
    ce.status,
    et.name as event_type_name,
    et.code as event_code,
    c.business_name as company_name
FROM calendar_events ce
JOIN event_types et ON ce.event_type_id = et.id
JOIN companies c ON ce.company_id = c.id
WHERE ce.company_id = '6aac42e9-a605-40d3-b15a-01b9eab5269f'::uuid
ORDER BY ce.due_date;
