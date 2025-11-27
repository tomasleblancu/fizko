/**
 * Company Setup Edge Function
 *
 * Completes initial company setup:
 * 1. Save company settings from onboarding questions
 * 2. Mark setup as complete
 * 3. Initialize company calendar (mandatory events + optional selected templates)
 * 4. Launch calendar sync task to generate concrete calendar events
 *
 * This function is called after SII authentication when the user completes
 * the initial setup wizard.
 */

import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

// Import types
import type {
  CompanySetupRequest,
  CompanySetupResponse,
} from "./types.ts";

// Import operations
import { saveCompanySettings } from "./settings.ts";
import { initializeCompanyCalendar } from "./calendar.ts";

// Import task functions
import { launchCalendarSyncTask } from "./tasks.ts";

// Main handler
Deno.serve(async (req: Request) => {
  // CORS headers
  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers":
      "authorization, x-client-info, apikey, content-type",
  };

  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    // Get auth token
    const authHeader = req.headers.get("Authorization");
    if (!authHeader) {
      return new Response(
        JSON.stringify({
          success: false,
          error: "No autenticado",
        }),
        {
          status: 401,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Initialize Supabase clients
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseAnonKey = Deno.env.get("SUPABASE_ANON_KEY")!;
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const backendUrl =
      Deno.env.get("BACKEND_URL") ||
      "https://fizko-v2-production.up.railway.app";

    // Client for auth verification (uses user's token)
    const authClient = createClient(supabaseUrl, supabaseAnonKey, {
      global: {
        headers: { Authorization: authHeader },
      },
    });

    // Client for privileged operations (uses service role key, bypasses RLS)
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Verify user is authenticated
    const {
      data: { user },
      error: userError,
    } = await authClient.auth.getUser();

    if (userError || !user) {
      return new Response(
        JSON.stringify({ success: false, error: "No autenticado" }),
        {
          status: 401,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    const userId = user.id;

    console.log(`[Company Setup] Starting setup for user: ${userId}`);

    // Parse request body
    const {
      company_id,
      settings,
      selected_template_ids,
    }: CompanySetupRequest = await req.json();

    if (!company_id) {
      return new Response(
        JSON.stringify({
          success: false,
          error: "company_id es requerido",
        }),
        {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    console.log(`[Company Setup] Processing company: ${company_id}`);
    console.log(`[Company Setup] User ID: ${userId}`);

    // Verify user has access to this company
    const { data: session, error: sessionError } = await supabase
      .from("sessions")
      .select("id")
      .eq("user_id", userId)
      .eq("company_id", company_id)
      .maybeSingle();

    console.log(`[Company Setup] Session query result:`, {
      session,
      sessionError,
      hasSession: !!session,
    });

    if (sessionError) {
      console.error(`[Company Setup] Session query error:`, sessionError);
      return new Response(
        JSON.stringify({
          success: false,
          error: `Error al verificar sesión: ${sessionError.message}`,
        }),
        {
          status: 500,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    if (!session) {
      console.warn(
        `[Company Setup] No session found for user ${userId} and company ${company_id}`
      );
      return new Response(
        JSON.stringify({
          success: false,
          error: "No tienes acceso a esta empresa",
        }),
        {
          status: 403,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // 1. Save company settings
    const savedSettings = await saveCompanySettings(
      supabase,
      company_id,
      settings
    );

    console.log(`[Company Setup] Settings saved: ${savedSettings.id}`);

    // 2. Initialize calendar
    const companyEvents = await initializeCompanyCalendar(
      supabase,
      company_id,
      selected_template_ids
    );

    console.log(
      `[Company Setup] Calendar initialized with ${companyEvents.length} events`
    );

    // 3. Launch calendar sync task to generate concrete events
    await launchCalendarSyncTask(backendUrl, company_id);

    const response: CompanySetupResponse = {
      success: true,
      settings_id: savedSettings.id,
      company_events_created: companyEvents.length,
      message: "Setup completado exitosamente",
    };

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("[Company Setup] Unexpected error:", error);
    return new Response(
      JSON.stringify({
        success: false,
        error: error instanceof Error ? error.message : "Error inesperado",
      }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  }
});
