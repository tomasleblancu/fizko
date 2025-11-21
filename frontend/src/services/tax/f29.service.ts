/**
 * F29 Service
 *
 * Handles Form 29 (Declaración Mensual de IVA) operations:
 * - Listing forms with filters
 * - Data transformation
 */

import { createServiceClient } from '@/lib/supabase/server';
import type { Database } from '@/types/database';
import type { F29Form, F29Status, FormType } from '@/types/f29';

type Form29Row = Database['public']['Tables']['form29']['Row'];

export interface ListF29Params {
  companyId: string;
  formType?: FormType;
  year?: number;
  month?: number;
}

export interface ListF29Response {
  data: F29Form[];
  total: number;
}

export class F29Service {
  /**
   * List F29 forms for a company with optional filters
   *
   * @param params - Query parameters
   * @returns List of F29 forms with count
   */
  static async list(params: ListF29Params): Promise<ListF29Response> {
    console.log(`[F29 Service] Listing forms for company ${params.companyId}`);

    const supabase = createServiceClient();

    // Build query
    let query = supabase
      .from('form29')
      .select('*', { count: 'exact' })
      .eq('company_id', params.companyId)
      .order('period_year', { ascending: false })
      .order('period_month', { ascending: false });

    // Apply optional year filter
    if (params.year) {
      query = query.eq('period_year', params.year);
    }

    // Apply optional month filter
    if (params.month) {
      query = query.eq('period_month', params.month);
    }

    // Execute query
    const { data: forms, error, count } = await query as {
      data: Form29Row[] | null;
      error: any;
      count: number | null;
    };

    if (error) {
      console.error('[F29 Service] Error fetching forms:', error);
      throw new Error(`Failed to fetch F29 forms: ${error.message}`);
    }

    console.log(`[F29 Service] Found ${count || 0} forms`);

    // Transform to response format
    const transformedForms = this.transformForms(forms || []);

    return {
      data: transformedForms,
      total: count || 0,
    };
  }

  /**
   * Get a single F29 form by ID
   *
   * @param formId - Form UUID
   * @returns F29 form
   */
  static async getById(formId: string): Promise<F29Form> {
    console.log(`[F29 Service] Fetching form ${formId}`);

    const supabase = createClient();

    const { data: form, error } = await supabase
      .from('form29')
      .select('*')
      .eq('id', formId)
      .single() as { data: Form29Row | null; error: any };

    if (error || !form) {
      console.error('[F29 Service] Error fetching form:', error);
      throw new Error(`Form not found: ${error?.message || 'Unknown error'}`);
    }

    return this.transformForm(form);
  }

  /**
   * Transform database rows to F29Form format
   */
  private static transformForms(forms: Form29Row[]): F29Form[] {
    return forms.map((form) => this.transformForm(form));
  }

  /**
   * Transform single database row to F29Form format
   */
  private static transformForm(form: Form29Row): F29Form {
    return {
      id: form.id,
      company_id: form.company_id,
      period_year: form.period_year,
      period_month: form.period_month,
      total_sales: Number(form.total_sales),
      taxable_sales: Number(form.taxable_sales),
      exempt_sales: Number(form.exempt_sales),
      sales_tax: Number(form.sales_tax),
      total_purchases: Number(form.total_purchases),
      taxable_purchases: Number(form.taxable_purchases),
      purchases_tax: Number(form.purchases_tax),
      iva_to_pay: Number(form.iva_to_pay),
      iva_credit: Number(form.iva_credit),
      net_iva: Number(form.net_iva),
      status: form.status as F29Status,
      revision_number: form.revision_number,
      submission_date: form.submission_date,
      extra_data: form.extra_data as Record<string, any> | null,
      created_at: form.created_at,
      updated_at: form.updated_at,
    };
  }
}
