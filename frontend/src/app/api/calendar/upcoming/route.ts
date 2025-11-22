import { NextRequest, NextResponse } from 'next/server'
import type { UpcomingEventsResponse } from '@/types/calendar'
import { CalendarService } from '@/services/calendar/calendar.service'
import { createServiceClient } from '@/lib/supabase/server'

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

    // Create service client to bypass RLS (similar to tax-summary API)
    const supabase = createServiceClient()

    // Delegate to service layer with service client
    const events = await CalendarService.getUpcomingEventsWithTemplates(
      companyId,
      daysAhead,
      supabase
    )

    // Calculate date range for response
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const endDate = new Date(today)
    endDate.setDate(endDate.getDate() + daysAhead)

    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
    const endDateStr = `${endDate.getFullYear()}-${String(endDate.getMonth() + 1).padStart(2, '0')}-${String(endDate.getDate()).padStart(2, '0')}`

    const response: UpcomingEventsResponse = {
      data: events as any,
      total: events.length,
      period: {
        start: todayStr,
        end: endDateStr,
        days: daysAhead
      }
    }

    return NextResponse.json(response)
  } catch (error) {
    console.error('[Calendar Upcoming API] Error:', error)

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
