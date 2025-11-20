import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'
import type { Database } from '@/types/database'
import type {
  NotificationSubscription,
  NotificationSubscriptionRequest,
  NotificationSubscriptionUpdateRequest,
} from '@/types/notification-subscription'
import type { NotificationTemplate } from '@/types/notification-template'

function getSupabaseClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!

  return createClient<Database>(supabaseUrl, supabaseKey)
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const companyId = searchParams.get('companyId')

    if (!companyId) {
      return NextResponse.json(
        { error: 'companyId is required' },
        { status: 400 }
      )
    }

    const supabase = getSupabaseClient()

    // Fetch subscriptions with template details (join)
    const { data: subscriptions, error } = await supabase
      .from('notification_subscriptions')
      .select(`
        *,
        template:notification_templates(*)
      `)
      .eq('company_id', companyId)

    if (error) {
      console.error('Error fetching subscriptions:', error)
      return NextResponse.json(
        { error: 'Failed to fetch subscriptions' },
        { status: 500 }
      )
    }

    const response: NotificationSubscription[] = (subscriptions || []).map((sub: any) => ({
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
    }))

    return NextResponse.json({ data: response })
  } catch (error) {
    console.error('Error in subscriptions GET:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const companyId = searchParams.get('companyId')

    if (!companyId) {
      return NextResponse.json(
        { error: 'companyId is required' },
        { status: 400 }
      )
    }

    const body: NotificationSubscriptionRequest = await request.json()
    const supabase = getSupabaseClient()

    const { data: subscription, error } = await supabase
      .from('notification_subscriptions')
      .insert({
        company_id: companyId,
        notification_template_id: body.notification_template_id,
        is_enabled: body.is_enabled ?? true,
        custom_timing_config: body.custom_timing_config ?? null,
        custom_message_template: body.custom_message_template ?? null,
      })
      .select(`
        *,
        template:notification_templates(*)
      `)
      .single()

    if (error) {
      console.error('Error creating subscription:', error)
      return NextResponse.json(
        { error: 'Failed to create subscription' },
        { status: 500 }
      )
    }

    const response: NotificationSubscription = {
      id: subscription.id,
      company_id: subscription.company_id,
      notification_template_id: subscription.notification_template_id,
      is_enabled: subscription.is_enabled,
      custom_timing_config: subscription.custom_timing_config,
      custom_message_template: subscription.custom_message_template,
      channels: subscription.channels || ['whatsapp'],
      filters: subscription.filters,
      created_at: subscription.created_at,
      updated_at: subscription.updated_at,
      template: subscription.template as any,
    }

    return NextResponse.json({ data: response })
  } catch (error) {
    console.error('Error in subscriptions POST:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function PUT(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const subscriptionId = searchParams.get('subscriptionId')

    if (!subscriptionId) {
      return NextResponse.json(
        { error: 'subscriptionId is required' },
        { status: 400 }
      )
    }

    const body: NotificationSubscriptionUpdateRequest = await request.json()
    const supabase = getSupabaseClient()

    const { data: subscription, error } = await supabase
      .from('notification_subscriptions')
      .update(body)
      .eq('id', subscriptionId)
      .select(`
        *,
        template:notification_templates(*)
      `)
      .single()

    if (error) {
      console.error('Error updating subscription:', error)
      return NextResponse.json(
        { error: 'Failed to update subscription' },
        { status: 500 }
      )
    }

    const response: NotificationSubscription = {
      id: subscription.id,
      company_id: subscription.company_id,
      notification_template_id: subscription.notification_template_id,
      is_enabled: subscription.is_enabled,
      custom_timing_config: subscription.custom_timing_config,
      custom_message_template: subscription.custom_message_template,
      channels: subscription.channels || ['whatsapp'],
      filters: subscription.filters,
      created_at: subscription.created_at,
      updated_at: subscription.updated_at,
      template: subscription.template as any,
    }

    return NextResponse.json({ data: response })
  } catch (error) {
    console.error('Error in subscriptions PUT:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const subscriptionId = searchParams.get('subscriptionId')

    if (!subscriptionId) {
      return NextResponse.json(
        { error: 'subscriptionId is required' },
        { status: 400 }
      )
    }

    const supabase = getSupabaseClient()

    const { error } = await supabase
      .from('notification_subscriptions')
      .delete()
      .eq('id', subscriptionId)

    if (error) {
      console.error('Error deleting subscription:', error)
      return NextResponse.json(
        { error: 'Failed to delete subscription' },
        { status: 500 }
      )
    }

    return NextResponse.json({ message: 'Subscription deleted successfully' })
  } catch (error) {
    console.error('Error in subscriptions DELETE:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
