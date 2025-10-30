import { useState, useEffect, useCallback } from 'react';
import { useAuth } from "@/app/providers/AuthContext";
import type { PayrollSummary } from "@/shared/types/fizko";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";

export function usePayroll(companyId: string | null, period?: string) {
  const { session } = useAuth();
  const [payrollSummary, setPayrollSummary] = useState<PayrollSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPayrollSummary = useCallback(async () => {
    if (!session?.access_token || !companyId) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (period) {
        params.append('period', period);
      }

      const url = `${API_BASE_URL}/payroll-summary/${companyId}${params.toString() ? `?${params.toString()}` : ''}`;

      const response = await apiFetch(url, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // 404 is expected for new companies without payroll data yet
        if (response.status === 404) {
          setPayrollSummary(null);
          setError(null);
          return;
        }
        throw new Error(`Failed to fetch payroll summary: ${response.statusText}`);
      }

      const data = await response.json();
      setPayrollSummary(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch payroll summary');
      setPayrollSummary(null);
    } finally {
      setLoading(false);
    }
  }, [session?.access_token, companyId, period]);

  useEffect(() => {
    fetchPayrollSummary();
  }, [fetchPayrollSummary]);

  return {
    payrollSummary,
    loading,
    error,
    refresh: fetchPayrollSummary,
  };
}
