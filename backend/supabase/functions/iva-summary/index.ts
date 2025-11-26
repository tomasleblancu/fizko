/**
 * IVA Summary Edge Function
 *
 * Calculates complete IVA summary for a company and period:
 * - Débito fiscal (from sales)
 * - Crédito fiscal (from purchases)
 * - Balance (débito - crédito)
 * - Previous month credit
 * - Overdue IVA credit
 * - PPM (Provisional Monthly Payment)
 * - Retención (from honorarios)
 * - Reverse charge withholding
 */

import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

// Import types
import type { IvaSummaryRequest } from "./types.ts";

// Import helpers
import { calculatePeriodRange } from "./helpers.ts";

// Import calculation functions
import { calculateIvaSummary } from "./calculations.ts";

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
        JSON.stringify({ error: "Missing authorization header" }),
        {
          status: 401,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Initialize Supabase client
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseAnonKey = Deno.env.get("SUPABASE_ANON_KEY")!;

    const supabase = createClient(supabaseUrl, supabaseAnonKey, {
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
      return new Response(JSON.stringify({ error: "Unauthorized" }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // Parse request - support both GET and POST
    let company_id: string;
    let period: string | undefined;

    if (req.method === "GET") {
      const url = new URL(req.url);
      company_id = url.searchParams.get("companyId") || "";
      period = url.searchParams.get("period") || undefined;
    } else {
      const body: IvaSummaryRequest = await req.json();
      company_id = body.company_id;
      period = body.period;
    }

    if (!company_id) {
      return new Response(
        JSON.stringify({ error: "company_id or companyId is required" }),
        {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Calculate date range
    const [periodStart, periodEnd] = calculatePeriodRange(period || null);

    // Calculate IVA summary
    const result = await calculateIvaSummary(
      supabase,
      company_id,
      periodStart,
      periodEnd
    );

    return new Response(JSON.stringify(result), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("Error in iva-summary function:", error);
    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : "Unknown error",
      }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  }
});
