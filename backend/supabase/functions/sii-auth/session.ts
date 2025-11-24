/**
 * Session and profile management functions
 */

import type { SupabaseClient } from "jsr:@supabase/supabase-js@2";
import type { Session } from "./types.ts";

/**
 * Ensure user has a profile record
 */
export async function ensureUserProfile(
  supabase: SupabaseClient,
  userId: string,
  userEmail: string
): Promise<void> {
  console.log("[Profile] Checking if profile exists for user:", userId);

  const { data: existingProfile } = await supabase
    .from("profiles")
    .select("id")
    .eq("id", userId)
    .maybeSingle();

  if (existingProfile) {
    console.log("[Profile] Profile already exists");
    return;
  }

  console.log("[Profile] Creating profile for user:", userId);

  const { error: profileError } = await supabase.from("profiles").insert({
    id: userId,
    email: userEmail,
  });

  if (profileError) {
    console.error("[Profile] Error creating profile:", profileError);
    throw new Error(`Error al crear perfil: ${profileError.message}`);
  }

  console.log("[Profile] Profile created successfully");
}

/**
 * Create or update user-company session
 */
export async function createOrUpdateSession(
  supabase: SupabaseClient,
  userId: string,
  companyId: string,
  cookies: any[],
  userEmail: string
): Promise<Session> {
  // Ensure user has a profile first (sessions references profiles, not auth.users)
  await ensureUserProfile(supabase, userId, userEmail);

  console.log("[Session] Creating/updating session");

  const { data: session, error: sessionError } = await supabase
    .from("sessions")
    .upsert(
      {
        user_id: userId,
        company_id: companyId,
        is_active: true,
        cookies: cookies || {},
        resources: { user_email: userEmail },
        last_accessed_at: new Date().toISOString(),
      },
      { onConflict: "user_id,company_id" }
    )
    .select()
    .single();

  if (sessionError) {
    console.error("[Session] Error creating session:", sessionError);
    throw new Error(`Error al crear sesión: ${sessionError.message}`);
  }

  console.log(`[Session] Session created/updated: ${session.id}`);

  return session as Session;
}
