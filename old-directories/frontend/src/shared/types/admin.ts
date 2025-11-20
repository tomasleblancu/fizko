/**
 * Type definitions for admin company view
 */

export interface UserInfo {
  id: string;
  email: string;
  full_name: string | null;
  name: string | null;
  lastname: string | null;
  rol: string | null;
  session_id: string;
  is_active: boolean;
  last_accessed_at: string | null;
  created_at: string;
}

export interface DocumentStats {
  total_purchase_documents: number;
  total_sales_documents: number;
  latest_purchase_date: string | null;
  latest_sales_date: string | null;
  total_purchase_amount: number;
  total_sales_amount: number;
}

export interface SyncAction {
  session_id: string;
  user_email: string;
  last_sync: string | null;
  total_syncs: number;
}

export interface CompanySummary {
  id: string;
  rut: string;
  business_name: string;
  trade_name: string | null;
  tax_regime: string | null;
  total_users: number;
  total_documents: number;
  created_at: string;
  last_activity: string | null;
  latest_f29_status: string | null;
  latest_f29_period: string | null;
}

export interface CompanyDetail {
  // Company info
  id: string;
  rut: string;
  business_name: string;
  trade_name: string | null;
  address: string | null;
  phone: string | null;
  email: string | null;
  created_at: string;
  updated_at: string;

  // Tax info
  tax_regime: string | null;
  sii_activity_code: string | null;
  sii_activity_name: string | null;
  legal_representative_rut: string | null;
  legal_representative_name: string | null;

  // Users with access
  users: UserInfo[];

  // Document statistics
  document_stats: DocumentStats;

  // Sync actions
  sync_actions: SyncAction[];
}
