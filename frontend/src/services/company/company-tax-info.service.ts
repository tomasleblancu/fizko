/**
 * Company Tax Info Service
 *
 * Handles CRUD operations for company_tax_info table
 */

import { createServiceClient } from '@/lib/supabase/server';
import type { ContribuyenteInfo } from '@/types/sii.types';

export class CompanyTaxInfoService {
  /**
   * Create or update company_tax_info from SII contributor data
   *
   * @param companyId - Company UUID
   * @param contribInfo - Contributor information from SII
   */
  static async upsert(
    companyId: string,
    contribInfo: ContribuyenteInfo
  ): Promise<void> {
    const serviceClient = createServiceClient();

    // Check if tax info already exists
    const { data: existingTaxInfo } = await serviceClient
      .from('company_tax_info')
      .select('id')
      .eq('company_id', companyId)
      .maybeSingle();

    const taxInfoData = this.buildTaxInfoData(companyId, contribInfo);

    if (!existingTaxInfo) {
      console.log('[Company Tax Info Service] Creating company_tax_info');

      const { error } = await serviceClient
        .from('company_tax_info')
        .insert(taxInfoData);

      if (error) {
        console.error('[Company Tax Info Service] Error creating:', error);
        throw new Error(`Error creating tax info: ${error.message}`);
      }

      console.log('[Company Tax Info Service] Created successfully');
    } else {
      console.log('[Company Tax Info Service] Updating existing company_tax_info');

      // Don't update company_id on update
      const { company_id, ...updateData } = taxInfoData;

      const { error } = await serviceClient
        .from('company_tax_info')
        .update(updateData)
        .eq('company_id', companyId);

      if (error) {
        console.error('[Company Tax Info Service] Error updating:', error);
        throw new Error(`Error updating tax info: ${error.message}`);
      }

      console.log('[Company Tax Info Service] Updated successfully');
    }
  }

  /**
   * Build company_tax_info data object from contributor info
   */
  private static buildTaxInfoData(
    companyId: string,
    contribInfo: ContribuyenteInfo
  ) {
    const representante =
      contribInfo.representantes && contribInfo.representantes.length > 0
        ? contribInfo.representantes[0]
        : null;

    const actividadPrincipal =
      contribInfo.actividades && contribInfo.actividades.length > 0
        ? contribInfo.actividades[0]
        : null;

    return {
      company_id: companyId,
      tax_regime: 'regimen_general' as const, // Default, can be updated later
      sii_activity_code: actividadPrincipal?.codigo || null,
      sii_activity_name:
        actividadPrincipal?.descripcion ||
        contribInfo.actividad_economica ||
        null,
      legal_representative_rut: representante?.rut || null,
      legal_representative_name: representante?.nombre_completo || null,
      start_of_activities_date: this.parseStartDate(
        contribInfo.fecha_inicio_actividades
      ),
      accounting_start_month: 1, // Default
      extra_data: contribInfo, // Store ALL SII data as JSONB
    };
  }

  /**
   * Parse start of activities date from SII format
   *
   * Converts "2023-04-13 00:00:00.0" to "2023-04-13"
   */
  private static parseStartDate(dateStr: string | null): string | null {
    if (!dateStr) return null;

    try {
      // Extract date part before space
      const datePart = dateStr.split(' ')[0];
      return datePart;
    } catch (e) {
      console.error(
        '[Company Tax Info Service] Error parsing start_of_activities_date:',
        e
      );
      return null;
    }
  }
}
