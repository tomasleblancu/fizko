-- Migration: Event History System
-- Description: Add event_history table to track all actions and changes on calendar events
-- Author: Claude
-- Date: 2025-10-27

-- ============================================================================
-- 1. CREATE ENUM TYPE
-- ============================================================================

CREATE TYPE event_history_type AS ENUM (
    'created',           -- Evento creado
    'status_changed',    -- Cambio de estado
    'note_added',        -- Nota agregada
    'document_attached', -- Documento adjunto
    'task_completed',    -- Tarea completada
    'reminder_sent',     -- Recordatorio enviado
    'updated',           -- Actualización general
    'completed',         -- Evento completado
    'cancelled',         -- Evento cancelado
    'system_action'      -- Acción automática del sistema
);

COMMENT ON TYPE event_history_type IS 'Tipos de eventos en el historial de calendar_events';

-- ============================================================================
-- 2. CREATE TABLE
-- ============================================================================

CREATE TABLE event_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relación con el evento del calendario
    calendar_event_id UUID NOT NULL REFERENCES calendar_events(id) ON DELETE CASCADE,

    -- Usuario que realizó la acción (NULL para acciones automáticas)
    user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,

    -- Tipo de evento/acción
    event_type event_history_type NOT NULL,

    -- Título/resumen del evento
    title TEXT NOT NULL,

    -- Descripción detallada (opcional)
    description TEXT,

    -- Datos adicionales en formato JSON
    -- Puede contener: cambios específicos, datos del documento, folio, etc.
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- 3. INDEXES
-- ============================================================================

-- Índice principal para consultar historial por evento
CREATE INDEX idx_event_history_calendar_event
    ON event_history(calendar_event_id, created_at DESC);

-- Índice para consultar por tipo de evento
CREATE INDEX idx_event_history_event_type
    ON event_history(event_type);

-- Índice para consultar acciones de un usuario
CREATE INDEX idx_event_history_user
    ON event_history(user_id, created_at DESC)
    WHERE user_id IS NOT NULL;

-- Índice para búsquedas por fecha
CREATE INDEX idx_event_history_created_at
    ON event_history(created_at DESC);

-- ============================================================================
-- 4. ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE event_history ENABLE ROW LEVEL SECURITY;

-- Los usuarios pueden ver el historial de eventos de su empresa
CREATE POLICY "event_history_select_policy" ON event_history
    FOR SELECT USING (
        calendar_event_id IN (
            SELECT id FROM calendar_events
            WHERE company_id IN (
                SELECT company_id FROM sessions
                WHERE user_id = auth.uid() AND is_active = true
            )
        )
    );

-- Los usuarios pueden insertar en el historial de eventos de su empresa
CREATE POLICY "event_history_insert_policy" ON event_history
    FOR INSERT WITH CHECK (
        calendar_event_id IN (
            SELECT id FROM calendar_events
            WHERE company_id IN (
                SELECT company_id FROM sessions
                WHERE user_id = auth.uid() AND is_active = true
            )
        )
    );

-- ============================================================================
-- 5. TRIGGER: Auto-crear entrada de historial al crear evento
-- ============================================================================

CREATE OR REPLACE FUNCTION create_event_history_on_calendar_event_create()
RETURNS TRIGGER AS $$
BEGIN
    -- Crear entrada en el historial cuando se crea un evento del calendario
    INSERT INTO event_history (
        calendar_event_id,
        user_id,
        event_type,
        title,
        description,
        metadata
    ) VALUES (
        NEW.id,
        NULL,  -- NULL porque es creación automática del sistema
        'created',
        'Evento creado',
        'El evento "' || NEW.title || '" fue creado en el calendario',
        jsonb_build_object(
            'due_date', NEW.due_date,
            'status', NEW.status,
            'auto_generated', NEW.auto_generated
        )
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_create_event_history_on_calendar_event_create
    AFTER INSERT ON calendar_events
    FOR EACH ROW
    EXECUTE FUNCTION create_event_history_on_calendar_event_create();

-- ============================================================================
-- 6. TRIGGER: Auto-crear entrada de historial al cambiar estado
-- ============================================================================

CREATE OR REPLACE FUNCTION create_event_history_on_status_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Solo crear entrada si el estado cambió
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO event_history (
            calendar_event_id,
            user_id,
            event_type,
            title,
            description,
            metadata
        ) VALUES (
            NEW.id,
            NULL,  -- TODO: Capturar user_id del contexto si está disponible
            'status_changed',
            'Estado cambiado',
            'El estado cambió de "' || OLD.status || '" a "' || NEW.status || '"',
            jsonb_build_object(
                'old_status', OLD.status,
                'new_status', NEW.status,
                'completion_date', NEW.completion_date
            )
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_create_event_history_on_status_change
    AFTER UPDATE ON calendar_events
    FOR EACH ROW
    WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION create_event_history_on_status_change();

-- ============================================================================
-- 7. COMMENTS
-- ============================================================================

COMMENT ON TABLE event_history IS 'Historial de acciones y eventos en calendar_events para auditoría y contexto';

COMMENT ON COLUMN event_history.calendar_event_id IS 'Referencia al evento del calendario';
COMMENT ON COLUMN event_history.user_id IS 'Usuario que realizó la acción (NULL para acciones automáticas del sistema)';
COMMENT ON COLUMN event_history.event_type IS 'Tipo de acción/evento registrado';
COMMENT ON COLUMN event_history.title IS 'Título corto del evento en el historial';
COMMENT ON COLUMN event_history.description IS 'Descripción detallada de lo que ocurrió';
COMMENT ON COLUMN event_history.metadata IS 'Datos adicionales en formato JSON (cambios, documentos, etc.)';
COMMENT ON COLUMN event_history.created_at IS 'Timestamp de cuando ocurrió el evento';
