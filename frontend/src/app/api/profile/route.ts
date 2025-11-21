import { NextRequest, NextResponse } from 'next/server'
import type { ProfileUpdateRequest } from '@/types/profile'
import { ProfileService } from '@/services/profile'

export async function GET(request: NextRequest) {
  try {
    // TODO: Get user ID from auth session
    // For now, we'll expect it as a query param
    const searchParams = request.nextUrl.searchParams
    const userId = searchParams.get('userId')

    if (!userId) {
      return NextResponse.json(
        { error: 'userId is required' },
        { status: 400 }
      )
    }

    const profile = await ProfileService.getByUserId(userId)

    return NextResponse.json({ data: profile })
  } catch (error) {
    console.error('[Profile API] GET Error:', error)

    if (error instanceof Error) {
      return NextResponse.json(
        { error: error.message },
        { status: error.message.includes('not found') ? 404 : 400 }
      )
    }

    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function PATCH(request: NextRequest) {
  try {
    // TODO: Get user ID from auth session
    const searchParams = request.nextUrl.searchParams
    const userId = searchParams.get('userId')

    if (!userId) {
      return NextResponse.json(
        { error: 'userId is required' },
        { status: 400 }
      )
    }

    const body: ProfileUpdateRequest = await request.json()

    const profile = await ProfileService.update(userId, body)

    return NextResponse.json({ data: profile })
  } catch (error) {
    console.error('[Profile API] PATCH Error:', error)

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
