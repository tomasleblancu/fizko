/**
 * F29 SII Downloads types - Forms downloaded from the SII (Chilean tax authority)
 *
 * Re-exports the database type with stricter typing for status fields
 */

import type { Database } from './database'

// Strict status types
export type SIIFormStatus = 'vigente' | 'rectificado' | 'anulado'
export type PDFDownloadStatus = 'pending' | 'downloaded' | 'error'

// Re-export base type from database with stricter status typing
export type F29SIIDownload = Omit<Database['public']['Tables']['form29_sii_downloads']['Row'], 'status' | 'pdf_download_status'> & {
  status: SIIFormStatus
  pdf_download_status: PDFDownloadStatus
}

// API response types
export interface F29SIIDownloadsResponse {
  data: F29SIIDownload[]
  total: number
}

export interface F29SIIDownloadsParams {
  companyId: string
  year?: number
  month?: number
}
