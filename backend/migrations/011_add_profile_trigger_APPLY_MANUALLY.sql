-- =====================================================================
-- APLICAR TODO ESTO EN SUPABASE DASHBOARD → SQL EDITOR
-- =====================================================================
-- Copiar y pegar TODO este archivo en Supabase Dashboard SQL Editor
-- La función ya existe pero el trigger debe crearse manualmente
-- =====================================================================

-- Primero asegurarnos de que la función existe (ejecutar otra vez no hace daño)
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_full_name TEXT;
    v_name TEXT;
    v_lastname TEXT;
BEGIN
    v_full_name := COALESCE(NEW.raw_user_meta_data->>'full_name', '');

    IF v_full_name != '' THEN
        v_name := SPLIT_PART(v_full_name, ' ', 1);
        v_lastname := TRIM(SUBSTRING(v_full_name FROM LENGTH(v_name) + 1));
    ELSE
        v_name := '';
        v_lastname := '';
    END IF;

    INSERT INTO public.profiles (
        id,
        email,
        full_name,
        name,
        lastname,
        phone,
        avatar_url,
        created_at,
        updated_at
    )
    VALUES (
        NEW.id,
        NEW.email,
        v_full_name,
        v_name,
        v_lastname,
        COALESCE(NEW.phone, NEW.raw_user_meta_data->>'phone', NULL),
        COALESCE(NEW.raw_user_meta_data->>'avatar_url', NEW.raw_user_meta_data->>'picture', NULL),
        NOW(),
        NOW()
    );

    RETURN NEW;
END;
$$;

-- Ahora crear el trigger en auth.users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- Add comment
COMMENT ON TRIGGER on_auth_user_created ON auth.users IS
    'Trigger that executes handle_new_user() after a new user is inserted into auth.users';

-- =====================================================================
-- VERIFICACIÓN: Ejecuta esto después para confirmar que funcionó
-- =====================================================================
/*
SELECT
    t.tgname as trigger_name,
    t.tgenabled as enabled,
    p.proname as function_name
FROM pg_trigger t
JOIN pg_proc p ON t.tgfoid = p.oid
WHERE t.tgname = 'on_auth_user_created';

-- Debería retornar:
-- trigger_name: on_auth_user_created
-- enabled: O
-- function_name: handle_new_user
*/
