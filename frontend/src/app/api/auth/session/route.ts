import { NextResponse } from 'next/server'
import { AuthService } from '@/services/auth/auth.service'

export async function GET() {
  try {
    const result = await AuthService.getCurrentUser()

    if (!result.user) {
      return NextResponse.json({ user: null }, { status: 401 })
    }

    return NextResponse.json(result)
  } catch (error) {
    console.error('[Auth Session API] Error:', error)

    return NextResponse.json(
      { user: null, error: 'Internal server error' },
      { status: 500 }
    )
  }
}
