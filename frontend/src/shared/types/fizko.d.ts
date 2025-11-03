export interface Company {
  id: string;
  rut: string;
  business_name: string;
  trade_name?: string;
  address?: string;
  phone?: string;
  email?: string;
  tax_regime?: string;
  sii_activity_code?: string;
  created_at: string;
  session_id?: string;
}

export interface CompanySettings {
  id?: string;
  company_id: string;
  has_formal_employees: boolean | null;
  has_imports: boolean | null;
  has_exports: boolean | null;
  has_lease_contracts: boolean | null;
  is_initial_setup_complete: boolean;
  initial_setup_completed_at: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface TaxSummary {
  id: string;
  company_id: string;
  period_start: string;
  period_end: string;
  total_revenue: number;
  total_expenses: number;
  iva_collected: number;
  iva_paid: number;
  net_iva: number;
  income_tax: number;
  previous_month_credit?: number;
  monthly_tax: number;
  created_at: string;
}

export interface PayrollRecord {
  id: string;
  company_id: string;
  employee_name: string;
  employee_rut: string;
  gross_salary: number;
  afp_deduction: number;
  isapre_deduction: number;
  other_deductions: number;
  net_salary: number;
  employer_contributions: number;
  period: string;
  created_at: string;
}

export interface PayrollSummary {
  period: string;
  total_employees: number;
  total_gross_salary: number;
  total_deductions: number;
  total_net_salary: number;
  total_employer_contributions: number;
}

export interface TaxDocument {
  id: string;
  company_id: string;
  document_type: string;
  document_number: string;
  issue_date: string;
  amount: number;
  tax_amount?: number;
  status: string;
  description?: string;
  source: 'sale' | 'purchase'; // Indicates if document is a sale or purchase
  created_at: string;
}

// ============================================================================
// Calendar System Types
// ============================================================================

export type EventCategory =
  | 'impuesto_mensual'
  | 'impuesto_anual'
  | 'prevision'
  | 'declaracion_jurada'
  | 'libros'
  | 'otros';

export type EventStatus =
  | 'pending'
  | 'in_progress'
  | 'completed'
  | 'overdue'
  | 'cancelled';

export type TaskStatus =
  | 'pending'
  | 'in_progress'
  | 'completed'
  | 'skipped';

export type RecurrenceFrequency =
  | 'monthly'
  | 'quarterly'
  | 'annual'
  | 'biannual';

export interface EventTemplate {
  id: string;
  code: string;
  name: string;
  description?: string;
  category: EventCategory;
  authority: string;
  is_mandatory: boolean;
  applies_to_regimes?: Record<string, any>;
  default_recurrence: {
    frequency: RecurrenceFrequency;
    day_of_month?: number;
    month_of_year?: number;
    business_days_adjustment?: 'before' | 'after' | 'none';
  };
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface CompanyEvent {
  id: string;
  company_id: string;
  event_template_id: string;
  event_template?: EventTemplate;
  is_active: boolean;
  custom_config?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface EventTask {
  id: string;
  event_id: string;
  task_type: string;
  title: string;
  description?: string;
  order_index: number;
  status: TaskStatus;
  is_automated: boolean;
  automation_config?: Record<string, any>;
  completed_at?: string;
  completed_by?: string;
}

export interface CalendarEvent {
  id: string;
  company_event_id: string;
  company_id: string;
  title: string;
  description?: string;
  event_template: {
    id: string;
    code: string;
    name: string;
    category: EventCategory;
    authority: string;
  };
  due_date: string;
  period_start?: string;
  period_end?: string;
  status: EventStatus;
  completion_date?: string;
  completion_data?: Record<string, any>;
  auto_generated: boolean;
  metadata: Record<string, any>;
  tasks?: EventTask[];
  history?: EventHistory[];
  created_at: string;
  updated_at: string;
}

export type EventHistoryType =
  | 'created'
  | 'status_changed'
  | 'note_added'
  | 'document_attached'
  | 'task_completed'
  | 'reminder_sent'
  | 'updated'
  | 'completed'
  | 'cancelled'
  | 'system_action';

export interface EventHistory {
  id: string;
  calendar_event_id: string;
  user_id?: string;
  event_type: EventHistoryType;
  title: string;
  description?: string;
  metadata: Record<string, any>;
  created_at: string;
}

export interface CalendarStats {
  total_pending: number;
  total_overdue: number;
  total_upcoming: number;
  next_due_date?: string;
  next_event?: CalendarEvent;
}

// ============================================================================
// Personnel Management Types
// ============================================================================

export type PersonStatus = 'active' | 'inactive' | 'terminated';

export interface Person {
  id: string;
  company_id: string;
  rut: string;
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  hire_date: string;
  termination_date?: string;
  status: PersonStatus;
  base_salary: number;
  afp_provider?: string;
  afp_percentage?: number;
  health_provider?: string;
  health_plan?: string;
  health_percentage?: number;
  health_fixed_amount?: number;
  bank_name?: string;
  bank_account_type?: string;
  bank_account_number?: string;
  notes?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface PersonCreate {
  company_id: string;
  rut: string;
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  hire_date: string;
  status?: PersonStatus;
  base_salary: number;
  afp_provider?: string;
  afp_percentage?: number;
  health_provider?: string;
  health_plan?: string;
  health_percentage?: number;
  health_fixed_amount?: number;
  bank_name?: string;
  bank_account_type?: string;
  bank_account_number?: string;
  notes?: string;
  metadata?: Record<string, any>;
}

export interface PersonUpdate {
  rut?: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  hire_date?: string;
  termination_date?: string;
  status?: PersonStatus;
  base_salary?: number;
  afp_provider?: string;
  afp_percentage?: number;
  health_provider?: string;
  health_plan?: string;
  health_percentage?: number;
  health_fixed_amount?: number;
  bank_name?: string;
  bank_account_type?: string;
  bank_account_number?: string;
  notes?: string;
  metadata?: Record<string, any>;
}

export interface PersonListResponse {
  data: Person[];
  total: number;
  page: number;
  page_size: number;
}

export type PayrollStatus = 'draft' | 'approved' | 'paid' | 'closed';
export type PaymentStatus = 'pending' | 'paid' | 'failed';

export interface PayrollItem {
  code: string;
  description: string;
  amount: number;
  is_percentage?: boolean;
}

export interface Payroll {
  id: string;
  company_id: string;
  person_id: string;
  period_month: number;
  period_year: number;
  base_salary: number;
  taxable_income_items: PayrollItem[];
  non_taxable_income_items: PayrollItem[];
  total_income: number;
  afp_deduction: number;
  health_deduction: number;
  unemployment_insurance: number;
  income_tax: number;
  other_deductions_items: PayrollItem[];
  total_deductions: number;
  net_salary: number;
  status: PayrollStatus;
  payment_status: PaymentStatus;
  payment_date?: string;
  notes?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
  person?: Person;
}

export interface PayrollCreate {
  company_id: string;
  person_id: string;
  period_month: number;
  period_year: number;
  base_salary: number;
  taxable_income_items?: PayrollItem[];
  non_taxable_income_items?: PayrollItem[];
  afp_deduction?: number;
  health_deduction?: number;
  unemployment_insurance?: number;
  income_tax?: number;
  other_deductions_items?: PayrollItem[];
  status?: PayrollStatus;
  payment_status?: PaymentStatus;
  payment_date?: string;
  notes?: string;
  metadata?: Record<string, any>;
}

export interface PayrollUpdate {
  base_salary?: number;
  taxable_income_items?: PayrollItem[];
  non_taxable_income_items?: PayrollItem[];
  afp_deduction?: number;
  health_deduction?: number;
  unemployment_insurance?: number;
  income_tax?: number;
  other_deductions_items?: PayrollItem[];
  status?: PayrollStatus;
  payment_status?: PaymentStatus;
  payment_date?: string;
  notes?: string;
  metadata?: Record<string, any>;
}

export interface PayrollListResponse {
  data: Payroll[];
  total: number;
  page: number;
  page_size: number;
}

export interface PayrollSummary {
  period_month: number;
  period_year: number;
  total_employees: number;
  total_gross_salary: number;
  total_deductions: number;
  total_net_salary: number;
}
