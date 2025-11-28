import { createBrowserClient } from '@supabase/ssr';
import type { EventTemplate, CreateEventTemplateDto, UpdateEventTemplateDto } from '@/types/event-template';

export class EventTemplatesService {
  private static getSupabaseClient() {
    return createBrowserClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
    );
  }

  /**
   * List all event templates
   */
  static async listAll(): Promise<EventTemplate[]> {
    const supabase = this.getSupabaseClient();

    const { data, error } = await supabase
      .from('event_templates')
      .select('*')
      .order('category', { ascending: true })
      .order('name', { ascending: true });

    if (error) {
      console.error('[EventTemplatesService] Error fetching templates:', error);
      throw new Error(`Failed to fetch event templates: ${error.message}`);
    }

    return data as EventTemplate[];
  }

  /**
   * Get event template by ID
   */
  static async getById(id: string): Promise<EventTemplate | null> {
    const supabase = this.getSupabaseClient();

    const { data, error } = await supabase
      .from('event_templates')
      .select('*')
      .eq('id', id)
      .single();

    if (error) {
      if (error.code === 'PGRST116') {
        return null;
      }
      console.error('[EventTemplatesService] Error fetching template:', error);
      throw new Error(`Failed to fetch event template: ${error.message}`);
    }

    return data as EventTemplate;
  }

  /**
   * Create a new event template
   */
  static async create(dto: CreateEventTemplateDto): Promise<EventTemplate> {
    const supabase = this.getSupabaseClient();

    const { data, error } = await supabase
      .from('event_templates')
      .insert({
        code: dto.code,
        name: dto.name,
        description: dto.description || null,
        category: dto.category,
        authority: dto.authority || null,
        is_mandatory: dto.is_mandatory ?? false,
        applies_to_regimes: dto.applies_to_regimes || null,
        default_recurrence: dto.default_recurrence,
        metadata: dto.metadata || {},
        display_days_before: dto.display_days_before ?? 30,
      })
      .select()
      .single();

    if (error) {
      console.error('[EventTemplatesService] Error creating template:', error);
      throw new Error(`Failed to create event template: ${error.message}`);
    }

    return data as EventTemplate;
  }

  /**
   * Update an event template
   */
  static async update(id: string, dto: UpdateEventTemplateDto): Promise<EventTemplate> {
    const supabase = this.getSupabaseClient();

    const updateData: any = {};
    if (dto.code !== undefined) updateData.code = dto.code;
    if (dto.name !== undefined) updateData.name = dto.name;
    if (dto.description !== undefined) updateData.description = dto.description || null;
    if (dto.category !== undefined) updateData.category = dto.category;
    if (dto.authority !== undefined) updateData.authority = dto.authority || null;
    if (dto.is_mandatory !== undefined) updateData.is_mandatory = dto.is_mandatory;
    if (dto.applies_to_regimes !== undefined) updateData.applies_to_regimes = dto.applies_to_regimes || null;
    if (dto.default_recurrence !== undefined) updateData.default_recurrence = dto.default_recurrence;
    if (dto.metadata !== undefined) updateData.metadata = dto.metadata;
    if (dto.display_days_before !== undefined) updateData.display_days_before = dto.display_days_before;

    updateData.updated_at = new Date().toISOString();

    const { data, error } = await supabase
      .from('event_templates')
      .update(updateData)
      .eq('id', id)
      .select()
      .single();

    if (error) {
      console.error('[EventTemplatesService] Error updating template:', error);
      throw new Error(`Failed to update event template: ${error.message}`);
    }

    return data as EventTemplate;
  }

  /**
   * Delete an event template
   */
  static async delete(id: string): Promise<void> {
    const supabase = this.getSupabaseClient();

    const { error } = await supabase
      .from('event_templates')
      .delete()
      .eq('id', id);

    if (error) {
      console.error('[EventTemplatesService] Error deleting template:', error);
      throw new Error(`Failed to delete event template: ${error.message}`);
    }
  }
}
