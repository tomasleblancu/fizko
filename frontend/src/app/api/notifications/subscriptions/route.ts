import { NextRequest, NextResponse } from 'next/server'
import type {
  NotificationSubscriptionRequest,
  NotificationSubscriptionUpdateRequest,
} from '@/types/notification-subscription'
import { NotificationSubscriptionsService } from '@/services/notifications'

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

    // Delegate to service layer
    const subscriptions = await NotificationSubscriptionsService.list(companyId)

    return NextResponse.json({ data: subscriptions })
  } catch (error) {
    console.error('[Notification Subscriptions API] GET Error:', error)

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

    // Delegate to service layer
    const subscription = await NotificationSubscriptionsService.create(companyId, body)

    return NextResponse.json({ data: subscription })
  } catch (error) {
    console.error('[Notification Subscriptions API] POST Error:', error)

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
    const subscriptionId = searchParams.get('subscriptionId')

    if (!subscriptionId) {
      return NextResponse.json(
        { error: 'subscriptionId is required' },
        { status: 400 }
      )
    }

    const body: NotificationSubscriptionUpdateRequest = await request.json()

    // Delegate to service layer
    const subscription = await NotificationSubscriptionsService.update(subscriptionId, body)

    return NextResponse.json({ data: subscription })
  } catch (error) {
    console.error('[Notification Subscriptions API] PUT Error:', error)

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

    // Delegate to service layer
    await NotificationSubscriptionsService.delete(subscriptionId)

    return NextResponse.json({ message: 'Subscription deleted successfully' })
  } catch (error) {
    console.error('[Notification Subscriptions API] DELETE Error:', error)

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
