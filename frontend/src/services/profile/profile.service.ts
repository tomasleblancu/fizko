/**
 * Profile Service
 *
 * Handles user profile operations:
 * - Get profile by user ID
 * - Update profile data
 * - Phone verification logic
 */

import { createServiceClient } from '@/lib/supabase/server';
import type { Database } from '@/types/database';
import type { Profile, ProfileUpdateRequest } from '@/types/profile';

type ProfileRow = Database['public']['Tables']['profiles']['Row'];

export class ProfileService {
  /**
   * Get user profile by user ID
   *
   * @param userId - User UUID
   * @returns User profile
   */
  static async getByUserId(userId: string): Promise<Profile> {
    console.log(`[Profile Service] Fetching profile for user ${userId}`);

    const supabase = createServiceClient();

    const { data: profile, error } = await supabase
      .from('profiles')
      .select('*')
      .eq('id', userId)
      .single() as { data: ProfileRow | null; error: any };

    if (error) {
      console.error('[Profile Service] Error fetching profile:', error);
      throw new Error(`Failed to fetch profile: ${error.message}`);
    }

    if (!profile) {
      throw new Error('Profile not found');
    }

    return this.transformProfile(profile);
  }

  /**
   * Update user profile
   *
   * Handles phone verification reset logic when phone number changes
   *
   * @param userId - User UUID
   * @param updates - Profile update data
   * @returns Updated profile
   */
  static async update(userId: string, updates: ProfileUpdateRequest): Promise<Profile> {
    console.log(`[Profile Service] Updating profile for user ${userId}`);

    const supabase = createServiceClient();

    // Check if phone is being updated
    const { data: currentProfile } = await supabase
      .from('profiles')
      .select('phone')
      .eq('id', userId)
      .single() as { data: { phone: string | null } | null; error: any };

    const updateData: any = { ...updates };

    // Reset phone verification if phone number changed
    if (updates.phone && currentProfile && updates.phone !== currentProfile.phone) {
      console.log('[Profile Service] Phone number changed, resetting verification');
      updateData.phone_verified = false;
      updateData.phone_verified_at = null;
    }

    const { data: updatedProfile, error } = await (supabase as any)
      .from('profiles')
      .update(updateData)
      .eq('id', userId)
      .select()
      .single();

    if (error) {
      console.error('[Profile Service] Error updating profile:', error);
      throw new Error(`Failed to update profile: ${error.message}`);
    }

    console.log('[Profile Service] Profile updated successfully');

    return this.transformProfile(updatedProfile);
  }

  /**
   * Transform database row to Profile format
   */
  private static transformProfile(profile: ProfileRow): Profile {
    return {
      id: profile.id,
      email: profile.email,
      name: profile.name,
      lastname: profile.lastname,
      phone: profile.phone,
      phone_verified: profile.phone_verified,
      phone_verified_at: profile.phone_verified_at,
      full_name: profile.full_name,
      company_name: profile.company_name,
      avatar_url: profile.avatar_url,
      rol: profile.rol,
      created_at: profile.created_at,
      updated_at: profile.updated_at,
    };
  }
}
