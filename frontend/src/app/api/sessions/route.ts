import { NextRequest, NextResponse } from 'next/server'
import { SessionsService } from '@/services/session/sessions.service'
import { createClient } from '@/lib/supabase/server'

export async function GET(request: NextRequest) {
  try {
    // Verify authentication first
    const supabase = await createClient()
    const { data: { user }, error: authError } = await supabase.auth.getUser()

    if (authError || !user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    // Fetch sessions using the service
    const sessions = await SessionsService.list({ userId: user.id })
    return NextResponse.json(sessions)
  } catch (error) {
    console.error('[Sessions API] Error:', error)

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
