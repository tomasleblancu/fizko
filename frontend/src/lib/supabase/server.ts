import { createServerClient } from "@supabase/ssr";
import { createClient as createSupabaseClient } from "@supabase/supabase-js";
import { cookies } from "next/headers";

/**
 * Especially important if using Fluid compute: Don't put this client in a
 * global variable. Always create a new client within each function when using
 * it.
 */
export async function createClient() {
  const cookieStore = await cookies();

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options),
            );
          } catch {
            // The `setAll` method was called from a Server Component.
            // This can be ignored if you have proxy refreshing
            // user sessions.
          }
        },
      },
    },
  );
}

/**
 * Creates a Supabase admin client with service role key for admin operations.
 * Use only in server-side API routes for operations that bypass RLS.
 *
 * IMPORTANT: This client bypasses ALL RLS policies. Use with caution.
 *
 * This uses the standard @supabase/supabase-js client (not @supabase/ssr)
 * to avoid cookie interference with the service role key.
 */
export function createServiceClient() {
  // Check if service role key is available
  if (!process.env.SUPABASE_SERVICE_ROLE_KEY) {
    console.error('[Supabase] SUPABASE_SERVICE_ROLE_KEY is not set!');
    throw new Error('SUPABASE_SERVICE_ROLE_KEY environment variable is required for admin operations');
  }

  console.log('[Supabase] Creating admin client with service role key (bypasses RLS)');

  // Use the standard Supabase client (not SSR) to avoid cookie interference
  return createSupabaseClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY,
    {
      auth: {
        persistSession: false,
        autoRefreshToken: false,
      },
    }
  );
}
