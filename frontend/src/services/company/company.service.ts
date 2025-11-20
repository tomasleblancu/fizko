/**
 * Company Service
 *
 * Handles CRUD operations for companies table and related operations
 */

import { createServiceClient } from '@/lib/supabase/server';
import type { ContribuyenteInfo } from '@/types/sii.types';
import { CompanyTaxInfoService } from './company-tax-info.service';

interface Company {
  id: string;
  rut: string;
  business_name: string;
  trade_name: string | null;
  address: string | null;
  phone: string | null;
  email: string | null;
  created_at: string;
  updated_at: string;
}

export class CompanyService {
  /**
   * Create or update company from SII contributor data
   *
   * @param normalizedRut - RUT in normalized format (e.g., "77794858k")
   * @param contribInfo - Contributor information from SII
   * @returns Company record and flag indicating if it's new
   */
  static async upsertFromSII(
    normalizedRut: string,
    contribInfo: ContribuyenteInfo
  ): Promise<{ company: Company; isNew: boolean }> {
    const serviceClient = createServiceClient();

    // Try to find existing company
    let { data: company } = await serviceClient
      .from('companies')
      .select('*')
      .eq('rut', normalizedRut)
      .single();

    const companyData = this.buildCompanyData(normalizedRut, contribInfo);
    let isNew = false;

    if (!company) {
      // Create new company
      console.log(`[Company Service] Creating new company with RUT: ${normalizedRut}`);
      isNew = true;

      const { data: newCompany, error: companyError } = await serviceClient
        .from('companies')
        .insert(companyData)
        .select()
        .single();

      if (companyError) {
        console.error('[Company Service] Error creating company:', companyError);
        console.error('[Company Service] Error details:', {
          code: companyError.code,
          message: companyError.message,
          details: companyError.details,
          hint: companyError.hint,
        });
        throw new Error(`Error al crear empresa: ${companyError.message}`);
      }

      company = newCompany;
      console.log(`[Company Service] Company created successfully: ${company.id}`);

      // Create company_tax_info for new company
      await CompanyTaxInfoService.upsert(company.id, contribInfo);
    } else {
      // Update existing company
      console.log(`[Company Service] Company already exists with RUT: ${normalizedRut}`);

      if (contribInfo.razon_social || contribInfo.nombre) {
        const { error: updateCompanyError } = await serviceClient
          .from('companies')
          .update(companyData)
          .eq('id', company.id);

        if (updateCompanyError) {
          console.error('[Company Service] Error updating company:', updateCompanyError);
          throw new Error(`Error updating company: ${updateCompanyError.message}`);
        }

        console.log('[Company Service] Company info updated successfully');
      }

      // Update company_tax_info
      await CompanyTaxInfoService.upsert(company.id, contribInfo);
    }

    return { company, isNew };
  }

  /**
   * Save encrypted SII credentials for a company
   *
   * @param companyId - Company UUID
   * @param encryptedPassword - Already encrypted SII password from backend
   */
  static async saveCredentials(
    companyId: string,
    encryptedPassword: string
  ): Promise<void> {
    const serviceClient = createServiceClient();

    console.log('[Company Service] Saving encrypted SII password');

    const { error } = await serviceClient
      .from('companies')
      .update({ sii_password: encryptedPassword })
      .eq('id', companyId);

    if (error) {
      console.error('[Company Service] Error saving credentials:', error);
      throw new Error(`Error al guardar credenciales: ${error.message}`);
    }

    console.log('[Company Service] Password saved successfully');
  }

  /**
   * Check if company needs initial setup
   *
   * @param companyId - Company UUID
   * @returns True if company needs setup, false otherwise
   */
  static async needsSetup(companyId: string): Promise<boolean> {
    const serviceClient = createServiceClient();

    const { data: settings } = await serviceClient
      .from('company_settings')
      .select('is_initial_setup_complete')
      .eq('company_id', companyId)
      .maybeSingle();

    const needsSetup = !settings || !settings.is_initial_setup_complete;

    console.log('[Company Service] Setup required:', needsSetup);

    return needsSetup;
  }

  /**
   * Build company data object from contributor info
   */
  private static buildCompanyData(
    normalizedRut: string,
    contribInfo: ContribuyenteInfo
  ) {
    const address = this.extractAddress(contribInfo);

    // Get contact info from primary source or fallback to address
    const mainAddress =
      contribInfo.direcciones && contribInfo.direcciones.length > 0
        ? contribInfo.direcciones[0]
        : null;

    return {
      rut: normalizedRut,
      business_name:
        contribInfo.razon_social ||
        contribInfo.nombre ||
        `Empresa ${normalizedRut}`,
      trade_name: contribInfo.nombre_fantasia || null,
      address,
      phone: contribInfo.telefono || mainAddress?.telefono || null,
      email:
        contribInfo.email ||
        mainAddress?.correo ||
        mainAddress?.mail ||
        null,
    };
  }

  /**
   * Extract and format primary address from contributor info
   */
  private static extractAddress(contribInfo: ContribuyenteInfo): string | null {
    if (!contribInfo.direcciones || contribInfo.direcciones.length === 0) {
      return null;
    }

    const mainAddress = contribInfo.direcciones[0];
    const parts = [mainAddress.calle];

    if (mainAddress.numero) {
      parts.push(mainAddress.numero);
    }

    parts.push(mainAddress.comuna);

    return parts.join(', ');
  }
}
