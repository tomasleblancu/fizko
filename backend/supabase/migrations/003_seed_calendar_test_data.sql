-- Seed data para testing del calendario tributario
-- Este script crea eventos de prueba para una empresa existente

-- Primero obtenemos el ID de una empresa existente y los event_types
DO $$
DECLARE
    v_company_id UUID;
    v_f29_type_id UUID;
    v_f22_type_id UUID;
    v_previred_type_id UUID;
    v_rule_f29_id UUID;
    v_rule_f22_id UUID;
    v_rule_previred_id UUID;
BEGIN
    -- Obtener una empresa existente (la primera que encontremos)
    SELECT id INTO v_company_id FROM companies LIMIT 1;

    IF v_company_id IS NULL THEN
        RAISE NOTICE 'No se encontró ninguna empresa. Saltando seed de datos de calendario.';
        RETURN;
    END IF;

    RAISE NOTICE 'Usando empresa ID: %', v_company_id;

    -- Obtener IDs de los event types
    SELECT id INTO v_f29_type_id FROM event_types WHERE code = 'f29';
    SELECT id INTO v_f22_type_id FROM event_types WHERE code = 'f22';
    SELECT id INTO v_previred_type_id FROM event_types WHERE code = 'previred';

    -- Crear event_rules para esta empresa (si no existen ya)
    -- Regla para F29 (mensual, vence día 12)
    INSERT INTO event_rules (company_id, event_type_id, is_active, recurrence_config)
    VALUES (
        v_company_id,
        v_f29_type_id,
        true,
        jsonb_build_object(
            'frequency', 'monthly',
            'day_of_month', 12,
            'business_days_adjustment', 'after'
        )
    )
    ON CONFLICT DO NOTHING
    RETURNING id INTO v_rule_f29_id;

    -- Si ya existía, obtener su ID
    IF v_rule_f29_id IS NULL THEN
        SELECT id INTO v_rule_f29_id
        FROM event_rules
        WHERE company_id = v_company_id AND event_type_id = v_f29_type_id;
    END IF;

    -- Regla para F22 (anual, vence 30 de abril)
    INSERT INTO event_rules (company_id, event_type_id, is_active, recurrence_config)
    VALUES (
        v_company_id,
        v_f22_type_id,
        true,
        jsonb_build_object(
            'frequency', 'annual',
            'day_of_month', 30,
            'month_of_year', 4,
            'business_days_adjustment', 'after'
        )
    )
    ON CONFLICT DO NOTHING
    RETURNING id INTO v_rule_f22_id;

    IF v_rule_f22_id IS NULL THEN
        SELECT id INTO v_rule_f22_id
        FROM event_rules
        WHERE company_id = v_company_id AND event_type_id = v_f22_type_id;
    END IF;

    -- Regla para Previred (mensual, vence día 10)
    INSERT INTO event_rules (company_id, event_type_id, is_active, recurrence_config)
    VALUES (
        v_company_id,
        v_previred_type_id,
        true,
        jsonb_build_object(
            'frequency', 'monthly',
            'day_of_month', 10,
            'business_days_adjustment', 'after'
        )
    )
    ON CONFLICT DO NOTHING
    RETURNING id INTO v_rule_previred_id;

    IF v_rule_previred_id IS NULL THEN
        SELECT id INTO v_rule_previred_id
        FROM event_rules
        WHERE company_id = v_company_id AND event_type_id = v_previred_type_id;
    END IF;

    -- Crear eventos de calendario para los próximos 2 meses

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
    ) VALUES (
        v_rule_f29_id,
        v_company_id,
        v_f29_type_id,
        'Declaración Mensual F29 - Octubre 2025',
        'Declaración y pago IVA correspondiente al período tributario de octubre 2025',
        '2025-11-12'::date,
        '2025-10-01'::date,
        '2025-10-31'::date,
        'pending'::event_status,
        true
    )
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
    ) VALUES (
        v_rule_f29_id,
        v_company_id,
        v_f29_type_id,
        'Declaración Mensual F29 - Noviembre 2025',
        'Declaración y pago IVA correspondiente al período tributario de noviembre 2025',
        '2025-12-12'::date,
        '2025-11-01'::date,
        '2025-11-30'::date,
        'pending'::event_status,
        true
    )
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
    ) VALUES (
        v_rule_previred_id,
        v_company_id,
        v_previred_type_id,
        'Declaración y Pago Previred - Octubre 2025',
        'Declaración y pago cotizaciones previsionales correspondientes a octubre 2025',
        '2025-11-10'::date,
        '2025-10-01'::date,
        '2025-10-31'::date,
        'pending'::event_status,
        true
    )
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
    ) VALUES (
        v_rule_previred_id,
        v_company_id,
        v_previred_type_id,
        'Declaración y Pago Previred - Noviembre 2025',
        'Declaración y pago cotizaciones previsionales correspondientes a noviembre 2025',
        '2025-12-10'::date,
        '2025-11-01'::date,
        '2025-11-30'::date,
        'pending'::event_status,
        true
    )
    ON CONFLICT DO NOTHING;

    -- F22 AT 2024 (vence 30-Abr-2025) - ya vencido para mostrar estado overdue
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
    ) VALUES (
        v_rule_f22_id,
        v_company_id,
        v_f22_type_id,
        'Declaración Renta Año Tributario 2024 (F22)',
        'Declaración anual de impuesto a la renta correspondiente al AT 2024',
        '2025-04-30'::date,
        '2024-01-01'::date,
        '2024-12-31'::date,
        'overdue'::event_status,
        true
    )
    ON CONFLICT DO NOTHING;

    RAISE NOTICE 'Eventos de calendario creados exitosamente para empresa %', v_company_id;

END $$;

-- Verificar los datos creados
SELECT
    ce.title,
    ce.due_date,
    ce.status,
    et.name as event_type_name,
    c.business_name as company_name
FROM calendar_events ce
JOIN event_types et ON ce.event_type_id = et.id
JOIN companies c ON ce.company_id = c.id
ORDER BY ce.due_date;
