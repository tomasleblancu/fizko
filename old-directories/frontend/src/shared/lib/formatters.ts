// Memoized formatters to avoid recreating Intl instances on every render

const currencyFormatter = new Intl.NumberFormat('es-CL', {
  style: 'currency',
  currency: 'CLP',
  minimumFractionDigits: 0,
});

const shortDateFormatter = new Intl.DateTimeFormat('es-CL', {
  day: 'numeric',
  month: 'short',
});

const mediumDateFormatter = new Intl.DateTimeFormat('es-CL', {
  month: 'short',
  year: 'numeric',
});

const longDateFormatter = new Intl.DateTimeFormat('es-CL', {
  month: 'long',
  year: 'numeric',
});

export function formatCurrency(amount: number): string {
  return currencyFormatter.format(amount);
}

export function formatShortDate(dateStr: string): string {
  return shortDateFormatter.format(new Date(dateStr));
}

export function formatMediumDate(dateStr: string): string {
  return mediumDateFormatter.format(new Date(dateStr));
}

export function formatLongDate(dateStr: string): string {
  return longDateFormatter.format(new Date(dateStr));
}

/**
 * Formats a Chilean RUT to the standard format: NN.NNN.NNN-N
 * Accepts RUT in any format (with or without dots/dash) and returns formatted version
 *
 * @param value - RUT string in any format
 * @returns Formatted RUT string (e.g., "12.345.678-9")
 *
 * @example
 * formatRUT("123456789") => "12.345.678-9"
 * formatRUT("12345678-9") => "12.345.678-9"
 * formatRUT("12.345.678-9") => "12.345.678-9"
 */
export function formatRUT(value: string): string {
  // Remove all non-alphanumeric characters (keep only numbers and letters for DV)
  const clean = value.replace(/[^0-9kK]/g, '');

  // If empty, return empty
  if (!clean) return '';

  // Extract body (all digits) and DV (last character)
  const body = clean.slice(0, -1);
  const dv = clean.slice(-1).toUpperCase();

  // If only one character, just return it
  if (clean.length === 1) return clean;

  // Format body with dots (reverse, add dots every 3 digits, reverse back)
  const reversedBody = body.split('').reverse().join('');
  const formattedBody = reversedBody.match(/.{1,3}/g)?.join('.') || '';
  const finalBody = formattedBody.split('').reverse().join('');

  // Return formatted RUT
  return `${finalBody}-${dv}`;
}

/**
 * Cleans a RUT string by removing all formatting (dots and dash)
 * Useful for sending to backend API
 *
 * @param value - Formatted or unformatted RUT string
 * @returns Clean RUT string (e.g., "123456789")
 *
 * @example
 * cleanRUT("12.345.678-9") => "123456789"
 * cleanRUT("12345678-9") => "123456789"
 */
export function cleanRUT(value: string): string {
  return value.replace(/[^0-9kK]/g, '');
}
