-- Fix event history trigger to use event_template.title instead of calendar_events.title
-- This is needed after removing title/description columns from calendar_events

CREATE OR REPLACE FUNCTION create_event_history_on_calendar_event_create()
RETURNS TRIGGER AS $$
DECLARE
    v_event_title TEXT;
BEGIN
    -- Get title from event_template
    SELECT title INTO v_event_title
    FROM event_template
    WHERE id = NEW.event_template_id;

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
        'El evento "' || COALESCE(v_event_title, 'Sin título') || '" fue creado en el calendario',
        jsonb_build_object(
            'due_date', NEW.due_date,
            'status', NEW.status,
            'auto_generated', NEW.auto_generated,
            'event_template_id', NEW.event_template_id
        )
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Comment explaining the change
COMMENT ON FUNCTION create_event_history_on_calendar_event_create() IS
    'Creates event history entry when calendar event is created. Fetches title from event_template since calendar_events no longer stores title/description directly.';
