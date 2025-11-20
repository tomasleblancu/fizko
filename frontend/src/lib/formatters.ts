/**
 * Format utilities for Chilean RUT and other data
 */

/**
 * Formats a Chilean RUT with dots and dash
 * @param value - Raw RUT value (e.g., "123456789" or "12.345.678-9")
 * @returns Formatted RUT (e.g., "12.345.678-9")
 */
export function formatRUT(value: string): string {
  // Remove all non-alphanumeric characters
  const clean = value.replace(/[^0-9kK]/g, '');

  if (clean.length === 0) return '';

  // Separate body and verification digit
  const body = clean.slice(0, -1);
  const dv = clean.slice(-1).toUpperCase();

  if (body.length === 0) return dv;

  // Format body with dots (thousands separator)
  const formattedBody = body.replace(/\B(?=(\d{3})+(?!\d))/g, '.');

  // Return formatted RUT
  return `${formattedBody}-${dv}`;
}

/**
 * Cleans a Chilean RUT to remove formatting
 * @param value - Formatted RUT (e.g., "12.345.678-9")
 * @returns Clean RUT (e.g., "123456789")
 */
export function cleanRUT(value: string): string {
  return value.replace(/[^0-9kK]/g, '');
}

/**
 * Validates a Chilean RUT
 * @param rut - RUT to validate (formatted or clean)
 * @returns true if valid, false otherwise
 */
export function validateRUT(rut: string): boolean {
  const clean = cleanRUT(rut);

  if (clean.length < 2) return false;

  const body = clean.slice(0, -1);
  const dv = clean.slice(-1).toUpperCase();

  // Calculate verification digit
  let sum = 0;
  let multiplier = 2;

  for (let i = body.length - 1; i >= 0; i--) {
    sum += parseInt(body[i]) * multiplier;
    multiplier = multiplier === 7 ? 2 : multiplier + 1;
  }

  const expectedDV = 11 - (sum % 11);
  const calculatedDV = expectedDV === 11 ? '0' : expectedDV === 10 ? 'K' : expectedDV.toString();

  return dv === calculatedDV;
}

/**
 * Extracts the verification digit from a RUT
 * @param rut - RUT (formatted or clean)
 * @returns Verification digit (uppercase)
 */
export function extractDV(rut: string): string {
  const clean = cleanRUT(rut);
  return clean.slice(-1).toUpperCase();
}

/**
 * Extracts the body (without DV) from a RUT
 * @param rut - RUT (formatted or clean)
 * @returns RUT body without verification digit
 */
export function extractRutBody(rut: string): string {
  const clean = cleanRUT(rut);
  return clean.slice(0, -1);
}
