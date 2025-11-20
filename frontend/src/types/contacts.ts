/**
 * Contact types for providers and clients
 */

export interface Contact {
  id: string
  rut: string
  business_name: string
  trade_name: string | null
  contact_type: ContactType
  address: string | null
  phone: string | null
  email: string | null
  created_at: string
  updated_at: string
}

export type ContactType = 'provider' | 'client' | 'both'

export interface ContactsResponse {
  data: Contact[]
  total: number
}
