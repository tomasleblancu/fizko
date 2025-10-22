-- =====================================================================
-- Migration: Backfill Profiles for Existing Users
-- =====================================================================
-- Description: Creates profiles for users who registered before the
--              trigger was applied
-- Version: 012
-- Date: 2025-01-22
--
-- IMPORTANTE: Solo ejecutar DESPUÉS de aplicar 011_add_profile_trigger.sql
-- =====================================================================

-- Ver cuántos usuarios no tienen perfil
SELECT
    COUNT(*) as users_without_profile
FROM auth.users u
LEFT JOIN public.profiles p ON p.id = u.id
WHERE p.id IS NULL;

-- Si hay usuarios sin perfil, ejecutar este script:

DO $$
DECLARE
    v_user RECORD;
    v_full_name TEXT;
    v_name TEXT;
    v_lastname TEXT;
    v_count INTEGER := 0;
BEGIN
    -- Loop through all users who don't have a profile yet
    FOR v_user IN
        SELECT u.*
        FROM auth.users u
        LEFT JOIN public.profiles p ON p.id = u.id
        WHERE p.id IS NULL
    LOOP
        -- Extract and split full_name
        v_full_name := COALESCE(v_user.raw_user_meta_data->>'full_name', '');

        IF v_full_name != '' THEN
            v_name := SPLIT_PART(v_full_name, ' ', 1);
            v_lastname := TRIM(SUBSTRING(v_full_name FROM LENGTH(v_name) + 1));
        ELSE
            v_name := '';
            v_lastname := '';
        END IF;

        -- Insert profile
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
            v_user.id,
            v_user.email,
            v_full_name,
            v_name,
            v_lastname,
            COALESCE(v_user.phone, v_user.raw_user_meta_data->>'phone', NULL),
            COALESCE(v_user.raw_user_meta_data->>'avatar_url', v_user.raw_user_meta_data->>'picture', NULL),
            v_user.created_at,
            NOW()
        );

        v_count := v_count + 1;
        RAISE NOTICE 'Created profile for user: % (email: %)', v_user.id, v_user.email;
    END LOOP;

    RAISE NOTICE 'Backfill completed. Created % profiles.', v_count;
END;
$$;

-- Verificar que todos los usuarios ahora tengan perfil
SELECT
    COUNT(*) as users_without_profile
FROM auth.users u
LEFT JOIN public.profiles p ON p.id = u.id
WHERE p.id IS NULL;

-- Debería retornar 0

-- =====================================================================
-- END OF MIGRATION
-- =====================================================================
