import { NextRequest, NextResponse } from 'next/server'
import type { NotificationPreferencesRequest } from '@/types/notification-subscription'
import { NotificationPreferencesService } from '@/services/notifications'

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

    // Delegate to service layer
    const preferences = await NotificationPreferencesService.get(
      userId,
      companyId || undefined
    )

    return NextResponse.json({ data: preferences })
  } catch (error) {
    console.error('[Notification Preferences API] GET Error:', error)

    if (error instanceof Error) {
      return NextResponse.json(
        { error: error.message },
        { status: 500 }
      )
    }

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

    // Delegate to service layer
    const preferences = await NotificationPreferencesService.upsert(userId, body)

    return NextResponse.json({
      data: preferences,
      message: 'Preferencias actualizadas exitosamente'
    })
  } catch (error) {
    console.error('[Notification Preferences API] PUT Error:', error)

    if (error instanceof Error) {
      return NextResponse.json(
        { error: error.message },
        { status: 500 }
      )
    }

    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
