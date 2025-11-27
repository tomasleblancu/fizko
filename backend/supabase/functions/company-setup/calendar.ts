/**
 * Calendar initialization operations
 */

import type { SupabaseClient } from "jsr:@supabase/supabase-js@2";
import type { EventTemplate, CompanyEvent } from "./types.ts";

/**
 * Initialize company calendar
 *
 * Creates company_events for:
 * 1. All mandatory event templates (is_mandatory = true)
 * 2. Any additional templates specified by IDs
 *
 * @param supabase - Supabase client (service role)
 * @param companyId - Company UUID
 * @param selectedTemplateIds - Optional: additional template IDs to enable
 * @returns Array of created company events
 */
export async function initializeCompanyCalendar(
  supabase: SupabaseClient,
  companyId: string,
  selectedTemplateIds?: string[]
): Promise<CompanyEvent[]> {
  console.log(`[Calendar] Initializing calendar for company: ${companyId}`);

  // 1. Get mandatory event templates
  const { data: mandatoryTemplates, error: mandatoryError } = await supabase
    .from("event_templates")
    .select("id, code, name, is_mandatory")
    .eq("is_mandatory", true);

  if (mandatoryError) {
    console.error("[Calendar] Error fetching mandatory templates:", mandatoryError);
    throw new Error(`Failed to fetch mandatory event templates: ${mandatoryError.message}`);
  }

  console.log(`[Calendar] Found ${mandatoryTemplates?.length || 0} mandatory templates`);

  // 2. Get selected templates (if any)
  let selectedTemplates: EventTemplate[] = [];
  if (selectedTemplateIds && selectedTemplateIds.length > 0) {
    const { data, error } = await supabase
      .from("event_templates")
      .select("id, code, name, is_mandatory")
      .in("id", selectedTemplateIds);

    if (error) {
      console.error("[Calendar] Error fetching selected templates:", error);
      // Don't throw - continue with mandatory templates only
    } else {
      selectedTemplates = data || [];
      console.log(`[Calendar] Found ${selectedTemplates.length} selected templates`);
    }
  }

  // 3. Combine templates (dedupe by ID)
  const allTemplates = [...(mandatoryTemplates || []), ...selectedTemplates];
  const uniqueTemplates = Array.from(
    new Map(allTemplates.map(t => [t.id, t])).values()
  );

  console.log(`[Calendar] Creating company events for ${uniqueTemplates.length} templates`);

  // 4. Check which company_events already exist
  const { data: existingEvents, error: existingError } = await supabase
    .from("company_events")
    .select("event_template_id")
    .eq("company_id", companyId);

  if (existingError) {
    console.error("[Calendar] Error checking existing company events:", existingError);
    throw new Error(`Failed to check existing company events: ${existingError.message}`);
  }

  const existingTemplateIds = new Set(
    (existingEvents || []).map(e => e.event_template_id)
  );

  // 5. Filter out templates that already have company_events
  const templatesToCreate = uniqueTemplates.filter(
    t => !existingTemplateIds.has(t.id)
  );

  if (templatesToCreate.length === 0) {
    console.log("[Calendar] All templates already have company events");
    return [];
  }

  console.log(`[Calendar] Creating ${templatesToCreate.length} new company events`);

  // 6. Create company_events
  const companyEventsToInsert = templatesToCreate.map(template => ({
    company_id: companyId,
    event_template_id: template.id,
    is_active: true,
  }));

  const { data: createdEvents, error: insertError } = await supabase
    .from("company_events")
    .insert(companyEventsToInsert)
    .select();

  if (insertError) {
    console.error("[Calendar] Error creating company events:", insertError);
    throw new Error(`Failed to create company events: ${insertError.message}`);
  }

  console.log(`[Calendar] Successfully created ${createdEvents?.length || 0} company events`);

  return createdEvents || [];
}
