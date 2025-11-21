import { createClient } from '@/lib/supabase/server'

export interface GetCurrentUserResponse {
  user: {
    id: string
    email?: string
    [key: string]: any
  } | null
}

export class AuthService {
  /**
   * Get the currently authenticated user
   * Uses server-side Supabase client with cookies
   */
  static async getCurrentUser(): Promise<GetCurrentUserResponse> {
    const supabase = await createClient()

    const {
      data: { user },
      error,
    } = await supabase.auth.getUser()

    if (error || !user) {
      return { user: null }
    }

    return { user }
  }
}
