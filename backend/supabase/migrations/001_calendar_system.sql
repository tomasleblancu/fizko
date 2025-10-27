-- Migration: Calendar System for Fizko
-- Description: Sistema de calendario tributario con eventos recurrentes
-- Author: Claude
-- Date: 2025-10-27

-- ============================================================================
-- 1. ENUM TYPES
-- ============================================================================

-- Categorías de eventos tributarios
CREATE TYPE event_category AS ENUM (
    'impuesto_mensual',    -- F29, etc.
    'impuesto_anual',      -- F22, Declaración Renta
    'prevision',           -- Previred
    'aduanas',             -- Declaraciones de importación
    'laboral',             -- Finiquitos, contratos
    'otros'
);

-- Estado de eventos del calendario
CREATE TYPE event_status AS ENUM (
    'pending',       -- Pendiente
    'in_progress',   -- En progreso
    'completed',     -- Completado
    'overdue',       -- Vencido
    'cancelled'      -- Cancelado
);

-- Estado de tareas dentro de un evento
CREATE TYPE task_status AS ENUM (
    'pending',
    'completed',
    'failed',
    'skipped'
);

-- Frecuencia de recurrencia
CREATE TYPE recurrence_frequency AS ENUM (
    'monthly',
    'quarterly',
    'annual',
    'custom'
);

-- ============================================================================
-- 2. TABLE: event_types (Catálogo Global)
-- ============================================================================

CREATE TABLE event_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identificación
    code VARCHAR(50) UNIQUE NOT NULL,  -- 'f29', 'f22', 'previred'
    name VARCHAR(255) NOT NULL,         -- 'Declaración Mensual F29'
    description TEXT,

    -- Clasificación
    category event_category NOT NULL,
    authority VARCHAR(100),             -- 'SII', 'Previred', 'Aduana'

    -- Aplicabilidad
    is_mandatory BOOLEAN DEFAULT false,  -- Si aplica a todas las empresas
    applies_to_regimes JSONB,           -- ['pro_pyme', 'general', '14ter']

    -- Configuración por defecto
    default_recurrence JSONB NOT NULL,  -- Configuración de recurrencia

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_event_types_code ON event_types(code);
CREATE INDEX idx_event_types_category ON event_types(category);

-- Trigger para updated_at
CREATE TRIGGER update_event_types_updated_at
    BEFORE UPDATE ON event_types
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 3. TABLE: event_rules (Configuración por Empresa)
-- ============================================================================

CREATE TABLE event_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relaciones
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    event_type_id UUID NOT NULL REFERENCES event_types(id) ON DELETE CASCADE,

    -- Configuración
    is_active BOOLEAN DEFAULT true,

    -- Recurrencia específica de la empresa
    recurrence_config JSONB NOT NULL,
    /*
    Ejemplo:
    {
        "frequency": "monthly",
        "interval": 1,
        "day_of_month": 12,
        "months": [1,2,3,4,5,6,7,8,9,10,11,12],
        "start_date": "2025-01-01",
        "end_date": null,
        "business_days_adjustment": true,
        "advance_days": 5
    }
    */

    -- Configuraciones personalizadas
    custom_config JSONB DEFAULT '{}'::jsonb,

    -- Notificaciones
    notification_settings JSONB DEFAULT '{
        "enabled": true,
        "channels": ["email", "in_app"],
        "reminder_days": [7, 3, 1]
    }'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    UNIQUE(company_id, event_type_id)
);

-- Índices
CREATE INDEX idx_event_rules_company ON event_rules(company_id);
CREATE INDEX idx_event_rules_event_type ON event_rules(event_type_id);
CREATE INDEX idx_event_rules_active ON event_rules(is_active) WHERE is_active = true;

-- Trigger
CREATE TRIGGER update_event_rules_updated_at
    BEFORE UPDATE ON event_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 4. TABLE: calendar_events (Instancias Concretas)
-- ============================================================================

CREATE TABLE calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relaciones
    event_rule_id UUID NOT NULL REFERENCES event_rules(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    event_type_id UUID NOT NULL REFERENCES event_types(id) ON DELETE CASCADE,

    -- Información del evento
    title VARCHAR(255) NOT NULL,         -- 'F29 Octubre 2025'
    description TEXT,

    -- Fechas
    due_date DATE NOT NULL,              -- Fecha de vencimiento
    period_start DATE,                   -- Inicio del período (ej: 2025-10-01)
    period_end DATE,                     -- Fin del período (ej: 2025-10-31)

    -- Estado
    status event_status DEFAULT 'pending',

    -- Cumplimiento
    completion_date TIMESTAMPTZ,
    completion_data JSONB,              -- Datos del cumplimiento

    -- Metadata
    auto_generated BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_calendar_events_company_due_date ON calendar_events(company_id, due_date);
CREATE INDEX idx_calendar_events_company_status ON calendar_events(company_id, status);
CREATE INDEX idx_calendar_events_due_date ON calendar_events(due_date);
CREATE INDEX idx_calendar_events_status ON calendar_events(status);
CREATE INDEX idx_calendar_events_event_type ON calendar_events(event_type_id);

-- Trigger
CREATE TRIGGER update_calendar_events_updated_at
    BEFORE UPDATE ON calendar_events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 5. TABLE: event_tasks (Tareas dentro de un Evento)
-- ============================================================================

CREATE TABLE event_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relación
    calendar_event_id UUID NOT NULL REFERENCES calendar_events(id) ON DELETE CASCADE,

    -- Información de la tarea
    task_type VARCHAR(100) NOT NULL,     -- 'calculate_iva', 'submit_f29'
    title VARCHAR(255) NOT NULL,
    description TEXT,

    -- Orden y estado
    order_index INTEGER DEFAULT 0,
    status task_status DEFAULT 'pending',

    -- Automatización
    is_automated BOOLEAN DEFAULT false,
    automation_config JSONB,

    -- Resultado
    completion_data JSONB,
    completed_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_event_tasks_calendar_event ON event_tasks(calendar_event_id);
CREATE INDEX idx_event_tasks_status ON event_tasks(status);
CREATE INDEX idx_event_tasks_order ON event_tasks(calendar_event_id, order_index);

-- Trigger
CREATE TRIGGER update_event_tasks_updated_at
    BEFORE UPDATE ON event_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 6. TABLE: event_dependencies (Dependencias entre Eventos)
-- ============================================================================

CREATE TABLE event_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relaciones
    event_type_id UUID NOT NULL REFERENCES event_types(id) ON DELETE CASCADE,
    depends_on_event_type_id UUID NOT NULL REFERENCES event_types(id) ON DELETE CASCADE,

    -- Tipo de dependencia
    dependency_type VARCHAR(50) NOT NULL,  -- 'blocks', 'suggests', 'requires_data'
    description TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CHECK (event_type_id != depends_on_event_type_id)
);

