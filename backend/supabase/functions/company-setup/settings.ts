/**
 * Company settings operations
 */

import type { SupabaseClient } from "jsr:@supabase/supabase-js@2";
import type {
  CompanySettingsInput,
  CompanySettings,
} from "./types.ts";

/**
 * Save or update company settings
 *
 * @param supabase - Supabase client (service role)
 * @param companyId - Company UUID
 * @param settings - Settings values from setup form
 * @returns Created or updated settings record
 */
export async function saveCompanySettings(
  supabase: SupabaseClient,
  companyId: string,
  settings: CompanySettingsInput
): Promise<CompanySettings> {
  console.log(`[Settings] Saving settings for company: ${companyId}`);

  // Check if settings already exist
  const { data: existing, error: fetchError } = await supabase
    .from("company_settings")
    .select("id, is_initial_setup_complete")
    .eq("company_id", companyId)
    .maybeSingle();

  if (fetchError) {
    console.error("[Settings] Error checking existing settings:", fetchError);
    throw new Error(`Failed to check existing settings: ${fetchError.message}`);
  }

  const updateData = {
    ...settings,
    is_initial_setup_complete: true,
    initial_setup_completed_at: new Date().toISOString(),
  };

  if (existing) {
    // Update existing settings
    console.log("[Settings] Updating existing settings");

    const { data, error } = await supabase
      .from("company_settings")
      .update(updateData)
      .eq("company_id", companyId)
      .select()
      .single();

    if (error) {
      console.error("[Settings] Error updating settings:", error);
      throw new Error(`Failed to update settings: ${error.message}`);
    }

    console.log("[Settings] Settings updated successfully");
    return data;
  } else {
    // Create new settings
    console.log("[Settings] Creating new settings");

    const { data, error } = await supabase
      .from("company_settings")
      .insert({
        company_id: companyId,
        ...updateData,
      })
      .select()
      .single();

    if (error) {
      console.error("[Settings] Error creating settings:", error);
      throw new Error(`Failed to create settings: ${error.message}`);
    }

    console.log("[Settings] Settings created successfully");
    return data;
  }
}
