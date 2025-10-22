-- =====================================================================
-- Migration: Auto-create Profile Trigger
-- =====================================================================
-- Description: Creates a trigger to automatically create a user profile
--              when a new user signs up via Supabase Auth
-- Version: 011
-- Date: 2025-01-22
--
-- This ensures every user in auth.users has a corresponding profile
-- in the public.profiles table, preventing errors when the app
-- tries to access user profile data.
-- =====================================================================

-- =====================================================================
-- FUNCTION: Create Profile for New User
-- =====================================================================

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
    -- Extract full_name from user metadata (populated by OAuth providers like Google)
    v_full_name := COALESCE(NEW.raw_user_meta_data->>'full_name', '');

    -- Split full_name into name and lastname
    -- Example: "John Doe" -> name: "John", lastname: "Doe"
    IF v_full_name != '' THEN
        v_name := SPLIT_PART(v_full_name, ' ', 1);
        v_lastname := TRIM(SUBSTRING(v_full_name FROM LENGTH(v_name) + 1));
    ELSE
        v_name := '';
        v_lastname := '';
    END IF;

    -- Insert new profile record
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

-- =====================================================================
-- TRIGGER: Execute on New User Creation
-- =====================================================================

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- =====================================================================
-- COMMENTS
-- =====================================================================

COMMENT ON FUNCTION public.handle_new_user() IS
    'Automatically creates a profile in public.profiles when a new user is created in auth.users. '
    'Extracts user data from OAuth metadata (Google, etc.) and splits full_name into name/lastname.';

COMMENT ON TRIGGER on_auth_user_created ON auth.users IS
    'Trigger that executes handle_new_user() after a new user is inserted into auth.users';

-- =====================================================================
-- BACKFILL: Create Profiles for Existing Users (Optional)
-- =====================================================================
-- Uncomment the following block if you have existing users without profiles

/*
DO $$
DECLARE
    v_user RECORD;
    v_full_name TEXT;
    v_name TEXT;
    v_lastname TEXT;
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

        RAISE NOTICE 'Created profile for user: %', v_user.email;
    END LOOP;
END;
$$;
*/

-- =====================================================================
-- END OF MIGRATION
-- =====================================================================
