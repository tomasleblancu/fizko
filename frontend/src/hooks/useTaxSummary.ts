"use client";

import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/lib/query-keys";
import type { TaxSummary } from "@/types/tax";

interface UseTaxSummaryOptions {
  companyId: string;
  period?: string; // Format: YYYY-MM
}

/**
 * Hook to fetch tax summary for a company and period
 *
 * Calculates Chilean tax summary including:
 * - Sales revenue and IVA collected
 * - Purchase expenses and IVA paid
 * - Net IVA (iva_collected - iva_paid)
 * - Previous month credit from Form29
 * - PPM (0.125% of net revenue)
 * - Retención from honorarios receipts
 * - Monthly tax calculation
 *
 * @param companyId - Company UUID
 * @param period - Optional period in YYYY-MM format (defaults to current month)
 */
export function useTaxSummary({ companyId, period }: UseTaxSummaryOptions) {
  return useQuery({
    queryKey: queryKeys.taxSummary.byCompany(companyId, period),
    queryFn: async (): Promise<TaxSummary> => {
      const params = new URLSearchParams({ companyId });
      if (period) {
        params.append('period', period);
      }

      const response = await fetch(`/api/tax-summary?${params.toString()}`);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to fetch tax summary');
      }

      return response.json();
    },
    enabled: !!companyId,
    staleTime: 2 * 60 * 1000, // 2 minutes - same as other hooks
    refetchOnWindowFocus: true,
  });
}
