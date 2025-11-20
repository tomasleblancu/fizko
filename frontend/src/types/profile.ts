/**
 * User Profile types
 */

export interface Profile {
  id: string
  email: string
  name: string | null
  lastname: string | null
  phone: string | null
  phone_verified: boolean
  phone_verified_at: string | null
  full_name: string | null
  company_name: string | null
  avatar_url: string | null
  rol: string | null
  created_at: string
  updated_at: string
}

export interface ProfileUpdateRequest {
  name?: string | null
  lastname?: string | null
  phone?: string | null
  full_name?: string | null
  company_name?: string | null
  avatar_url?: string | null
}

export interface ProfileResponse {
  data: Profile
}
