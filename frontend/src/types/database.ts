export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      // ============================================
      // Sessions & Authentication
      // ============================================
      sessions: {
        Row: {
          id: string
          user_id: string
          company_id: string
          is_active: boolean
          cookies: Json
          resources: Json
          last_accessed_at: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          company_id: string
          is_active?: boolean
          cookies?: Json
          resources?: Json
          last_accessed_at?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          company_id?: string
          is_active?: boolean
          cookies?: Json
          resources?: Json
          last_accessed_at?: string | null
          created_at?: string
          updated_at?: string
        }
      }

      // ============================================
      // Companies
      // ============================================
      companies: {
        Row: {
          id: string
          rut: string
          business_name: string | null
          trade_name: string | null
          address: string | null
          phone: string | null
          email: string | null
          created_at: string
          updated_at: string
          sii_password: string | null
        }
        Insert: {
          id?: string
          rut: string
          business_name?: string | null
          trade_name?: string | null
          address?: string | null
          phone?: string | null
          email?: string | null
          created_at?: string
          updated_at?: string
          sii_password?: string | null
        }
        Update: {
          id?: string
          rut?: string
          business_name?: string | null
          trade_name?: string | null
          address?: string | null
          phone?: string | null
          email?: string | null
          created_at?: string
          updated_at?: string
          sii_password?: string | null
        }
      }

      // ============================================
      // Tax Documents - Sales
      // ============================================
      sales_documents: {
        Row: {
          id: string
          company_id: string
          document_type: string
          document_type_code: string | null
          folio: number | null
          issue_date: string
          reception_date: string | null
          accounting_date: string | null
          recipient_rut: string | null
          recipient_name: string | null
          net_amount: number
          tax_amount: number
          exempt_amount: number
          total_amount: number
          overdue_iva_credit: number
          status: string
          dte_xml: string | null
          sii_track_id: string | null
          file_url: string | null
          extra_data: Json | null
          created_at: string
          updated_at: string
          contact_id: string | null
        }
        Insert: {
          id?: string
          company_id: string
          document_type: string
          folio?: number | null
          issue_date: string
          reception_date?: string | null
          accounting_date?: string | null
          recipient_rut?: string | null
          recipient_name?: string | null
          net_amount: number
          tax_amount: number
          exempt_amount: number
          total_amount: number
          status: string
          dte_xml?: string | null
          sii_track_id?: string | null
          file_url?: string | null
          extra_data?: Json | null
          created_at?: string
          updated_at?: string
          contact_id?: string | null
        }
        Update: {
          id?: string
          company_id?: string
          document_type?: string
          folio?: number | null
          issue_date?: string
          reception_date?: string | null
          accounting_date?: string | null
          recipient_rut?: string | null
          recipient_name?: string | null
          net_amount?: number
          tax_amount?: number
          exempt_amount?: number
          total_amount?: number
          status?: string
          dte_xml?: string | null
          sii_track_id?: string | null
          file_url?: string | null
          extra_data?: Json | null
          created_at?: string
          updated_at?: string
          contact_id?: string | null
        }
      }

      // ============================================
      // Tax Documents - Purchases
      // ============================================
      purchase_documents: {
        Row: {
          id: string
          company_id: string
          document_type: string
          document_type_code: string | null
          folio: number | null
          issue_date: string
          reception_date: string | null
          sender_rut: string | null
          sender_name: string | null
          net_amount: number
          tax_amount: number
          exempt_amount: number
          total_amount: number
          overdue_iva_credit: number
          status: string
          dte_xml: string | null
          sii_track_id: string | null
          file_url: string | null
          extra_data: Json | null
          created_at: string
          updated_at: string
          contact_id: string | null
          accounting_state: string | null
          accounting_date: string | null
        }
        Insert: {
          id?: string
          company_id: string
          document_type: string
          folio?: number | null
          issue_date: string
          reception_date?: string | null
          sender_rut?: string | null
          sender_name?: string | null
          net_amount: number
          tax_amount: number
          exempt_amount: number
          total_amount: number
          status: string
          dte_xml?: string | null
          sii_track_id?: string | null
          file_url?: string | null
          extra_data?: Json | null
          created_at?: string
          updated_at?: string
          contact_id?: string | null
          accounting_state?: string | null
          accounting_date?: string | null
        }
        Update: {
          id?: string
          company_id?: string
          document_type?: string
          folio?: number | null
          issue_date?: string
          reception_date?: string | null
          sender_rut?: string | null
          sender_name?: string | null
          net_amount?: number
          tax_amount?: number
          exempt_amount?: number
          total_amount?: number
          status?: string
          dte_xml?: string | null
          sii_track_id?: string | null
          file_url?: string | null
          extra_data?: Json | null
          created_at?: string
          updated_at?: string
          contact_id?: string | null
          accounting_state?: string | null
          accounting_date?: string | null
        }
      }

      // ============================================
      // Form 29 (Monthly Tax Declaration)
      // ============================================
      form29: {
        Row: {
          id: string
          company_id: string
          period_year: number
          period_month: number
          total_sales: number
          taxable_sales: number
          exempt_sales: number
          sales_tax: number
          total_purchases: number
          taxable_purchases: number
          purchases_tax: number
          iva_to_pay: number
          iva_credit: number
          net_iva: number
          status: string
          revision_number: number
          submission_date: string | null
          extra_data: Json | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          company_id: string
          period_year: number
          period_month: number
          total_sales?: number
          taxable_sales?: number
          exempt_sales?: number
          sales_tax?: number
          total_purchases?: number
          taxable_purchases?: number
          purchases_tax?: number
          iva_to_pay?: number
          iva_credit?: number
          net_iva?: number
          status?: string
          revision_number?: number
          submission_date?: string | null
          extra_data?: Json | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          company_id?: string
          period_year?: number
          period_month?: number
          total_sales?: number
          taxable_sales?: number
          exempt_sales?: number
          sales_tax?: number
          total_purchases?: number
          taxable_purchases?: number
          purchases_tax?: number
          iva_to_pay?: number
          iva_credit?: number
          net_iva?: number
          status?: string
          revision_number?: number
          submission_date?: string | null
          extra_data?: Json | null
          created_at?: string
          updated_at?: string
        }
      }

      // ============================================
      // Form 29 SII Downloads
      // ============================================
      form29_sii_downloads: {
        Row: {
          id: string
          company_id: string
          form29_id: string | null
          sii_folio: string
          sii_id_interno: string | null
          period_year: number
          period_month: number
          period_display: string
          contributor_rut: string
          submission_date: string | null
          status: string
          amount_cents: number
          pdf_storage_url: string | null
          pdf_download_status: string
          pdf_download_error: string | null
          pdf_downloaded_at: string | null
          extra_data: Json | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          company_id: string
          form29_id?: string | null
          sii_folio: string
          sii_id_interno?: string | null
          period_year: number
          period_month: number
          period_display: string
          contributor_rut: string
          submission_date?: string | null
          status: string
          amount_cents: number
          pdf_storage_url?: string | null
          pdf_download_status?: string
          pdf_download_error?: string | null
          pdf_downloaded_at?: string | null
          extra_data?: Json | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          company_id?: string
          form29_id?: string | null
          sii_folio?: string
          sii_id_interno?: string | null
          period_year?: number
          period_month?: number
          period_display?: string
          contributor_rut?: string
          submission_date?: string | null
          status?: string
          amount_cents?: number
          pdf_storage_url?: string | null
          pdf_download_status?: string
          pdf_download_error?: string | null
          pdf_downloaded_at?: string | null
          extra_data?: Json | null
          created_at?: string
          updated_at?: string
        }
      }

      // ============================================
      // Honorarios Receipts
      // ============================================
      honorarios_receipts: {
        Row: {
          id: string
          company_id: string
          receipt_type: string
          folio: number | null
          issue_date: string
          recipient_rut: string | null
          recipient_name: string | null
          gross_amount: number
          recipient_retention: number
          net_amount: number
          extra_data: Json | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          company_id: string
          receipt_type: string
          folio?: number | null
          issue_date: string
          recipient_rut?: string | null
          recipient_name?: string | null
          gross_amount: number
          recipient_retention: number
          net_amount: number
          extra_data?: Json | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          company_id?: string
          receipt_type?: string
          folio?: number | null
          issue_date?: string
          recipient_rut?: string | null
          recipient_name?: string | null
          gross_amount?: number
          recipient_retention?: number
          net_amount?: number
          extra_data?: Json | null
          created_at?: string
          updated_at?: string
        }
      }

      // ============================================
      // Contacts (Providers & Clients)
      // ============================================
      contacts: {
        Row: {
          id: string
          company_id: string
          rut: string
          business_name: string
          trade_name: string | null
          contact_type: string
          address: string | null
          phone: string | null
          email: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          company_id: string
          rut: string
          business_name: string
          trade_name?: string | null
          contact_type: string
          address?: string | null
          phone?: string | null
          email?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          company_id?: string
          rut?: string
          business_name?: string
          trade_name?: string | null
          contact_type?: string
          address?: string | null
          phone?: string | null
          email?: string | null
          created_at?: string
          updated_at?: string
        }
      }

      // ============================================
      // People (Personnel / Employees)
      // ============================================
      people: {
        Row: {
          id: string
          company_id: string
          rut: string
          first_name: string
          last_name: string
          email: string | null
          phone: string | null
          birth_date: string | null
          position_title: string | null
          contract_type: string | null
          hire_date: string | null
          base_salary: number
          afp_provider: string | null
          afp_percentage: number | null
          health_provider: string | null
          health_plan: string | null
          health_percentage: number | null
          health_fixed_amount: number | null
          bank_name: string | null
          bank_account_type: string | null
          bank_account_number: string | null
          status: string
          termination_date: string | null
          termination_reason: string | null
          notes: string | null
          photo_url: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          company_id: string
          rut: string
          first_name: string
          last_name: string
          email?: string | null
          phone?: string | null
          birth_date?: string | null
          position_title?: string | null
          contract_type?: string | null
          hire_date?: string | null
          base_salary?: number
          afp_provider?: string | null
          afp_percentage?: number | null
          health_provider?: string | null
          health_plan?: string | null
          health_percentage?: number | null
          health_fixed_amount?: number | null
          bank_name?: string | null
          bank_account_type?: string | null
          bank_account_number?: string | null
          status?: string
          termination_date?: string | null
          termination_reason?: string | null
          notes?: string | null
          photo_url?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          company_id?: string
          rut?: string
          first_name?: string
          last_name?: string
          email?: string | null
          phone?: string | null
          birth_date?: string | null
          position_title?: string | null
          contract_type?: string | null
          hire_date?: string | null
          base_salary?: number
          afp_provider?: string | null
          afp_percentage?: number | null
          health_provider?: string | null
          health_plan?: string | null
          health_percentage?: number | null
          health_fixed_amount?: number | null
          bank_name?: string | null
          bank_account_type?: string | null
          bank_account_number?: string | null
          status?: string
          termination_date?: string | null
          termination_reason?: string | null
          notes?: string | null
          photo_url?: string | null
          created_at?: string
          updated_at?: string
        }
      }

      // ============================================
      // Profiles (User Profiles)
      // ============================================
      profiles: {
        Row: {
          id: string
          email: string
          name: string | null
          lastname: string | null
          phone: string | null
          phone_verified: boolean
          phone_verified_at: string | null
          full_name: string | null
          company_name: string | null
          avatar_url: string | null
          rol: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id: string
          email: string
          name?: string | null
          lastname?: string | null
          phone?: string | null
          phone_verified?: boolean
          phone_verified_at?: string | null
          full_name?: string | null
          company_name?: string | null
          avatar_url?: string | null
          rol?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          email?: string
          name?: string | null
          lastname?: string | null
          phone?: string | null
          phone_verified?: boolean
          phone_verified_at?: string | null
          full_name?: string | null
          company_name?: string | null
          avatar_url?: string | null
          rol?: string | null
          created_at?: string
          updated_at?: string
        }
      }

      // ============================================
      // Company Settings
      // ============================================
      company_settings: {
        Row: {
          id: string
          company_id: string
          has_formal_employees: boolean | null
          has_imports: boolean | null
          has_exports: boolean | null
          has_lease_contracts: boolean | null
          has_bank_loans: boolean | null
          business_description: string | null
          is_initial_setup_complete: boolean
          initial_setup_completed_at: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          company_id: string
          has_formal_employees?: boolean | null
          has_imports?: boolean | null
          has_exports?: boolean | null
          has_lease_contracts?: boolean | null
          has_bank_loans?: boolean | null
          business_description?: string | null
          is_initial_setup_complete?: boolean
          initial_setup_completed_at?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          company_id?: string
          has_formal_employees?: boolean | null
          has_imports?: boolean | null
          has_exports?: boolean | null
          has_lease_contracts?: boolean | null
          has_bank_loans?: boolean | null
          business_description?: string | null
          is_initial_setup_complete?: boolean
          initial_setup_completed_at?: string | null
          created_at?: string
          updated_at?: string
        }
      }

      // ============================================
      // Notification Templates
      // ============================================
      notification_templates: {
        Row: {
          id: string
          code: string
          name: string
          description: string | null
          category: string
          entity_type: string | null
          message_template: string
          timing_config: Json | null
          priority: string
          is_active: boolean
          can_repeat: boolean
          max_repeats: number | null
          repeat_interval_hours: number | null
          auto_assign_to_new_companies: boolean
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          code: string
          name: string
          description?: string | null
          category: string
          entity_type?: string | null
          message_template: string
          timing_config?: Json | null
          priority?: string
          is_active?: boolean
          can_repeat?: boolean
          max_repeats?: number | null
          repeat_interval_hours?: number | null
          auto_assign_to_new_companies?: boolean
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          code?: string
          name?: string
          description?: string | null
          category?: string
          entity_type?: string | null
          message_template?: string
          timing_config?: Json | null
          priority?: string
          is_active?: boolean
          can_repeat?: boolean
          max_repeats?: number | null
          repeat_interval_hours?: number | null
          auto_assign_to_new_companies?: boolean
          created_at?: string
          updated_at?: string
        }
      }

      // ============================================
      // Notification Subscriptions
      // ============================================
      notification_subscriptions: {
        Row: {
          id: string
          company_id: string
          notification_template_id: string
          is_enabled: boolean
          custom_timing_config: Json | null
          custom_message_template: string | null
          channels: Json
          filters: Json | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          company_id: string
          notification_template_id: string
          is_enabled?: boolean
          custom_timing_config?: Json | null
          custom_message_template?: string | null
          channels?: Json
          filters?: Json | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          company_id?: string
          notification_template_id?: string
          is_enabled?: boolean
          custom_timing_config?: Json | null
          custom_message_template?: string | null
          channels?: Json
          filters?: Json | null
          created_at?: string
          updated_at?: string
        }
      }

      // ============================================
      // User Notification Preferences
      // ============================================
      user_notification_preferences: {
        Row: {
          id: string
          user_id: string
          company_id: string | null
          notifications_enabled: boolean
          quiet_hours_start: string | null
          quiet_hours_end: string | null
          quiet_days: Json | null
          muted_categories: Json | null
          muted_templates: Json
          max_notifications_per_day: number
          min_interval_minutes: number
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          company_id?: string | null
          notifications_enabled?: boolean
          quiet_hours_start?: string | null
          quiet_hours_end?: string | null
          quiet_days?: Json | null
          muted_categories?: Json | null
          muted_templates?: Json
          max_notifications_per_day?: number
          min_interval_minutes?: number
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          company_id?: string | null
          notifications_enabled?: boolean
          quiet_hours_start?: string | null
          quiet_hours_end?: string | null
          quiet_days?: Json | null
          muted_categories?: Json | null
          muted_templates?: Json
          max_notifications_per_day?: number
          min_interval_minutes?: number
          created_at?: string
          updated_at?: string
        }
      }
    }
  }
}

