/**
 * Date utility functions for handling ISO date strings without timezone issues
 *
 * When using new Date(dateString) with ISO date-only strings (e.g., "2024-10-31"),
 * JavaScript interprets them as UTC midnight, which can cause timezone offset issues
 * when displaying in local time (Chile is UTC-3).
 *
 * These utilities parse dates as local timezone to avoid shifts.
 */

/**
 * Parse ISO date string (YYYY-MM-DD) as local date to avoid timezone shifts
 * @param dateString ISO date string in format "YYYY-MM-DD"
 * @returns Date object in local timezone
 *
 * @example
 * parseLocalDate("2024-10-31") // October 31, 2024 at 00:00 local time
 * // vs
 * new Date("2024-10-31") // October 31, 2024 at 00:00 UTC (may display as Oct 30 in Chile)
 */
export function parseLocalDate(dateString: string): Date {
  const [year, month, day] = dateString.split('-').map(Number);
  return new Date(year, month - 1, day);
}

/**
 * Get year from ISO date string safely (no timezone issues)
 * @param dateString ISO date string in format "YYYY-MM-DD"
 * @returns Year as number
 */
export function getYear(dateString: string): number {
  return parseLocalDate(dateString).getFullYear();
}

/**
 * Get month from ISO date string safely (no timezone issues)
 * @param dateString ISO date string in format "YYYY-MM-DD"
 * @returns Month as number (1-12)
 */
export function getMonth(dateString: string): number {
  return parseLocalDate(dateString).getMonth() + 1;
}

/**
 * Get timestamp for sorting ISO date strings (no timezone issues)
 * @param dateString ISO date string in format "YYYY-MM-DD"
 * @returns Unix timestamp in milliseconds
 */
export function getTimestamp(dateString: string): number {
  return parseLocalDate(dateString).getTime();
}

/**
 * Format ISO date string to localized date (Chilean Spanish)
 * @param dateString ISO date string in format "YYYY-MM-DD"
 * @param options Intl.DateTimeFormat options
 * @returns Formatted date string
 */
export function formatDate(
  dateString: string,
  options: Intl.DateTimeFormatOptions = {
    weekday: "long",
    day: "numeric",
    month: "long",
  }
): string {
  const date = parseLocalDate(dateString);
  return new Intl.DateTimeFormat("es-CL", options).format(date);
}
