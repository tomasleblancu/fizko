/**
 * Helper functions for RUT processing and address formatting
 */

import type { ContribuyenteInfo, CompanyData } from "./types.ts";

/**
 * Normalize RUT to format: {body}{dv_lowercase}
 * Examples: "77.794.858-K" -> "77794858k"
 */
export function normalizeRUT(rut: string): string {
  const rutBody = extractRutBody(rut);
  const dv = extractDV(rut);
  return `${rutBody}${dv.toLowerCase()}`;
}

/**
 * Extract RUT body (without DV)
 */
export function extractRutBody(rut: string): string {
  const cleaned = rut.replace(/[\.\s]/g, "");
  const parts = cleaned.split("-");
  return parts[0];
}

/**
 * Extract DV from RUT
 */
export function extractDV(rut: string): string {
  const cleaned = rut.replace(/[\.\s]/g, "");
  const parts = cleaned.split("-");
  return parts.length > 1 ? parts[1].toUpperCase() : "";
}

/**
 * Extract and format primary address from contributor info
 */
export function extractAddress(contribInfo: ContribuyenteInfo): string | null {
  if (!contribInfo?.direcciones || contribInfo.direcciones.length === 0) {
    return null;
  }

  const mainAddress = contribInfo.direcciones[0];
  const parts = [mainAddress.calle];

  if (mainAddress.numero) {
    parts.push(mainAddress.numero);
  }

  parts.push(mainAddress.comuna);

  return parts.join(", ");
}

/**
 * Build company data object from contributor info
 */
export function buildCompanyData(
  normalizedRut: string,
  contribInfo: ContribuyenteInfo
): CompanyData {
  const address = extractAddress(contribInfo);
  const mainAddress = contribInfo?.direcciones?.[0];

  return {
    rut: normalizedRut,
    business_name:
      contribInfo?.razon_social ||
      contribInfo?.nombre ||
      `Empresa ${normalizedRut}`,
    trade_name: contribInfo?.nombre_fantasia || null,
    address,
    phone: contribInfo?.telefono || mainAddress?.telefono || null,
    email:
      contribInfo?.email || mainAddress?.correo || mainAddress?.mail || null,
  };
}
