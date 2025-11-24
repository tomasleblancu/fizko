/**
 * Company management functions
 */

import type { SupabaseClient } from "jsr:@supabase/supabase-js@2";
import type { Company, ContribuyenteInfo } from "./types.ts";
import { buildCompanyData } from "./helpers.ts";

/**
 * Create or update company_tax_info
 */
export async function upsertCompanyTaxInfo(
  supabase: SupabaseClient,
  companyId: string,
  contribInfo: ContribuyenteInfo
): Promise<void> {
  const activities = contribInfo?.actividades_economicas || [];
  const primaryActivity = activities[0];

  const taxInfoData = {
    company_id: companyId,
    sii_activity_code: primaryActivity?.codigo || null,
    sii_activity_name: primaryActivity?.nombre || null,
    start_of_activities_date: contribInfo?.fecha_inicio_actividades || null,
    extra_data: contribInfo || {},
  };

  const { error } = await supabase
    .from("company_tax_info")
    .upsert(taxInfoData, { onConflict: "company_id" });

  if (error) {
    console.error("[Company Tax Info] Error upserting:", error);
    throw new Error(`Error al guardar info tributaria: ${error.message}`);
  }
}

/**
 * Create or update company from SII contributor data
 */
export async function upsertCompany(
  supabase: SupabaseClient,
  normalizedRut: string,
  contribInfo: ContribuyenteInfo
): Promise<{ company: Company; isNew: boolean }> {
  // Try to find existing company
  const { data: existingCompany } = await supabase
    .from("companies")
    .select("*")
    .eq("rut", normalizedRut)
    .maybeSingle();

  const companyData = buildCompanyData(normalizedRut, contribInfo);

  if (!existingCompany) {
    // Create new company
    console.log(`[Company] Creating new company with RUT: ${normalizedRut}`);

    const { data: newCompany, error: companyError } = await supabase
      .from("companies")
      .insert(companyData)
      .select()
      .single();

    if (companyError) {
      console.error("[Company] Error creating company:", companyError);
      throw new Error(`Error al crear empresa: ${companyError.message}`);
    }

    // Create company_tax_info
    await upsertCompanyTaxInfo(supabase, newCompany.id, contribInfo);

    return { company: newCompany as Company, isNew: true };
  } else {
    // Update existing company
    console.log(`[Company] Company already exists with RUT: ${normalizedRut}`);

    if (contribInfo?.razon_social || contribInfo?.nombre) {
      const { error: updateError } = await supabase
        .from("companies")
        .update(companyData)
        .eq("id", existingCompany.id);

      if (updateError) {
        console.error("[Company] Error updating company:", updateError);
        throw new Error(`Error updating company: ${updateError.message}`);
      }
    }

    // Update company_tax_info
    await upsertCompanyTaxInfo(supabase, existingCompany.id, contribInfo);

    return { company: existingCompany as Company, isNew: false };
  }
}

/**
 * Save encrypted SII credentials to company
 */
export async function saveCompanyCredentials(
  supabase: SupabaseClient,
  companyId: string,
  encryptedPassword: string
): Promise<void> {
  console.log("[Company] Saving encrypted credentials");

  const { error: credError } = await supabase
    .from("companies")
    .update({ sii_password: encryptedPassword })
    .eq("id", companyId);

  if (credError) {
    console.error("[Company] Error saving credentials:", credError);
    throw new Error(`Error al guardar credenciales: ${credError.message}`);
  }
}

/**
 * Check if company needs initial setup
 */
export async function checkNeedsSetup(
  supabase: SupabaseClient,
  companyId: string
): Promise<boolean> {
  const { data: settings } = await supabase
    .from("company_settings")
    .select("is_initial_setup_complete")
    .eq("company_id", companyId)
    .maybeSingle();

  return !settings || !settings.is_initial_setup_complete;
}
