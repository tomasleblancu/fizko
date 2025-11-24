/**
 * SII Onboarding Edge Function
 *
 * Processes company onboarding after SII authentication:
 * 1. Create or update company with SII data
 * 2. Save encrypted SII credentials
 * 3. Launch document sync tasks (for new companies only)
 * 4. Create user-company session
 * 5. Check if initial setup is needed
 *
 * Note: SII authentication is done by the backend (Selenium scraping).
 * This function receives the auth result and processes the onboarding.
 */

import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

// Import types
import type {
  SIIOnboardRequest,
  SIIOnboardResponse,
} from "./types.ts";

// Import helpers
import { normalizeRUT } from "./helpers.ts";

// Import company functions
import {
  upsertCompany,
  saveCompanyCredentials,
  checkNeedsSetup,
} from "./company.ts";

// Import session functions
import { createOrUpdateSession } from "./session.ts";

// Import task functions
import { launchDocumentSyncTasks } from "./tasks.ts";

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
        JSON.stringify({ success: false, error: "No autenticado", needs_setup: false }),
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
        JSON.stringify({ success: false, error: "No autenticado", needs_setup: false }),
        {
          status: 401,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    const userId = user.id;
    const userEmail = user.email!;

    console.log(`[SII Onboard] Starting onboarding for user: ${userId}`);

    // Parse request body - receive data from backend SII login
    const {
      rut,
      contribuyente_info,
      encrypted_password,
      cookies,
    }: SIIOnboardRequest = await req.json();

    if (!rut || !contribuyente_info || !encrypted_password) {
      return new Response(
        JSON.stringify({
          success: false,
          error: "RUT, contribuyente_info y encrypted_password son requeridos",
          needs_setup: false,
        }),
        {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Normalize RUT
    const normalizedRut = normalizeRUT(rut);
    console.log(`[SII Onboard] Processing RUT: ${normalizedRut}`);

    // 1. Create or update company
    const { company, isNew } = await upsertCompany(
      supabase,
      normalizedRut,
      contribuyente_info
    );

    console.log(
      `[SII Onboard] Company ${isNew ? "created" : "updated"}: ${company.id}`
    );

    // 2. Save encrypted SII credentials
    await saveCompanyCredentials(
      supabase,
      company.id,
      encrypted_password
    );

    // 3. Launch document sync tasks (only for new companies)
    if (isNew) {
      await launchDocumentSyncTasks(backendUrl, company.id);
    }

    // 4. Create or update session
    const session = await createOrUpdateSession(
      supabase,
      userId,
      company.id,
      cookies || [],
      userEmail
    );

    // 5. Check if company needs initial setup
    const needsSetup = await checkNeedsSetup(supabase, company.id);

    console.log(`[SII Onboard] Setup required: ${needsSetup}`);

    const response: SIIOnboardResponse = {
      success: true,
      company_id: company.id,
      session_id: session.id,
      needs_setup: needsSetup,
      message: isNew
        ? "Empresa creada exitosamente"
        : "Onboarding completado",
    };

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("[SII Onboard] Unexpected error:", error);
    return new Response(
      JSON.stringify({
        success: false,
        error: error instanceof Error ? error.message : "Error inesperado",
        needs_setup: false,
      }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  }
});
