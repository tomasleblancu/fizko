/**
 * F29 SII Downloads Service
 *
 * Handles Form 29 downloads from SII:
 * - Listing downloads with filters
 * - Data transformation
 */

import { createServiceClient } from '@/lib/supabase/server';
import type { Database } from '@/types/database';
import type { F29SIIDownload, SIIFormStatus, PDFDownloadStatus } from '@/types/f29-sii-downloads';

type Form29SiiDownloadRow = Database['public']['Tables']['form29_sii_downloads']['Row'];

export interface ListF29SIIDownloadsParams {
  companyId: string;
  year?: number;
  month?: number;
}

export interface ListF29SIIDownloadsResponse {
  data: F29SIIDownload[];
  total: number;
}

export class F29SIIDownloadsService {
  /**
   * List F29 SII downloads for a company with optional filters
   *
   * @param params - Query parameters
   * @returns List of F29 SII downloads with count
   */
  static async list(params: ListF29SIIDownloadsParams): Promise<ListF29SIIDownloadsResponse> {
    console.log(`[F29 SII Downloads Service] Listing downloads for company ${params.companyId}`);

    const supabase = createServiceClient();

    // Build query
    let query = supabase
      .from('form29_sii_downloads')
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
    const { data: downloads, error, count } = await query;

    if (error) {
      console.error('[F29 SII Downloads Service] Error fetching downloads:', error);
      throw new Error(`Failed to fetch F29 SII downloads: ${error.message}`);
    }

    console.log(`[F29 SII Downloads Service] Found ${count || 0} downloads`);

    // Transform to response format
    const transformedDownloads = this.transformDownloads(downloads || []);

    return {
      data: transformedDownloads,
      total: count || 0,
    };
  }

  /**
   * Get a single F29 SII download by ID
   *
   * @param downloadId - Download UUID
   * @returns F29 SII download
   */
  static async getById(downloadId: string): Promise<F29SIIDownload> {
    console.log(`[F29 SII Downloads Service] Fetching download ${downloadId}`);

    const supabase = createClient();

    const { data: download, error } = await supabase
      .from('form29_sii_downloads')
      .select('*')
      .eq('id', downloadId)
      .single();

    if (error || !download) {
      console.error('[F29 SII Downloads Service] Error fetching download:', error);
      throw new Error(`Download not found: ${error?.message || 'Unknown error'}`);
    }

    return this.transformDownload(download as any);
  }

  /**
   * Transform database rows to F29SIIDownload format
   */
  private static transformDownloads(downloads: Form29SiiDownloadRow[]): F29SIIDownload[] {
    return downloads.map((download) => this.transformDownload(download));
  }

  /**
   * Transform single database row to F29SIIDownload format
   */
  private static transformDownload(download: Form29SiiDownloadRow): F29SIIDownload {
    return {
      id: download.id,
      company_id: download.company_id,
      form29_id: download.form29_id,
      sii_folio: download.sii_folio,
      sii_id_interno: download.sii_id_interno,
      period_year: download.period_year,
      period_month: download.period_month,
      period_display: download.period_display,
      contributor_rut: download.contributor_rut,
      submission_date: download.submission_date,
      status: download.status as SIIFormStatus,
      amount_cents: Number(download.amount_cents),
      pdf_storage_url: download.pdf_storage_url,
      pdf_download_status: download.pdf_download_status as PDFDownloadStatus,
      pdf_download_error: download.pdf_download_error,
      pdf_downloaded_at: download.pdf_downloaded_at,
      extra_data: download.extra_data as Record<string, any> | null,
      created_at: download.created_at,
      updated_at: download.updated_at,
    };
  }
}
