/**
 * Notification Preferences Service
 *
 * Handles user notification preferences:
 * - Get preferences with defaults
 * - Update/upsert preferences
 * - Quiet hours, muted categories, rate limiting
 */

import { createServiceClient } from '@/lib/supabase/server';
import type { Database } from '@/types/database';
import type {
  NotificationPreferences,
  NotificationPreferencesRequest,
} from '@/types/notification-subscription';

type NotificationPreferencesRow = Database['public']['Tables']['user_notification_preferences']['Row'];

const DEFAULT_PREFERENCES: Omit<NotificationPreferences, 'id' | 'user_id' | 'company_id' | 'created_at' | 'updated_at'> = {
  notifications_enabled: true,
  quiet_hours_start: null,
  quiet_hours_end: null,
  quiet_days: null,
  muted_categories: null,
  muted_templates: [],
  max_notifications_per_day: 20,
  min_interval_minutes: 30,
};

export class NotificationPreferencesService {
  /**
   * Get notification preferences for a user
   *
   * Returns defaults if no preferences exist
   *
   * @param userId - User UUID
   * @param companyId - Optional company UUID for company-specific preferences
   * @returns Notification preferences
   */
  static async get(
    userId: string,
    companyId?: string
  ): Promise<NotificationPreferences> {
    console.log(`[Notification Preferences Service] Fetching preferences for user ${userId}`);

    const supabase = createServiceClient();

    let query = supabase
      .from('user_notification_preferences')
      .select('*')
      .eq('user_id', userId);

    if (companyId) {
      query = query.eq('company_id', companyId);
    } else {
      query = query.is('company_id', null);
    }

    const { data: preferences, error } = await query.single() as {
      data: NotificationPreferencesRow | null;
      error: any;
    };

    if (error && error.code !== 'PGRST116') { // Not found is ok
      console.error('[Notification Preferences Service] Error fetching preferences:', error);
      throw new Error(`Failed to fetch preferences: ${error.message}`);
    }

    // Return defaults if no preferences exist
    if (!preferences) {
      console.log('[Notification Preferences Service] No preferences found, returning defaults');
      return {
        ...DEFAULT_PREFERENCES,
        user_id: userId,
        company_id: companyId || null,
      } as NotificationPreferences;
    }

    return this.transformPreferences(preferences);
  }

  /**
   * Update or create notification preferences
   *
   * Uses upsert logic to handle both create and update
   *
   * @param userId - User UUID
   * @param updates - Preference updates
   * @returns Updated preferences
   */
  static async upsert(
    userId: string,
    updates: NotificationPreferencesRequest
  ): Promise<NotificationPreferences> {
    console.log(`[Notification Preferences Service] Upserting preferences for user ${userId}`);

    const supabase = createServiceClient();

    // Check if preferences exist
    let query = supabase
      .from('user_notification_preferences')
      .select('id')
      .eq('user_id', userId);

    if (updates.company_id) {
      query = query.eq('company_id', updates.company_id);
    } else {
      query = query.is('company_id', null);
    }

    const { data: existing } = await query.single() as { data: { id: string } | null; error: any };

    const updateData: any = {};
    if (updates.notifications_enabled !== undefined) updateData.notifications_enabled = updates.notifications_enabled;
    if (updates.quiet_hours_start !== undefined) updateData.quiet_hours_start = updates.quiet_hours_start;
    if (updates.quiet_hours_end !== undefined) updateData.quiet_hours_end = updates.quiet_hours_end;
    if (updates.quiet_days !== undefined) updateData.quiet_days = updates.quiet_days;
    if (updates.muted_categories !== undefined) updateData.muted_categories = updates.muted_categories;
    if (updates.muted_templates !== undefined) updateData.muted_templates = updates.muted_templates;
    if (updates.max_notifications_per_day !== undefined) updateData.max_notifications_per_day = updates.max_notifications_per_day;
    if (updates.min_interval_minutes !== undefined) updateData.min_interval_minutes = updates.min_interval_minutes;

    let result: NotificationPreferencesRow;

    if (existing) {
      // Update existing
      const { data, error } = await (supabase as any)
        .from('user_notification_preferences')
        .update(updateData)
        .eq('id', existing.id)
        .select()
        .single();

      if (error) {
        console.error('[Notification Preferences Service] Error updating:', error);
        throw new Error(`Failed to update preferences: ${error.message}`);
      }
      result = data;
    } else {
      // Create new
      const { data, error } = await (supabase as any)
        .from('user_notification_preferences')
        .insert({
          user_id: userId,
          company_id: updates.company_id || null,
          ...DEFAULT_PREFERENCES,
          ...updateData,
        })
        .select()
        .single();

      if (error) {
        console.error('[Notification Preferences Service] Error creating:', error);
        throw new Error(`Failed to create preferences: ${error.message}`);
      }
      result = data;
    }

    console.log('[Notification Preferences Service] Preferences saved successfully');

    return this.transformPreferences(result);
  }

  /**
   * Transform database row to NotificationPreferences format
   */
  private static transformPreferences(prefs: NotificationPreferencesRow): NotificationPreferences {
    return {
      id: prefs.id,
      user_id: prefs.user_id,
      company_id: prefs.company_id ?? undefined,
      notifications_enabled: prefs.notifications_enabled,
      quiet_hours_start: prefs.quiet_hours_start,
      quiet_hours_end: prefs.quiet_hours_end,
      quiet_days: prefs.quiet_days as any,
      muted_categories: prefs.muted_categories as any,
      muted_templates: (prefs.muted_templates as any) || [],
      max_notifications_per_day: prefs.max_notifications_per_day,
      min_interval_minutes: prefs.min_interval_minutes,
      created_at: prefs.created_at,
      updated_at: prefs.updated_at,
    };
  }
}
