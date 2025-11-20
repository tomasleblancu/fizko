import { useState } from 'react';
import {
  FileText,
  Filter,
  Calendar,
  DollarSign,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  Clock,
  XCircle,
  AlertCircle,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { API_BASE_URL } from "@/shared/lib/config";
import { useAuth } from "@/app/providers/AuthContext";

interface Form29Generated {
  id: string;
  company_id: string;
  period_year: number;
  period_month: number;
  total_sales: number;
  taxable_sales: number;
  exempt_sales: number;
  sales_tax: number;
  total_purchases: number;
  taxable_purchases: number;
  purchases_tax: number;
  iva_to_pay: number;
  iva_credit: number;
  net_iva: number;
  status: string; // draft, validated, confirmed, submitted, paid, cancelled
  submission_date: string | null;
  folio: string | null;
  created_at: string;
  updated_at: string;
}

interface Form29GeneratedListProps {
  companyId: string;
}

export default function Form29GeneratedList({ companyId }: Form29GeneratedListProps) {
  const { session } = useAuth();
  const [selectedYear, setSelectedYear] = useState<number | 'all'>('all');
  const [selectedStatus, setSelectedStatus] = useState<string | 'all'>('all');

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);

  // Fetch F29 generated forms
  const { data, isLoading: loading, error } = useQuery({
    queryKey: ['form29-generated', companyId, selectedYear, selectedStatus],
    queryFn: async () => {
      const params = new URLSearchParams({ company_id: companyId });
      if (selectedYear !== 'all') params.append('period_year', selectedYear.toString());
      if (selectedStatus !== 'all') params.append('status', selectedStatus);

      const response = await fetch(`${API_BASE_URL}/api/form29?${params}`, {
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch Form29 records');
      }

      const result = await response.json();
      return result.data as Form29Generated[];
    },
    enabled: !!session?.access_token && !!companyId,
  });

  const forms = data || [];

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('es-CL', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      draft: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
      validated: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300',
      confirmed: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300',
      submitted: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300',
      paid: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-300',
      cancelled: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300',
    };

    const labels = {
      draft: 'Borrador',
      validated: 'Validado',
      confirmed: 'Confirmado',
      submitted: 'Presentado',
      paid: 'Pagado',
      cancelled: 'Cancelado',
    };

    return (
      <span
        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
          styles[status as keyof typeof styles] || styles.draft
        }`}
      >
        {labels[status as keyof typeof labels] || status}
      </span>
    );
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'submitted':
      case 'paid':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'confirmed':
      case 'validated':
        return <Clock className="h-4 w-4 text-blue-600" />;
      case 'cancelled':
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getMonthName = (month: number) => {
    const months = [
      'Enero',
      'Febrero',
      'Marzo',
      'Abril',
      'Mayo',
      'Junio',
      'Julio',
      'Agosto',
      'Septiembre',
      'Octubre',
      'Noviembre',
      'Diciembre',
    ];
    return months[month - 1] || month.toString();
  };

  if (loading) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
            <p className="text-gray-600 dark:text-gray-400">Cargando formularios generados...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 dark:border-red-800 dark:bg-red-900/20">
        <div className="flex items-start space-x-3">
          <XCircle className="h-5 w-5 flex-shrink-0 text-red-600 dark:text-red-400" />
          <div>
            <h3 className="font-medium text-red-800 dark:text-red-300">Error al cargar formularios</h3>
            <p className="mt-1 text-sm text-red-700 dark:text-red-400">
              {error instanceof Error ? error.message : 'Error desconocido'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
      {/* Header */}
      <div className="mb-6 flex flex-col space-y-4 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
        <div className="flex items-center space-x-2">
          <FileText className="h-5 w-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Formularios 29 Generados ({forms.length})
          </h2>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-2">
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(e.target.value === 'all' ? 'all' : parseInt(e.target.value))}
              className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 shadow-sm transition-colors hover:border-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:hover:border-gray-500"
            >
              <option value="all">Todos los años</option>
              {years.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </div>

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 shadow-sm transition-colors hover:border-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:hover:border-gray-500"
          >
            <option value="all">Todos los estados</option>
            <option value="draft">Borrador</option>
            <option value="validated">Validado</option>
            <option value="confirmed">Confirmado</option>
            <option value="submitted">Presentado</option>
            <option value="paid">Pagado</option>
            <option value="cancelled">Cancelado</option>
          </select>
        </div>
      </div>

      {/* Forms List */}
      {forms.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center dark:border-gray-700 dark:bg-gray-900/50">
          <FileText className="mx-auto mb-3 h-12 w-12 text-gray-400" />
          <p className="text-gray-600 dark:text-gray-400">No se encontraron formularios generados</p>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-500">
            Los formularios se generan automáticamente cuando hay datos de ventas y compras
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {forms.map((form) => (
            <div
              key={form.id}
              className="rounded-lg border border-gray-200 bg-gray-50 p-4 transition-colors hover:bg-gray-100 dark:border-gray-700 dark:bg-gray-900/50 dark:hover:bg-gray-900"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {/* Period and Status */}
                  <div className="mb-2 flex items-center space-x-3">
                    <div className="flex items-center space-x-2">
                      <Calendar className="h-4 w-4 text-gray-400" />
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {getMonthName(form.period_month)} {form.period_year}
                      </span>
                    </div>
                    {getStatusBadge(form.status)}
                    <div className="flex items-center space-x-1" title={`Estado: ${form.status}`}>
                      {getStatusIcon(form.status)}
                    </div>
                  </div>

                  {/* Details Grid */}
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    {/* Sales */}
                    <div className="rounded-md bg-green-50 p-3 dark:bg-green-900/20">
                      <div className="flex items-center space-x-1 mb-1">
                        <TrendingUp className="h-3.5 w-3.5 text-green-600" />
                        <p className="text-xs font-medium text-green-700 dark:text-green-400">Ventas</p>
                      </div>
                      <p className="text-sm font-semibold text-gray-900 dark:text-white">
                        {formatCurrency(form.total_sales)}
                      </p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        IVA: {formatCurrency(form.sales_tax)}
                      </p>
                    </div>

                    {/* Purchases */}
                    <div className="rounded-md bg-blue-50 p-3 dark:bg-blue-900/20">
                      <div className="flex items-center space-x-1 mb-1">
                        <TrendingDown className="h-3.5 w-3.5 text-blue-600" />
                        <p className="text-xs font-medium text-blue-700 dark:text-blue-400">Compras</p>
                      </div>
                      <p className="text-sm font-semibold text-gray-900 dark:text-white">
                        {formatCurrency(form.total_purchases)}
                      </p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        IVA: {formatCurrency(form.purchases_tax)}
                      </p>
                    </div>

                    {/* Net IVA */}
                    <div className={`rounded-md p-3 ${
                      form.net_iva > 0
                        ? 'bg-orange-50 dark:bg-orange-900/20'
                        : 'bg-emerald-50 dark:bg-emerald-900/20'
                    }`}>
                      <div className="flex items-center space-x-1 mb-1">
                        <DollarSign className={`h-3.5 w-3.5 ${
                          form.net_iva > 0 ? 'text-orange-600' : 'text-emerald-600'
                        }`} />
                        <p className={`text-xs font-medium ${
                          form.net_iva > 0
                            ? 'text-orange-700 dark:text-orange-400'
                            : 'text-emerald-700 dark:text-emerald-400'
                        }`}>
                          IVA Neto
                        </p>
                      </div>
                      <p className="text-sm font-semibold text-gray-900 dark:text-white">
                        {formatCurrency(Math.abs(form.net_iva))}
                      </p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        {form.net_iva > 0 ? 'A pagar' : 'A favor'}
                      </p>
                    </div>

                    {/* Submission Info */}
                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Folio</p>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {form.folio || 'Sin folio'}
                      </p>
                      {form.submission_date && (
                        <>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Presentado</p>
                          <p className="text-xs text-gray-900 dark:text-white">{formatDate(form.submission_date)}</p>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Metadata */}
                  <div className="mt-3 flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                    <span>Creado: {formatDate(form.created_at)}</span>
                    <span>Actualizado: {formatDate(form.updated_at)}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Summary */}
      {forms.length > 0 && (
        <div className="mt-6 grid gap-4 border-t border-gray-200 pt-6 sm:grid-cols-4 dark:border-gray-700">
          <div className="rounded-lg bg-gray-50 p-4 dark:bg-gray-900/50">
            <p className="text-sm text-gray-600 dark:text-gray-400">Borradores</p>
            <p className="mt-1 text-2xl font-bold text-gray-700 dark:text-gray-300">
              {forms.filter((f) => f.status === 'draft').length}
            </p>
          </div>
          <div className="rounded-lg bg-blue-50 p-4 dark:bg-blue-900/20">
            <p className="text-sm text-gray-600 dark:text-gray-400">Validados</p>
            <p className="mt-1 text-2xl font-bold text-blue-700 dark:text-blue-400">
              {forms.filter((f) => f.status === 'validated').length}
            </p>
          </div>
          <div className="rounded-lg bg-green-50 p-4 dark:bg-green-900/20">
            <p className="text-sm text-gray-600 dark:text-gray-400">Presentados</p>
            <p className="mt-1 text-2xl font-bold text-green-700 dark:text-green-400">
              {forms.filter((f) => f.status === 'submitted' || f.status === 'paid').length}
            </p>
          </div>
          <div className="rounded-lg bg-red-50 p-4 dark:bg-red-900/20">
            <p className="text-sm text-gray-600 dark:text-gray-400">Cancelados</p>
            <p className="mt-1 text-2xl font-bold text-red-700 dark:text-red-400">
              {forms.filter((f) => f.status === 'cancelled').length}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
