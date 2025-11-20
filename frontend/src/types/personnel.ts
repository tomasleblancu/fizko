/**
 * Personnel (People/Employees) types
 */

export interface Person {
  id: string
  company_id: string
  rut: string
  first_name: string
  last_name: string
  email: string | null
  phone: string | null
  birth_date: string | null
  position_title: string | null
  contract_type: ContractType | null
  hire_date: string | null
  base_salary: number
  afp_provider: string | null
  afp_percentage: number | null
  health_provider: string | null
  health_plan: string | null
  health_percentage: number | null
  health_fixed_amount: number | null
  bank_name: string | null
  bank_account_type: BankAccountType | null
  bank_account_number: string | null
  status: PersonStatus
  termination_date: string | null
  termination_reason: string | null
  notes: string | null
  photo_url: string | null
  created_at: string
  updated_at: string
}

export type ContractType =
  | 'indefinido'
  | 'plazo_fijo'
  | 'honorarios'
  | 'por_obra'
  | 'part_time'

export type BankAccountType =
  | 'cuenta corriente'
  | 'cuenta vista'
  | 'cuenta ahorro'

export type PersonStatus = 'active' | 'inactive' | 'terminated'

export interface PersonListResponse {
  data: Person[]
  total: number
  page: number
  page_size: number
}
