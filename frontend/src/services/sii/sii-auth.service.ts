/**
 * SII Auth Service
 *
 * Main orchestrator for SII authentication and data synchronization
 */

import { extractDV, extractRutBody } from '@/lib/formatters';
import type { SIIAuthResult } from '@/types/sii.types';
import { SIIBackendClient } from './sii-backend-client';
import { CompanyService } from '../company/company.service';
import { SessionService } from '../session/session.service';
import { CeleryTaskService } from '../celery/celery-task.service';
import { CalendarService } from '../calendar/calendar.service';

export class SIIAuthService {
  /**
   * Authenticate with SII and synchronize company data
   *
   * This is the main entry point that orchestrates the entire authentication flow:
   * 1. Normalize RUT format
   * 2. Authenticate with SII backend
   * 3. Create or update company with SII data
   * 4. Save encrypted SII credentials
   * 5. Launch document sync task (for new companies only)
   * 6. Create user-company session
   * 7. Check if initial setup is needed
   *
   * @param userId - User UUID from Supabase auth
   * @param userEmail - User email from Supabase auth
   * @param rut - Raw RUT string (can be formatted like "77.794.858-K" or "77794858-K")
   * @param password - SII password (plain text, will be encrypted)
   * @returns Authentication result with company_id, session_id, and setup status
   */
  static async authenticateAndSync(
    userId: string,
    userEmail: string,
    rut: string,
    password: string
  ): Promise<SIIAuthResult> {
    console.log('[SII Auth Service] Starting authentication flow');

    // 1. Normalize RUT (remove hyphen, lowercase DV)
    const normalizedRut = this.normalizeRUT(rut);
    const rutBody = extractRutBody(rut);
    const dv = extractDV(rut);

    console.log(`[SII Auth Service] Normalized RUT: ${normalizedRut}`);

    // 2. Authenticate with backend and get contributor info
    const siiData = await SIIBackendClient.login(rutBody, dv, password);

    // 3. Create or update company with SII data
    const { company, isNew } = await CompanyService.upsertFromSII(
      normalizedRut,
      siiData.contribuyente_info
    );

    // 4. Save encrypted SII credentials (already encrypted by backend)
    await CompanyService.saveCredentials(company.id, siiData.encrypted_password);

    // 5. Launch document sync tasks for new companies
    if (isNew) {
      try {
        console.log(
          '[SII Auth Service] Launching document sync tasks for new company'
        );

        // Sync current month
        const taskResponse = await CeleryTaskService.syncSIIDocuments(
          company.id,
          1, // months
          0 // month_offset
        );
        console.log(
          '[SII Auth Service] Document sync task (current month) launched:',
          taskResponse.task_id
        );

        // Sync previous month (offset 1)
        const taskResponse1 = await CeleryTaskService.syncSIIDocuments(
          company.id,
          1, // months
          1 // month_offset
        );
        console.log(
          '[SII Auth Service] Document sync task (offset 1) launched:',
          taskResponse1.task_id
        );

        // Sync 2 months ago (offset 2)
        const taskResponse2 = await CeleryTaskService.syncSIIDocuments(
          company.id,
          1, // months
          2 // month_offset
        );
        console.log(
          '[SII Auth Service] Document sync task (offset 2) launched:',
          taskResponse2.task_id
        );

        // Sync last 12 months (starting from 3 months ago)
        const taskResponse3 = await CeleryTaskService.syncSIIDocuments(
          company.id,
          12, // months
          3 // month_offset
        );
        console.log(
          '[SII Auth Service] Document sync task (12 months, offset 3) launched:',
          taskResponse3.task_id
        );

        // Launch Form29 sync task
        console.log(
          '[SII Auth Service] Launching Form29 sync task for new company'
        );
        const form29TaskResponse = await CeleryTaskService.syncSIIForm29(
          company.id,
          '2025'
        );
        console.log(
          '[SII Auth Service] Form29 sync task launched:',
          form29TaskResponse.task_id
        );
      } catch (error) {
        console.error(
          '[SII Auth Service] Failed to launch sync tasks:',
          error
        );
        // Don't fail auth if task launch fails - log and continue
      }
    }

    // 6. Create or update user-company session with SII cookies
    const session = await SessionService.createOrUpdate(
      userId,
      company.id,
      siiData.cookies,
      userEmail
    );

    // 7. Check if company needs initial setup
    const needsSetup = await CompanyService.needsSetup(company.id);

    console.log('[SII Auth Service] Authentication flow completed successfully');

    return {
      success: true,
      company_id: company.id,
      session_id: session.id,
      needs_setup: needsSetup,
    };
  }

  /**
   * Initialize calendar events for a company after setup is complete
   *
   * This creates company_events (company-template relationships) for all
   * mandatory tax events. Should be called after initial company setup.
   *
   * @param companyId - Company UUID
   * @returns Created company events
   */
  static async initializeCompanyCalendar(companyId: string): Promise<void> {
    try {
      console.log(
        '[SII Auth Service] Initializing calendar for company:',
        companyId
      );

      // Initialize calendar with mandatory events
      // The backend will create company_events for all mandatory event_templates
      const companyEvents = await CalendarService.initializeCompanyCalendar(
        companyId
      );

      console.log(
        `[SII Auth Service] Calendar initialized with ${companyEvents.length} event templates`
      );
    } catch (error) {
      console.error(
        '[SII Auth Service] Failed to initialize calendar:',
        error
      );
      // Don't fail the setup if calendar init fails - log and continue
    }
  }

  /**
   * Normalize RUT to format: {body}{dv_lowercase}
   *
   * Examples:
   * - "77.794.858-K" -> "77794858k"
   * - "77794858-K" -> "77794858k"
   * - "12345678-9" -> "123456789"
   *
   * @param rut - Raw RUT string
   * @returns Normalized RUT without hyphen and with lowercase DV
   */
  private static normalizeRUT(rut: string): string {
    const rutBody = extractRutBody(rut);
    const dv = extractDV(rut);
    return `${rutBody}${dv.toLowerCase()}`;
  }
}
