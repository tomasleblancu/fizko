import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
import { hasEnvVars } from "../utils";

export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({
    request,
  });

  // If the env vars are not set, skip proxy check. You can remove this
  // once you setup the project.
  if (!hasEnvVars) {
    return supabaseResponse;
  }

  // With Fluid compute, don't put this client in a global environment
  // variable. Always create a new one on each request.
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value),
          );
          supabaseResponse = NextResponse.next({
            request,
          });
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options),
          );
        },
      },
    },
  );

  // Do not run code between createServerClient and
  // supabase.auth.getUser(). A simple mistake could make it very hard to debug
  // issues with users being randomly logged out.

  const {
    data: { user },
  } = await supabase.auth.getUser();

  const pathname = request.nextUrl.pathname;

  // Public routes that don't require authentication
  const publicRoutes = [
    "/",
    "/como-funciona",
    "/terminos",
    "/privacidad",
    "/contacto",
  ];

  const isPublicRoute = publicRoutes.includes(pathname) ||
    pathname.startsWith("/login") ||
    pathname.startsWith("/auth") ||
    pathname.startsWith("/onboarding");

  if (!user && !isPublicRoute) {
    const url = request.nextUrl.clone();
    url.pathname = "/auth/login";
    return NextResponse.redirect(url);
  }

  // If authenticated, verify onboarding/setup flow
  if (user) {
    const pathname = request.nextUrl.pathname;

    // Check admin route protection
    if (pathname.startsWith("/admin")) {
      const { data: profile } = await supabase
        .from("profiles")
        .select("rol")
        .eq("id", user.id)
        .single();

      if (!profile || profile.rol !== "admin-fizko") {
        const url = request.nextUrl.clone();
        url.pathname = "/";
        url.searchParams.set("error", "unauthorized");
        return NextResponse.redirect(url);
      }
    }

    // Fetch user sessions with company settings
    const { data: sessions } = await supabase
      .from('sessions')
      .select(`
        *,
        company:companies(
          id,
          rut,
          settings:company_settings(is_initial_setup_complete)
        )
      `)
      .eq('user_id', user.id)
      .eq('is_active', true)
      .limit(1)
      .maybeSingle();

    // Usuario SIN sesión SII activa
    if (!sessions || !sessions.cookies || Object.keys(sessions.cookies).length === 0) {
      if (pathname.startsWith('/dashboard') || pathname === '/onboarding/setup') {
        const url = request.nextUrl.clone();
        url.pathname = '/onboarding/sii';
        return NextResponse.redirect(url);
      }
    }
    // Usuario CON sesión SII pero SIN setup completo
    else if (sessions.company && (!sessions.company.settings || !sessions.company.settings.is_initial_setup_complete)) {
      // Si intenta ir a dashboard, redirigir a /onboarding/setup
      if (pathname.startsWith('/dashboard')) {
        const url = request.nextUrl.clone();
        url.pathname = '/onboarding/setup';
        return NextResponse.redirect(url);
      }
    }
    // Usuario CON sesión SII y CON setup completo
    else if (sessions.company?.settings?.is_initial_setup_complete) {
      // Si está en cualquier ruta de onboarding, redirigir a dashboard
      if (pathname.startsWith('/onboarding')) {
        const url = request.nextUrl.clone();
        url.pathname = '/dashboard';
        return NextResponse.redirect(url);
      }
    }
  }

  // IMPORTANT: You *must* return the supabaseResponse object as it is.
  // If you're creating a new response object with NextResponse.next() make sure to:
  // 1. Pass the request in it, like so:
  //    const myNewResponse = NextResponse.next({ request })
  // 2. Copy over the cookies, like so:
  //    myNewResponse.cookies.setAll(supabaseResponse.cookies.getAll())
  // 3. Change the myNewResponse object to fit your needs, but avoid changing
  //    the cookies!
  // 4. Finally:
  //    return myNewResponse
  // If this is not done, you may be causing the browser and server to go out
  // of sync and terminate the user's session prematurely!

  return supabaseResponse;
}
