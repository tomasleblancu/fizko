/**
 * SII Authentication API Route
 *
 * Handles SII login and company data synchronization
 */

import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { SIIAuthService } from '@/services/sii/sii-auth.service';

export async function POST(request: NextRequest) {
  try {
    const { rut, password } = await request.json();

    // Validate input
    if (!rut || !password) {
      return NextResponse.json(
        { success: false, error: 'RUT y contraseña son requeridos' },
        { status: 400 }
      );
    }

    // Get authenticated user
    const supabase = await createClient();
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json(
        { success: false, error: 'No autenticado' },
        { status: 401 }
      );
    }

    // Get user email (required for profile creation)
    const userEmail = user.email;
    if (!userEmail) {
      return NextResponse.json(
        { success: false, error: 'Email de usuario no disponible' },
        { status: 400 }
      );
    }

    // Delegate to service layer
    const result = await SIIAuthService.authenticateAndSync(
      user.id,
      userEmail,
      rut,
      password
    );

    return NextResponse.json(result);
  } catch (error) {
    console.error('[SII Auth Route] Unexpected error:', error);
    return NextResponse.json(
      {
        success: false,
        error:
          error instanceof Error ? error.message : 'Error interno del servidor',
      },
      { status: 500 }
    );
  }
}
