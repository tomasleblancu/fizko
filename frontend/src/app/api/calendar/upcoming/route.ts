import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'
import type { Database } from '@/types/database'
import type { UpcomingEventsResponse } from '@/types/calendar'
import { parseLocalDate } from '@/shared/lib/date-utils'

// Create Supabase client for server-side operations
function getSupabaseClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!

  return createClient<Database>(supabaseUrl, supabaseKey)
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const companyId = searchParams.get('companyId')
    const daysAhead = parseInt(searchParams.get('daysAhead') || '30', 10)

    if (!companyId) {
      return NextResponse.json(
        { error: 'companyId is required' },
        { status: 400 }
      )
    }

    if (daysAhead < 1 || daysAhead > 365) {
      return NextResponse.json(
        { error: 'daysAhead must be between 1 and 365' },
        { status: 400 }
      )
    }

    const supabase = getSupabaseClient()

    // Calculate date range as ISO date strings (avoid timezone issues)
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const endDate = new Date(today)
    endDate.setDate(endDate.getDate() + daysAhead)

    // Format as YYYY-MM-DD directly to avoid timezone shifts
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
    const endDateStr = `${endDate.getFullYear()}-${String(endDate.getMonth() + 1).padStart(2, '0')}-${String(endDate.getDate()).padStart(2, '0')}`

    // Query upcoming calendar events
    // Note: This requires calendar_events and event_templates tables
    type CalendarEventWithTemplate = {
      id: string
      due_date: string
      status: string
      event_template: { code: string; name: string; display_days_before: number } | Array<{ code: string; name: string; display_days_before: number }>
    }

    const { data: events, error } = await supabase
      .from('calendar_events')
      .select(`
        id,
        due_date,
        status,
        event_template:event_templates!inner(
          code,
          name,
          display_days_before
        )
      `)
      .eq('company_id', companyId)
      .gte('due_date', todayStr)
      .lte('due_date', endDateStr)
      .order('due_date', { ascending: true }) as { data: CalendarEventWithTemplate[] | null; error: any }

    if (error) {
      console.error('Error fetching calendar events:', error)
      return NextResponse.json(
        { error: 'Failed to fetch calendar events' },
        { status: 500 }
      )
    }

    // Transform and filter events based on display_days_before
    const transformedEvents = (events || [])
      .map(event => {
        const dueDate = parseLocalDate(event.due_date)
        const daysUntilDue = Math.ceil((dueDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))

        // Handle the event_template which could be an array or object
        const template = Array.isArray(event.event_template)
          ? event.event_template[0]
          : event.event_template

        return {
          id: event.id,
          title: template?.name || 'Sin título',
          event_template: {
            code: template?.code || '',
            name: template?.name || '',
            display_days_before: template?.display_days_before || 30
          },
          due_date: event.due_date,
          days_until_due: daysUntilDue,
          status: event.status as any
        }
      })
      .filter(event => {
        // Only show events if they are within the display_days_before threshold
        return event.days_until_due <= event.event_template.display_days_before
      })

    const response: UpcomingEventsResponse = {
      data: transformedEvents,
      total: transformedEvents.length,
      period: {
        start: todayStr,
        end: endDateStr,
        days: daysAhead
      }
    }

    return NextResponse.json(response)
  } catch (error) {
    console.error('Error in calendar/upcoming route:', error)

    if (error instanceof Error) {
      return NextResponse.json(
        { error: error.message },
        { status: 400 }
      )
    }

    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