-- Índices
CREATE INDEX idx_event_dependencies_event_type ON event_dependencies(event_type_id);

-- ============================================================================
-- 7. ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE event_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_dependencies ENABLE ROW LEVEL SECURITY;

-- event_types: Todos pueden leer (catálogo público)
CREATE POLICY "event_types_select_policy" ON event_types
    FOR SELECT USING (true);

-- event_rules: Solo usuarios de la empresa pueden ver/modificar sus reglas
CREATE POLICY "event_rules_select_policy" ON event_rules
    FOR SELECT USING (
        company_id IN (
            SELECT company_id FROM sessions
            WHERE user_id = auth.uid() AND is_active = true
        )
    );

CREATE POLICY "event_rules_insert_policy" ON event_rules
    FOR INSERT WITH CHECK (
        company_id IN (
            SELECT company_id FROM sessions
            WHERE user_id = auth.uid() AND is_active = true
        )
    );

CREATE POLICY "event_rules_update_policy" ON event_rules
    FOR UPDATE USING (
        company_id IN (
            SELECT company_id FROM sessions
            WHERE user_id = auth.uid() AND is_active = true
        )
    );

-- calendar_events: Solo usuarios de la empresa
CREATE POLICY "calendar_events_select_policy" ON calendar_events
    FOR SELECT USING (
        company_id IN (
            SELECT company_id FROM sessions
            WHERE user_id = auth.uid() AND is_active = true
        )
    );

CREATE POLICY "calendar_events_insert_policy" ON calendar_events
    FOR INSERT WITH CHECK (
        company_id IN (
            SELECT company_id FROM sessions
            WHERE user_id = auth.uid() AND is_active = true
        )
    );

CREATE POLICY "calendar_events_update_policy" ON calendar_events
    FOR UPDATE USING (
        company_id IN (
            SELECT company_id FROM sessions
            WHERE user_id = auth.uid() AND is_active = true
        )
    );

-- event_tasks: Acceso a través de calendar_events
CREATE POLICY "event_tasks_select_policy" ON event_tasks
    FOR SELECT USING (
        calendar_event_id IN (
            SELECT id FROM calendar_events
            WHERE company_id IN (
                SELECT company_id FROM sessions
                WHERE user_id = auth.uid() AND is_active = true
            )
        )
    );

CREATE POLICY "event_tasks_update_policy" ON event_tasks
    FOR UPDATE USING (
        calendar_event_id IN (
            SELECT id FROM calendar_events
            WHERE company_id IN (
                SELECT company_id FROM sessions
                WHERE user_id = auth.uid() AND is_active = true
            )
        )
    );

-- event_dependencies: Todos pueden leer
CREATE POLICY "event_dependencies_select_policy" ON event_dependencies
    FOR SELECT USING (true);

-- ============================================================================
-- 8. COMMENTS (Documentación)
-- ============================================================================

COMMENT ON TABLE event_types IS 'Catálogo global de tipos de eventos tributarios';
COMMENT ON TABLE event_rules IS 'Configuración de eventos por empresa';
COMMENT ON TABLE calendar_events IS 'Instancias concretas de eventos en el calendario';
COMMENT ON TABLE event_tasks IS 'Tareas específicas dentro de cada evento';
COMMENT ON TABLE event_dependencies IS 'Dependencias entre tipos de eventos';

COMMENT ON COLUMN event_types.code IS 'Código único del evento (f29, f22, previred)';
COMMENT ON COLUMN event_types.applies_to_regimes IS 'Array de regímenes tributarios a los que aplica';
COMMENT ON COLUMN event_rules.recurrence_config IS 'Configuración JSONB de recurrencia específica de la empresa';
COMMENT ON COLUMN calendar_events.due_date IS 'Fecha de vencimiento del evento';
COMMENT ON COLUMN calendar_events.period_start IS 'Inicio del período al que aplica el evento';
COMMENT ON COLUMN calendar_events.period_end IS 'Fin del período al que aplica el evento';
