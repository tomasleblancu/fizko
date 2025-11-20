import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'
import type { Database } from '@/types/database'
import type {
  NotificationPreferences,
  NotificationPreferencesRequest,
} from '@/types/notification-subscription'

// Type for user_notification_preferences row from database
type NotificationPreferencesRow = Database['public']['Tables']['user_notification_preferences']['Row']

function getSupabaseClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!

  return createClient<Database>(supabaseUrl, supabaseKey)
}

const DEFAULT_PREFERENCES: NotificationPreferences = {
  notifications_enabled: true,
  quiet_hours_start: null,
  quiet_hours_end: null,
  quiet_days: null,
  muted_categories: null,
  muted_templates: [],
  max_notifications_per_day: 20,
  min_interval_minutes: 30,
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const userId = searchParams.get('userId')
    const companyId = searchParams.get('companyId')

    if (!userId) {
      return NextResponse.json(
        { error: 'userId is required' },
        { status: 400 }
      )
    }

    const supabase = getSupabaseClient()

    let query = supabase
      .from('user_notification_preferences')
      .select('*')
      .eq('user_id', userId)

    if (companyId) {
      query = query.eq('company_id', companyId)
    } else {
      query = query.is('company_id', null)
    }

    const { data: preferences, error } = await query.single() as { data: NotificationPreferencesRow | null; error: any }

    if (error && error.code !== 'PGRST116') { // Not found is ok
      console.error('Error fetching preferences:', error)
      return NextResponse.json(
        { error: 'Failed to fetch preferences' },
        { status: 500 }
      )
    }

    // Return defaults if no preferences exist
    if (!preferences) {
      return NextResponse.json({
        data: {
          ...DEFAULT_PREFERENCES,
          user_id: userId,
          company_id: companyId || null,
        }
      })
    }

    const response: NotificationPreferences = {
      id: preferences.id,
      user_id: preferences.user_id,
      company_id: preferences.company_id,
      notifications_enabled: preferences.notifications_enabled,
      quiet_hours_start: preferences.quiet_hours_start,
      quiet_hours_end: preferences.quiet_hours_end,
      quiet_days: preferences.quiet_days as any,
      muted_categories: preferences.muted_categories as any,
      muted_templates: (preferences.muted_templates as any) || [],
      max_notifications_per_day: preferences.max_notifications_per_day,
      min_interval_minutes: preferences.min_interval_minutes,
      created_at: preferences.created_at,
      updated_at: preferences.updated_at,
    }

    return NextResponse.json({ data: response })
  } catch (error) {
    console.error('Error in preferences GET:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function PUT(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const userId = searchParams.get('userId')

    if (!userId) {
      return NextResponse.json(
        { error: 'userId is required' },
        { status: 400 }
      )
    }

    const body: NotificationPreferencesRequest = await request.json()
    const supabase = getSupabaseClient()

    // Check if preferences exist
    let query = supabase
      .from('user_notification_preferences')
      .select('id')
      .eq('user_id', userId)

    if (body.company_id) {
      query = query.eq('company_id', body.company_id)
    } else {
      query = query.is('company_id', null)
    }

    const { data: existing } = await query.single() as { data: { id: string } | null; error: any }

    const updateData: any = {}
    if (body.notifications_enabled !== undefined) updateData.notifications_enabled = body.notifications_enabled
    if (body.quiet_hours_start !== undefined) updateData.quiet_hours_start = body.quiet_hours_start
    if (body.quiet_hours_end !== undefined) updateData.quiet_hours_end = body.quiet_hours_end
    if (body.quiet_days !== undefined) updateData.quiet_days = body.quiet_days
    if (body.muted_categories !== undefined) updateData.muted_categories = body.muted_categories
    if (body.muted_templates !== undefined) updateData.muted_templates = body.muted_templates
    if (body.max_notifications_per_day !== undefined) updateData.max_notifications_per_day = body.max_notifications_per_day
    if (body.min_interval_minutes !== undefined) updateData.min_interval_minutes = body.min_interval_minutes

    let result: NotificationPreferencesRow
    if (existing) {
      // Update existing - Using any cast to bypass Supabase type inference issue
      const { data, error } = await (supabase as any)
        .from('user_notification_preferences')
        .update(updateData)
        .eq('id', existing.id)
        .select()
        .single()

      if (error) throw error
      result = data
    } else {
      // Create new - Using any cast to bypass Supabase type inference issue
      const { data, error } = await (supabase as any)
        .from('user_notification_preferences')
        .insert({
          user_id: userId,
          company_id: body.company_id || null,
          ...DEFAULT_PREFERENCES,
          ...updateData,
        })
        .select()
        .single()

      if (error) throw error
      result = data
    }

    const response: NotificationPreferences = {
      id: result.id,
      user_id: result.user_id,
      company_id: result.company_id,
      notifications_enabled: result.notifications_enabled,
      quiet_hours_start: result.quiet_hours_start,
      quiet_hours_end: result.quiet_hours_end,
      quiet_days: result.quiet_days as any,
      muted_categories: result.muted_categories as any,
      muted_templates: (result.muted_templates as any) || [],
      max_notifications_per_day: result.max_notifications_per_day,
      min_interval_minutes: result.min_interval_minutes,
      created_at: result.created_at,
      updated_at: result.updated_at,
    }

    return NextResponse.json({
      data: response,
      message: 'Preferencias actualizadas exitosamente'
    })
  } catch (error) {
    console.error('Error in preferences PUT:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
