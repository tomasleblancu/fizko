/**
 * SII Authentication Edge Function
 *
 * Handles complete SII authentication and company onboarding flow:
 * 1. Normalize RUT
 * 2. Authenticate with SII backend (FastAPI)
 * 3. Create or update company with SII data
 * 4. Save encrypted SII credentials
 * 5. Launch document sync tasks (for new companies only)
 * 6. Create user-company session
 * 7. Check if initial setup is needed
 */

import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

// Import types
import type {
  SIIAuthRequest,
  SIIAuthResponse,
  SIILoginResponse,
} from "./types.ts";

// Import helpers
import { normalizeRUT, extractRutBody, extractDV } from "./helpers.ts";

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
        JSON.stringify({ success: false, error: "No autenticado" }),
        {
          status: 401,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Initialize Supabase client with service role for privileged operations
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const backendUrl =
      Deno.env.get("BACKEND_URL") ||
      "https://fizko-v2-production.up.railway.app";

    const supabase = createClient(supabaseUrl, supabaseServiceKey, {
      global: {
        headers: { Authorization: authHeader },
      },
    });

    // Verify user is authenticated
    const {
      data: { user },
      error: userError,
    } = await supabase.auth.getUser();

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
    const userEmail = user.email!;

    console.log(`[SII Auth] Starting authentication for user: ${userId}`);

    // Parse request body
    const { rut, password }: SIIAuthRequest = await req.json();

    if (!rut || !password) {
      return new Response(
        JSON.stringify({
          success: false,
          error: "RUT y contraseña son requeridos",
        }),
        {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // 1. Normalize RUT
    const normalizedRut = normalizeRUT(rut);
    const rutBody = extractRutBody(rut);
    const dv = extractDV(rut);

    console.log(`[SII Auth] Normalized RUT: ${normalizedRut}`);

    // 2. Authenticate with SII backend
    console.log("[SII Auth] Calling backend SII login");
    const siiResponse = await fetch(`${backendUrl}/api/sii/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        rut: rutBody,
        dv: dv,
        password: password,
      }),
    });

    if (!siiResponse.ok) {
      const errorText = await siiResponse.text();
      console.error("[SII Auth] Backend error:", errorText);
      return new Response(
        JSON.stringify({
          success: false,
          error: "Error al autenticar con SII",
          needs_setup: false,
        }),
        {
          status: 401,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    const siiData: SIILoginResponse = await siiResponse.json();

    if (!siiData.success) {
      return new Response(
        JSON.stringify({
          success: false,
          error: siiData.message || "Error al autenticar con SII",
          needs_setup: false,
        }),
        {
          status: 401,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    console.log("[SII Auth] SII authentication successful");

    // 3. Create or update company
    const { company, isNew } = await upsertCompany(
      supabase,
      normalizedRut,
      siiData.contribuyente_info!
    );

    console.log(
      `[SII Auth] Company ${isNew ? "created" : "updated"}: ${company.id}`
    );

    // 4. Save encrypted SII credentials
    await saveCompanyCredentials(
      supabase,
      company.id,
      siiData.encrypted_password!
    );

    // 5. Launch document sync tasks (only for new companies)
    if (isNew) {
      await launchDocumentSyncTasks(backendUrl, company.id);
    }

    // 6. Create or update session
    const session = await createOrUpdateSession(
      supabase,
      userId,
      company.id,
      siiData.cookies || [],
      userEmail
    );

    // 7. Check if company needs initial setup
    const needsSetup = await checkNeedsSetup(supabase, company.id);

    console.log(`[SII Auth] Setup required: ${needsSetup}`);

    const response: SIIAuthResponse = {
      success: true,
      company_id: company.id,
      session_id: session.id,
      needs_setup: needsSetup,
      message: isNew
        ? "Empresa creada exitosamente"
        : "Autenticación exitosa",
    };

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("[SII Auth] Unexpected error:", error);
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
