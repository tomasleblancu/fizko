/**
 * Example usage of iva-summary edge function from frontend
 *
 * This can be used in React components, hooks, or services
 */

import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client (usually done once in app setup)
const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

interface IvaSummary {
  debito_fiscal: number;
  credito_fiscal: number;
  balance: number;
  previous_month_credit: number;
  overdue_iva_credit: number;
  ppm: number;
  retencion: number;
  reverse_charge_withholding: number;
  sales_count: number;
  purchases_count: number;
}

/**
 * Get IVA summary for a company and period
 */
export async function getIvaSummary(
  companyId: string,
  period?: string // YYYY-MM format
): Promise<IvaSummary> {
  const { data, error } = await supabase.functions.invoke('iva-summary', {
    body: {
      company_id: companyId,
      period: period,
    },
  });

  if (error) {
    console.error('Error calling iva-summary function:', error);
    throw error;
  }

  return data as IvaSummary;
}

// ==============================================================================
// REACT HOOK EXAMPLE
// ==============================================================================

import { useQuery } from '@tanstack/react-query';

export function useIvaSummary(companyId: string | undefined, period?: string) {
  return useQuery({
    queryKey: ['iva-summary', companyId, period],
    queryFn: () => {
      if (!companyId) throw new Error('Company ID is required');
      return getIvaSummary(companyId, period);
    },
    enabled: !!companyId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// ==============================================================================
// REACT COMPONENT EXAMPLE
// ==============================================================================

export function IvaSummaryCard({ companyId, period }: { companyId: string; period?: string }) {
  const { data, isLoading, error } = useIvaSummary(companyId, period);

  if (isLoading) return <div>Cargando resumen de IVA...</div>;
  if (error) return <div>Error: {error.message}</div>;
  if (!data) return null;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">Resumen IVA</h2>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-gray-600">Débito Fiscal</p>
          <p className="text-2xl font-bold text-green-600">
            ${data.debito_fiscal.toLocaleString('es-CL')}
          </p>
        </div>

        <div>
          <p className="text-gray-600">Crédito Fiscal</p>
          <p className="text-2xl font-bold text-blue-600">
            ${data.credito_fiscal.toLocaleString('es-CL')}
          </p>
        </div>

        <div className="col-span-2 border-t pt-4">
          <p className="text-gray-600">Balance</p>
          <p className={`text-2xl font-bold ${data.balance > 0 ? 'text-red-600' : 'text-green-600'}`}>
            ${data.balance.toLocaleString('es-CL')}
          </p>
        </div>

        {data.previous_month_credit > 0 && (
          <div>
            <p className="text-gray-600 text-sm">Crédito Mes Anterior</p>
            <p className="text-lg font-semibold">
              ${data.previous_month_credit.toLocaleString('es-CL')}
            </p>
          </div>
        )}

        {data.ppm > 0 && (
          <div>
            <p className="text-gray-600 text-sm">PPM</p>
            <p className="text-lg font-semibold">
              ${data.ppm.toLocaleString('es-CL')}
            </p>
          </div>
        )}

        {data.retencion > 0 && (
          <div>
            <p className="text-gray-600 text-sm">Retención</p>
            <p className="text-lg font-semibold">
              ${data.retencion.toLocaleString('es-CL')}
            </p>
          </div>
        )}

        {data.overdue_iva_credit > 0 && (
          <div className="col-span-2 bg-yellow-50 p-3 rounded">
            <p className="text-yellow-800 text-sm font-medium">
              IVA Fuera de Plazo: ${data.overdue_iva_credit.toLocaleString('es-CL')}
            </p>
          </div>
        )}

        <div className="col-span-2 text-sm text-gray-500 mt-2">
          <p>{data.sales_count} documentos de venta • {data.purchases_count} documentos de compra</p>
        </div>
      </div>
    </div>
  );
}

// ==============================================================================
// COMPARISON WITH BACKEND ENDPOINT
// ==============================================================================

/**
 * For comparison: calling the Python backend endpoint
 *
 * This is the traditional way using FastAPI
 */
export async function getIvaSummaryFromBackend(
  companyId: string,
  period?: string
): Promise<IvaSummary> {
  const params = new URLSearchParams();
  params.append('company_id', companyId);
  if (period) params.append('period', period);

  const response = await fetch(
    `${import.meta.env.VITE_BACKEND_URL}/api/tax/summary/iva?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${await supabase.auth.getSession().then(s => s.data.session?.access_token)}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

// ==============================================================================
// PERFORMANCE COMPARISON UTILITY
// ==============================================================================

export async function comparePerformance(companyId: string, period: string) {
  console.log('Comparing Edge Function vs Backend Endpoint...');

  // Test Edge Function
  const edgeStart = performance.now();
  const edgeResult = await getIvaSummary(companyId, period);
  const edgeTime = performance.now() - edgeStart;

  // Test Backend Endpoint
  const backendStart = performance.now();
  const backendResult = await getIvaSummaryFromBackend(companyId, period);
  const backendTime = performance.now() - backendStart;

  console.log('Results:');
  console.log('--------');
  console.log(`Edge Function: ${edgeTime.toFixed(2)}ms`);
  console.log(`Backend Endpoint: ${backendTime.toFixed(2)}ms`);
  console.log(`Difference: ${(backendTime - edgeTime).toFixed(2)}ms`);
  console.log(`Edge Function is ${((backendTime / edgeTime) * 100 - 100).toFixed(1)}% faster`);

  // Verify results match
  const resultsMatch = JSON.stringify(edgeResult) === JSON.stringify(backendResult);
  console.log(`Results match: ${resultsMatch ? '✅' : '❌'}`);

  return {
    edgeTime,
    backendTime,
    edgeResult,
    backendResult,
    resultsMatch,
  };
}
