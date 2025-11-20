import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'
import type { Database } from '@/types/database'
import type { Profile, ProfileUpdateRequest } from '@/types/profile'

// Type for profiles row from database
type ProfileRow = Database['public']['Tables']['profiles']['Row']

function getSupabaseClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!

  return createClient<Database>(supabaseUrl, supabaseKey)
}

export async function GET(request: NextRequest) {
  try {
    const supabase = getSupabaseClient()

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

    const { data: profile, error } = await supabase
      .from('profiles')
      .select('*')
      .eq('id', userId)
      .single() as { data: ProfileRow | null; error: any }

    if (error) {
      console.error('Error fetching profile:', error)
      return NextResponse.json(
        { error: 'Failed to fetch profile' },
        { status: 500 }
      )
    }

    if (!profile) {
      return NextResponse.json(
        { error: 'Profile not found' },
        { status: 404 }
      )
    }

    const response: Profile = {
      id: profile.id,
      email: profile.email,
      name: profile.name,
      lastname: profile.lastname,
      phone: profile.phone,
      phone_verified: profile.phone_verified,
      phone_verified_at: profile.phone_verified_at,
      full_name: profile.full_name,
      company_name: profile.company_name,
      avatar_url: profile.avatar_url,
      rol: profile.rol,
      created_at: profile.created_at,
      updated_at: profile.updated_at,
    }

    return NextResponse.json({ data: response })
  } catch (error) {
    console.error('Error in profile GET:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function PATCH(request: NextRequest) {
  try {
    const supabase = getSupabaseClient()

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

    // Check if phone is being updated
    const { data: currentProfile } = await supabase
      .from('profiles')
      .select('phone')
      .eq('id', userId)
      .single() as { data: { phone: string | null } | null; error: any }

    const updateData: any = { ...body }

    // Reset phone verification if phone number changed
    if (body.phone && currentProfile && body.phone !== currentProfile.phone) {
      updateData.phone_verified = false
      updateData.phone_verified_at = null
    }

    const { data: updatedProfile, error } = await (supabase as any)
      .from('profiles')
      .update(updateData)
      .eq('id', userId)
      .select()
      .single()

    if (error) {
      console.error('Error updating profile:', error)
      return NextResponse.json(
        { error: 'Failed to update profile' },
        { status: 500 }
      )
    }

    const response: Profile = {
      id: updatedProfile.id,
      email: updatedProfile.email,
      name: updatedProfile.name,
      lastname: updatedProfile.lastname,
      phone: updatedProfile.phone,
      phone_verified: updatedProfile.phone_verified,
      phone_verified_at: updatedProfile.phone_verified_at,
      full_name: updatedProfile.full_name,
      company_name: updatedProfile.company_name,
      avatar_url: updatedProfile.avatar_url,
      rol: updatedProfile.rol,
      created_at: updatedProfile.created_at,
      updated_at: updatedProfile.updated_at,
    }

    return NextResponse.json({ data: response })
  } catch (error) {
    console.error('Error in profile PATCH:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
