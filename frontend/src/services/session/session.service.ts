/**
 * Session Service
 *
 * Handles user-company session management
 */

import { createServiceClient } from '@/lib/supabase/server';
import type { SIICookie } from '@/types/sii.types';

interface Session {
  id: string;
  user_id: string;
  company_id: string;
  is_active: boolean;
  cookies: any;
  last_accessed_at: string;
  created_at: string;
  updated_at: string;
}

export class SessionService {
  /**
   * Create or update user-company session with SII cookies
   *
   * IMPORTANT: This method ensures the user has a profile before creating the session,
   * since sessions table has a foreign key to profiles(id), not auth.users(id).
   *
   * @param userId - User UUID from Supabase auth
   * @param companyId - Company UUID
   * @param cookies - SII session cookies
   * @param userEmail - User email (for profile creation if needed)
   * @returns Session record
   */
  static async createOrUpdate(
    userId: string,
    companyId: string,
    cookies: SIICookie[],
    userEmail: string
  ): Promise<Session> {
    const serviceClient = createServiceClient();

    // Ensure user has a profile (sessions references profiles, not auth.users)
    await this.ensureUserProfile(userId, userEmail);

    console.log('[Session Service] Creating or updating session');

    const { data: session, error: sessionError } = await serviceClient
      .from('sessions')
      .upsert(
        {
          user_id: userId,
          company_id: companyId,
          is_active: true,
          cookies: cookies || {},
          last_accessed_at: new Date().toISOString(),
        },
        {
          onConflict: 'user_id,company_id',
        }
      )
      .select()
      .single();

    if (sessionError) {
      console.error('[Session Service] Error creating session:', sessionError);
      throw new Error(`Error al crear sesión: ${sessionError.message}`);
    }

    console.log('[Session Service] Session created/updated:', session.id);

    return session;
  }

  /**
   * Ensure user has a profile record
   *
   * Sessions table has a foreign key to profiles(id), so we must ensure
   * the profile exists before creating a session.
   */
  private static async ensureUserProfile(
    userId: string,
    userEmail: string
  ): Promise<void> {
    const serviceClient = createServiceClient();

    console.log('[Session Service] Checking if profile exists for user:', userId);

    // Check if profile exists
    const { data: existingProfile } = await serviceClient
      .from('profiles')
      .select('id')
      .eq('id', userId)
      .maybeSingle();

    if (existingProfile) {
      console.log('[Session Service] Profile already exists');
      return;
    }

    // Create profile if it doesn't exist
    console.log('[Session Service] Creating profile for user:', userId);

    const { error: profileError } = await serviceClient
      .from('profiles')
      .insert({
        id: userId,
        email: userEmail,
      });

    if (profileError) {
      console.error('[Session Service] Error creating profile:', profileError);
      throw new Error(`Error al crear perfil: ${profileError.message}`);
    }

    console.log('[Session Service] Profile created successfully');
  }
}
