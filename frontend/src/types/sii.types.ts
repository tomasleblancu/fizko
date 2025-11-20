/**
 * SII Service Types
 *
 * Type definitions for SII authentication and contributor information
 */

/**
 * Cookie from SII session
 */
export interface SIICookie {
  domain: string;
  expiry?: number;
  httpOnly: boolean;
  name: string;
  path: string;
  sameSite: 'Lax' | 'Strict' | 'None';
  secure: boolean;
  value: string;
}

/**
 * Economic activity from SII
 */
export interface ActividadEconomica {
  codigo: string;
  descripcion: string;
  categoria_tributaria: string;
  afecto_iva: boolean;
  fecha_inicio: string;
}

/**
 * Address from SII contributor info
 */
export interface DireccionSII {
  codigo: string;
  tipo: string;
  tipo_codigo: string;
  calle: string;
  numero: string | null;
  bloque: string | null;
  departamento: string | null;
  villa_poblacion: string | null;
  comuna: string;
  comuna_codigo: string;
  region: string;
  region_codigo: string;
  ciudad: string | null;
  tipo_propiedad: string;
  tipo_propiedad_codigo: string;
  rut_propietario: string;
  telefono: string | null;
  fax: string | null;
  correo: string | null;
  mail: string | null;
}

/**
 * Legal representative from SII
 */
export interface RepresentanteLegal {
  rut: string;
  nombre_completo: string;
  nombres: string;
  apellido_paterno: string;
  apellido_materno: string;
  fecha_inicio: string;
  fecha_termino: string | null;
  vigente: boolean;
}

/**
 * Partner/shareholder from SII
 */
export interface Socio {
  rut: string;
  nombre_completo: string;
  nombres: string;
  apellido_paterno: string;
  apellido_materno: string;
  fecha_incorporacion: string;
  fecha_fin_participacion: string | null;
  participacion_capital: string;
  participacion_utilidades: string;
  aporte_enterado: string;
  aporte_por_enterar: string;
  vigente: boolean;
}

/**
 * Document stamp/authorization from SII
 */
export interface Timbraje {
  codigo: string;
  descripcion: string;
  numero_inicial: string;
  numero_final: string;
  fecha_legalizacion: string;
}

/**
 * Tax compliance attribute
 */
export interface AtributoTributario {
  atr_codigo: string;
  cumple: 'SI' | 'NO';
  condicion: string;
  titulo: string;
  descripcion: string;
}

/**
 * Tax compliance info from SII
 */
export interface CumplimientoTributario {
  estado: string;
  semestre_actual: string;
  atributos: AtributoTributario[];
  historicos: any[] | null;
}

/**
 * Observations/alerts from SII
 */
export interface ObservacionesSII {
  tiene_observaciones: boolean;
  codigo: number;
  descripcion: string;
  observaciones: any[] | null;
}

/**
 * Complete contributor information from SII
 */
export interface ContribuyenteInfo {
  rut: string;
  razon_social: string;
  nombre: string;
  tipo_contribuyente: string;
  tipo_contribuyente_codigo: string;
  subtipo_contribuyente: string;
  subtipo_contribuyente_codigo: string;
  email: string;
  telefono: string;
  actividad_economica: string;
  fecha_inicio_actividades: string;
  fecha_constitucion: string;
  fecha_nacimiento: string | null;
  unidad_operativa: string;
  unidad_operativa_codigo: string;
  unidad_operativa_direccion: string;
  segmento: string;
  segmento_codigo: string;
  persona_empresa: string;
  actividades: ActividadEconomica[];
  direcciones: DireccionSII[];
  representantes: RepresentanteLegal[];
  socios: Socio[];
  timbrajes: Timbraje[];
  autorizado_declarar_dia_20: boolean;
  fecha_termino_giro: string | null;
  capital_enterado: string | null;
  capital_por_enterar: string;
  extraction_method: string;
  api_endpoint: string;
  cumplimiento_tributario: CumplimientoTributario;
  observaciones: ObservacionesSII;
  nombre_fantasia?: string;
  direccion?: string;
}

/**
 * Response from backend-v2 /api/sii/login endpoint
 */
export interface SIILoginResponse {
  success: boolean;
  message: string;
  session_active: boolean;
  cookies: SIICookie[];
  contribuyente_info: ContribuyenteInfo;
  encrypted_password: string;
}

/**
 * Result from SII authentication service
 */
export interface SIIAuthResult {
  success: boolean;
  company_id: string;
  session_id: string;
  needs_setup: boolean;
}

/**
 * Error response from SII authentication
 */
export interface SIIAuthError {
  success: false;
  error: string;
}
