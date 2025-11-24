/**
 * Type definitions for SII Auth Edge Function
 */

export interface SIIAuthRequest {
  rut: string;
  password: string;
}

export interface SIIAuthResponse {
  success: boolean;
  company_id?: string;
  session_id?: string;
  needs_setup: boolean;
  message?: string;
  error?: string;
}

export interface SIILoginResponse {
  success: boolean;
  message: string;
  session_active: boolean;
  cookies?: any[];
  contribuyente_info?: ContribuyenteInfo;
  encrypted_password?: string;
}

export interface ContribuyenteInfo {
  razon_social?: string;
  nombre?: string;
  nombre_fantasia?: string;
  telefono?: string;
  email?: string;
  rut?: string;
  actividades_economicas?: ActividadEconomica[];
  direcciones?: Direccion[];
  fecha_inicio_actividades?: string;
}

export interface ActividadEconomica {
  codigo: string;
  nombre: string;
}

export interface Direccion {
  calle: string;
  numero?: string;
  comuna: string;
  telefono?: string;
  correo?: string;
  mail?: string;
}

export interface CompanyData {
  rut: string;
  business_name: string;
  trade_name: string | null;
  address: string | null;
  phone: string | null;
  email: string | null;
}

export interface Company {
  id: string;
  rut: string;
  business_name: string;
  trade_name: string | null;
  address: string | null;
  phone: string | null;
  email: string | null;
  sii_password?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Session {
  id: string;
  user_id: string;
  company_id: string;
  is_active: boolean;
  cookies: any;
  resources?: any;
  last_accessed_at: string;
  created_at: string;
  updated_at: string;
}
