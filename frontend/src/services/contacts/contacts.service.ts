/**
 * Contacts Service
 *
 * Handles contact operations:
 * - Listing contacts with filters
 * - Data transformation
 */

import { createServiceClient } from '@/lib/supabase/server';
import type { Database } from '@/types/database';
import type { Contact, ContactType } from '@/types/contacts';

type ContactRow = Database['public']['Tables']['contacts']['Row'];

export interface ListContactsParams {
  companyId: string;
  contactType?: ContactType;
}

export class ContactsService {
  /**
   * List contacts for a company with optional type filter
   *
   * @param params - Query parameters
   * @returns List of contacts
   */
  static async list(params: ListContactsParams): Promise<Contact[]> {
    console.log(`[Contacts Service] Listing contacts for company ${params.companyId}`);

    const supabase = createServiceClient();

    // Build query
    let query = supabase
      .from('contacts')
      .select('*')
      .eq('company_id', params.companyId)
      .order('business_name', { ascending: true });

    // Apply optional contact type filter
    if (params.contactType) {
      query = query.eq('contact_type', params.contactType);
    }

    // Execute query
    const { data: contacts, error } = await query as { data: ContactRow[] | null; error: any };

    if (error) {
      console.error('[Contacts Service] Error fetching contacts:', error);
      throw new Error(`Failed to fetch contacts: ${error.message}`);
    }

    console.log(`[Contacts Service] Found ${contacts?.length || 0} contacts`);

    // Transform to response format
    return this.transformContacts(contacts || []);
  }

  /**
   * Get a single contact by ID
   *
   * @param contactId - Contact UUID
   * @returns Contact
   */
  static async getById(contactId: string): Promise<Contact> {
    console.log(`[Contacts Service] Fetching contact ${contactId}`);

    const supabase = createClient();

    const { data: contact, error } = await supabase
      .from('contacts')
      .select('*')
      .eq('id', contactId)
      .single() as { data: ContactRow | null; error: any };

    if (error || !contact) {
      console.error('[Contacts Service] Error fetching contact:', error);
      throw new Error(`Contact not found: ${error?.message || 'Unknown error'}`);
    }

    return this.transformContact(contact);
  }

  /**
   * Transform database rows to Contact format
   */
  private static transformContacts(contacts: ContactRow[]): Contact[] {
    return contacts.map((contact) => this.transformContact(contact));
  }

  /**
   * Transform single database row to Contact format
   */
  private static transformContact(contact: ContactRow): Contact {
    return {
      id: contact.id,
      rut: contact.rut,
      business_name: contact.business_name,
      trade_name: contact.trade_name,
      contact_type: contact.contact_type as ContactType,
      address: contact.address,
      phone: contact.phone,
      email: contact.email,
      created_at: contact.created_at,
      updated_at: contact.updated_at,
    };
  }
}
