/**
 * Personnel Service
 *
 * Handles people/personnel operations:
 * - Listing people with filters and pagination
 * - Search by name and RUT
 * - Data transformation
 */

import { createServiceClient } from '@/lib/supabase/server';
import type { Database } from '@/types/database';
import type { Person, PersonStatus } from '@/types/personnel';

type PersonRow = Database['public']['Tables']['people']['Row'];

export interface ListPeopleParams {
  companyId: string;
  status?: PersonStatus;
  search?: string;
  page?: number;
  pageSize?: number;
}

export interface ListPeopleResponse {
  data: Person[];
  total: number;
  page: number;
  page_size: number;
}

export class PersonnelService {
  /**
   * List people for a company with filters and pagination
   *
   * @param params - Query parameters
   * @returns Paginated list of people
   */
  static async list(params: ListPeopleParams): Promise<ListPeopleResponse> {
    const page = params.page || 1;
    const pageSize = params.pageSize || 50;

    console.log(`[Personnel Service] Listing people for company ${params.companyId}, page ${page}`);

    const supabase = createServiceClient();

    // Build query
    let query = supabase
      .from('people')
      .select('*', { count: 'exact' })
      .eq('company_id', params.companyId);

    // Apply optional status filter
    if (params.status) {
      query = query.eq('status', params.status);
    }

    // Apply optional search filter
    if (params.search) {
      query = query.or(
        `first_name.ilike.%${params.search}%,last_name.ilike.%${params.search}%,rut.ilike.%${params.search}%`
      );
    }

    // Apply pagination
    const from = (page - 1) * pageSize;
    const to = from + pageSize - 1;
    query = query.range(from, to);

    // Order by last name, first name
    query = query
      .order('last_name', { ascending: true })
      .order('first_name', { ascending: true });

    // Execute query
    const { data: people, error, count } = await query as {
      data: PersonRow[] | null;
      error: any;
      count: number | null;
    };

    if (error) {
      console.error('[Personnel Service] Error fetching people:', error);
      throw new Error(`Failed to fetch people: ${error.message}`);
    }

    console.log(`[Personnel Service] Found ${count || 0} people`);

    // Transform to response format
    const transformedPeople = this.transformPeople(people || []);

    return {
      data: transformedPeople,
      total: count || 0,
      page,
      page_size: pageSize,
    };
  }

  /**
   * Get a single person by ID
   *
   * @param personId - Person UUID
   * @returns Person
   */
  static async getById(personId: string): Promise<Person> {
    console.log(`[Personnel Service] Fetching person ${personId}`);

    const supabase = createServiceClient();

    const { data: person, error } = await supabase
      .from('people')
      .select('*')
      .eq('id', personId)
      .single() as { data: PersonRow | null; error: any };

    if (error || !person) {
      console.error('[Personnel Service] Error fetching person:', error);
      throw new Error(`Person not found: ${error?.message || 'Unknown error'}`);
    }

    return this.transformPerson(person);
  }

  /**
   * Transform database rows to Person format
   */
  private static transformPeople(people: PersonRow[]): Person[] {
    return people.map((person) => this.transformPerson(person));
  }

  /**
   * Transform single database row to Person format
   */
  private static transformPerson(person: PersonRow): Person {
    return {
      id: person.id,
      company_id: person.company_id,
      rut: person.rut,
      first_name: person.first_name,
      last_name: person.last_name,
      email: person.email,
      phone: person.phone,
      birth_date: person.birth_date,
      position_title: person.position_title,
      contract_type: person.contract_type as any,
      hire_date: person.hire_date,
      base_salary: Number(person.base_salary),
      afp_provider: person.afp_provider,
      afp_percentage: person.afp_percentage ? Number(person.afp_percentage) : null,
      health_provider: person.health_provider,
      health_plan: person.health_plan,
      health_percentage: person.health_percentage ? Number(person.health_percentage) : null,
      health_fixed_amount: person.health_fixed_amount ? Number(person.health_fixed_amount) : null,
      bank_name: person.bank_name,
      bank_account_type: person.bank_account_type as any,
      bank_account_number: person.bank_account_number,
      status: person.status as PersonStatus,
      termination_date: person.termination_date,
      termination_reason: person.termination_reason,
      notes: person.notes,
      photo_url: person.photo_url,
      created_at: person.created_at,
      updated_at: person.updated_at,
    };
  }
}
