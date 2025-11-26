/**
 * Helper functions for date and tax calculations
 */

/**
 * Calculate date range from period string (YYYY-MM)
 * Returns [periodStart, periodEnd] in ISO date format
 *
 * @example
 * calculatePeriodRange("2024-01") => ["2024-01-01", "2024-02-01"]
 * calculatePeriodRange("2024-12") => ["2024-12-01", "2025-01-01"]
 */
export function calculatePeriodRange(
  period: string | null
): [string | null, string | null] {
  if (!period) return [null, null];

  const [yearStr, monthStr] = period.split("-");
  const year = parseInt(yearStr);
  const month = parseInt(monthStr);

  const periodStart = `${year}-${month.toString().padStart(2, "0")}-01`;

  let periodEnd: string;
  if (month === 12) {
    periodEnd = `${year + 1}-01-01`;
  } else {
    periodEnd = `${year}-${(month + 1).toString().padStart(2, "0")}-01`;
  }

  return [periodStart, periodEnd];
}

/**
 * Calculate PPM (Provisional Monthly Payment)
 * PPM is 0.125% of net revenue (12.5 basis points)
 *
 * @param netRevenue - Net revenue for the period
 * @returns PPM amount (0 if netRevenue is negative or zero)
 */
export function calculatePPM(netRevenue: number): number {
  return netRevenue > 0 ? netRevenue * 0.00125 : 0;
}

/**
 * Calculate previous month period
 * Used to fetch previous month's F29 data
 *
 * @param periodStart - Current period start date (YYYY-MM-DD)
 * @returns [year, month] of previous period
 */
export function calculatePreviousMonth(
  periodStart: string
): [number, number] {
  const [yearStr, monthStr] = periodStart.split("-");
  let year = parseInt(yearStr);
  let month = parseInt(monthStr);

  // Calculate previous month
  if (month === 1) {
    year -= 1;
    month = 12;
  } else {
    month -= 1;
  }

  return [year, month];
}
