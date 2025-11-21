/**
 * Notification Subscriptions Service
 *
 * Handles notification subscriptions (company-template relationships):
 * - List subscriptions with template data
 * - Create, update, delete subscriptions
 * - Join with notification templates
 */

import { createServiceClient } from '@/lib/supabase/server';
import type { Database } from '@/types/database';
import type {
  NotificationSubscription,
  NotificationSubscriptionRequest,
  NotificationSubscriptionUpdateRequest,
} from '@/types/notification-subscription';

type NotificationSubscriptionRow = Database['public']['Tables']['notification_subscriptions']['Row'];

export class NotificationSubscriptionsService {
  /**
   * List notification subscriptions for a company
   *
   * Includes full template data via join
   *
   * @param companyId - Company UUID
   * @returns List of subscriptions with template data
   */
  static async list(companyId: string): Promise<NotificationSubscription[]> {
    console.log(`[Notification Subscriptions Service] Listing subscriptions for company ${companyId}`);

    const supabase = createServiceClient();

    // Fetch subscriptions with template details (join)
    const { data: subscriptions, error } = await supabase
      .from('notification_subscriptions')
      .select(`
        *,
        template:notification_templates(*)
      `)
      .eq('company_id', companyId) as { data: any[] | null; error: any };

    if (error) {
      console.error('[Notification Subscriptions Service] Error fetching subscriptions:', error);
      throw new Error(`Failed to fetch subscriptions: ${error.message}`);
    }

    console.log(`[Notification Subscriptions Service] Found ${subscriptions?.length || 0} subscriptions`);

    return this.transformSubscriptions(subscriptions || []);
  }

  /**
   * Create a new subscription
   *
   * @param companyId - Company UUID
   * @param request - Subscription creation data
   * @returns Created subscription with template data
   */
  static async create(
    companyId: string,
    request: NotificationSubscriptionRequest
  ): Promise<NotificationSubscription> {
    console.log(`[Notification Subscriptions Service] Creating subscription for company ${companyId}`);

    const supabase = createServiceClient();

    const { data: subscription, error } = await (supabase as any)
      .from('notification_subscriptions')
      .insert({
        company_id: companyId,
        notification_template_id: request.notification_template_id,
        is_enabled: request.is_enabled ?? true,
        custom_timing_config: request.custom_timing_config ?? null,
        custom_message_template: request.custom_message_template ?? null,
      })
      .select(`
        *,
        template:notification_templates(*)
      `)
      .single();

    if (error) {
      console.error('[Notification Subscriptions Service] Error creating subscription:', error);
      throw new Error(`Failed to create subscription: ${error.message}`);
    }

    console.log('[Notification Subscriptions Service] Subscription created successfully');

    return this.transformSubscription(subscription);
  }

  /**
   * Update an existing subscription
   *
   * @param subscriptionId - Subscription UUID
   * @param updates - Subscription update data
   * @returns Updated subscription with template data
   */
  static async update(
    subscriptionId: string,
    updates: NotificationSubscriptionUpdateRequest
  ): Promise<NotificationSubscription> {
    console.log(`[Notification Subscriptions Service] Updating subscription ${subscriptionId}`);

    const supabase = createServiceClient();

    const { data: subscription, error } = await (supabase as any)
      .from('notification_subscriptions')
      .update(updates)
      .eq('id', subscriptionId)
      .select(`
        *,
        template:notification_templates(*)
      `)
      .single();

    if (error) {
      console.error('[Notification Subscriptions Service] Error updating subscription:', error);
      throw new Error(`Failed to update subscription: ${error.message}`);
    }

    console.log('[Notification Subscriptions Service] Subscription updated successfully');

    return this.transformSubscription(subscription);
  }

  /**
   * Delete a subscription
   *
   * @param subscriptionId - Subscription UUID
   */
  static async delete(subscriptionId: string): Promise<void> {
    console.log(`[Notification Subscriptions Service] Deleting subscription ${subscriptionId}`);

    const supabase = createServiceClient();

    const { error } = await supabase
      .from('notification_subscriptions')
      .delete()
      .eq('id', subscriptionId);

    if (error) {
      console.error('[Notification Subscriptions Service] Error deleting subscription:', error);
      throw new Error(`Failed to delete subscription: ${error.message}`);
    }

    console.log('[Notification Subscriptions Service] Subscription deleted successfully');
  }

  /**
   * Transform database rows to NotificationSubscription format
   */
  private static transformSubscriptions(subscriptions: any[]): NotificationSubscription[] {
    return subscriptions.map((sub) => this.transformSubscription(sub));
  }

  /**
   * Transform single database row to NotificationSubscription format
   */
  private static transformSubscription(sub: any): NotificationSubscription {
    return {
      id: sub.id,
      company_id: sub.company_id,
      notification_template_id: sub.notification_template_id,
      is_enabled: sub.is_enabled,
      custom_timing_config: sub.custom_timing_config,
      custom_message_template: sub.custom_message_template,
      channels: sub.channels || ['whatsapp'],
      filters: sub.filters,
      created_at: sub.created_at,
      updated_at: sub.updated_at,
      template: {
        id: sub.template.id,
        code: sub.template.code,
        name: sub.template.name,
        description: sub.template.description,
        category: sub.template.category,
        entity_type: sub.template.entity_type,
        message_template: sub.template.message_template,
        timing_config: sub.template.timing_config,
        priority: sub.template.priority,
        is_active: sub.template.is_active,
        can_repeat: sub.template.can_repeat,
        max_repeats: sub.template.max_repeats,
        repeat_interval_hours: sub.template.repeat_interval_hours,
        auto_assign_to_new_companies: sub.template.auto_assign_to_new_companies,
        created_at: sub.template.created_at,
        updated_at: sub.template.updated_at,
      },
    };
  }
}