// ============================================
// Base Helper Types
// ============================================
// NOTE: For domain-specific types with stricter typing (e.g., F29Form, F29SIIDownload),
// use the modularized types in their respective files (f29.ts, f29-sii-downloads.ts, etc.)
// These are base types directly from the database schema.

export type Session = Database['public']['Tables']['sessions']['Row']
export type Company = Database['public']['Tables']['companies']['Row']
export type SalesDocument = Database['public']['Tables']['sales_documents']['Row']
export type PurchaseDocument = Database['public']['Tables']['purchase_documents']['Row']
export type HonorariosReceipt = Database['public']['Tables']['honorarios_receipts']['Row']
export type Contact = Database['public']['Tables']['contacts']['Row']
export type Person = Database['public']['Tables']['people']['Row']

// ============================================
// Combined Types
// ============================================

// Combined type for session with company data
export interface SessionWithCompany extends Session {
  company: Company
}

// Combined type for documents (sales + purchases)
export type Document = SalesDocument | PurchaseDocument

// Helper type for unified document view (sales or purchases with common fields)
export type DocumentWithType =
  | (SalesDocument & { type: 'sale'; counterparty_rut: string | null; counterparty_name: string | null })
  | (PurchaseDocument & { type: 'purchase'; counterparty_rut: string | null; counterparty_name: string | null })
