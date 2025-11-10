import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import {
  Building2,
  Users,
  FileText,
  Calendar,
  Activity,
  Search,
  ArrowUpDown,
  ExternalLink,
  ArrowLeft,
} from 'lucide-react';
import { useAdminCompanies } from "@/shared/hooks/useAdminCompanies";
import { useAuth } from "@/app/providers/AuthContext";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";

type SortField = 'business_name' | 'rut' | 'total_users' | 'total_documents' | 'created_at' | 'last_activity';
type SortDirection = 'asc' | 'desc';

export default function CompaniesTablePage() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<SortField>('business_name');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const queryClient = useQueryClient();
  const { session } = useAuth();

  // Use React Query hook
  const { data: companies = [], isLoading: loading, error } = useAdminCompanies();

  // Prefetch company details on hover for instant navigation
  const handlePrefetchCompany = (companyId: string) => {
    queryClient.prefetchQuery({
      queryKey: ['admin', 'company', companyId],
      queryFn: async () => {
        if (!session?.access_token) {
          throw new Error('No authenticated session');
        }

        const response = await apiFetch(`${API_BASE_URL}/admin/company/${companyId}`, {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch company data');
        }

        return response.json();
      },
      staleTime: 3 * 60 * 1000,
    });
  };

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('es-CL', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatDateTime = (dateString: string | null) => {
    if (!dateString) return 'Nunca';
    return new Date(dateString).toLocaleString('es-CL', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Filter and sort companies
  const filteredAndSortedCompanies = companies
    .filter((company) =>
      company.business_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      company.rut.includes(searchTerm) ||
      (company.trade_name?.toLowerCase() || '').includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      let aValue: any = a[sortField];
      let bValue: any = b[sortField];

      // Handle null values
      if (aValue === null) return 1;
      if (bValue === null) return -1;

      // Convert to comparable values
      if (sortField === 'created_at' || sortField === 'last_activity') {
        aValue = new Date(aValue).getTime();
        bValue = new Date(bValue).getTime();
      }

      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="text-gray-600 dark:text-gray-400">Cargando empresas...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <p className="mb-4 text-red-600 dark:text-red-400">
            {error instanceof Error ? error.message : 'Error desconocido'}
          </p>
          <button
            onClick={() => navigate(-1)}
            className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
          >
            Volver
          </button>
        </div>
      </div>
    );
  }

  const SortIcon = ({ field }: { field: SortField }) => (
    <ArrowUpDown
      className={`ml-1 inline h-4 w-4 ${
        sortField === field ? 'text-blue-600' : 'text-gray-400'
      }`}
    />
  );

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/admin')}
                className="rounded-lg p-2 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <ArrowLeft className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              </button>
              <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                  Empresas
                </h1>
                <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                  {companies.length} {companies.length === 1 ? 'empresa' : 'empresas'} registradas
                </p>
              </div>
            </div>
          </div>

          {/* Search bar */}
          <div className="mt-6">
            <div className="relative">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                placeholder="Buscar por nombre, RUT o nombre comercial..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="block w-full rounded-lg border border-gray-300 bg-white py-2 pl-10 pr-3 text-gray-900 placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Companies Table */}
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {filteredAndSortedCompanies.length === 0 ? (
          <div className="rounded-lg border border-gray-200 bg-white p-12 text-center dark:border-gray-700 dark:bg-gray-800">
            <Building2 className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">
              No se encontraron empresas
            </h3>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              {searchTerm
                ? 'Intenta con otro término de búsqueda'
                : 'No hay empresas disponibles'}
            </p>
          </div>
        ) : (
          <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow dark:border-gray-700 dark:bg-gray-800">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-900">
                  <tr>
                    <th
                      scope="col"
                      className="cursor-pointer px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
                      onClick={() => handleSort('business_name')}
                    >
                      Empresa
                      <SortIcon field="business_name" />
                    </th>
                    <th
                      scope="col"
                      className="cursor-pointer px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
                      onClick={() => handleSort('rut')}
                    >
                      RUT
                      <SortIcon field="rut" />
                    </th>
                    <th
                      scope="col"
                      className="cursor-pointer px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
                      onClick={() => handleSort('total_users')}
                    >
                      <Users className="inline h-4 w-4 mr-1" />
                      Usuarios
                      <SortIcon field="total_users" />
                    </th>
                    <th
                      scope="col"
                      className="cursor-pointer px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
                      onClick={() => handleSort('total_documents')}
                    >
                      <FileText className="inline h-4 w-4 mr-1" />
                      Documentos
                      <SortIcon field="total_documents" />
                    </th>
                    <th
                      scope="col"
                      className="cursor-pointer px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
                      onClick={() => handleSort('last_activity')}
                    >
                      <Activity className="inline h-4 w-4 mr-1" />
                      Última Actividad
                      <SortIcon field="last_activity" />
                    </th>
                    <th
                      scope="col"
                      className="cursor-pointer px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
                      onClick={() => handleSort('created_at')}
                    >
                      <Calendar className="inline h-4 w-4 mr-1" />
                      Creada
                      <SortIcon field="created_at" />
                    </th>
                    <th scope="col" className="relative px-6 py-3">
                      <span className="sr-only">Acciones</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800">
                  {filteredAndSortedCompanies.map((company) => (
                    <tr
                      key={company.id}
                      onMouseEnter={() => handlePrefetchCompany(company.id)}
                      className="transition-colors hover:bg-gray-50 dark:hover:bg-gray-700"
                    >
                      <td className="whitespace-nowrap px-6 py-4">
                        <div className="flex items-center">
                          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/20">
                            <Building2 className="h-5 w-5 text-blue-600" />
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900 dark:text-white">
                              {company.business_name}
                            </div>
                            {company.trade_name && (
                              <div className="text-sm text-gray-500 dark:text-gray-400">
                                {company.trade_name}
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <div className="text-sm font-mono text-gray-900 dark:text-white">
                          {company.rut}
                        </div>
                        {company.tax_regime && (
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            {company.tax_regime}
                          </div>
                        )}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-center">
                        <span className="inline-flex rounded-full bg-green-100 px-2 py-1 text-xs font-semibold text-green-800 dark:bg-green-900/20 dark:text-green-400">
                          {company.total_users}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-center">
                        <span className="inline-flex rounded-full bg-blue-100 px-2 py-1 text-xs font-semibold text-blue-800 dark:bg-blue-900/20 dark:text-blue-400">
                          {company.total_documents}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                        {formatDateTime(company.last_activity)}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                        {formatDate(company.created_at)}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-right text-sm font-medium">
                        <button
                          onClick={() => navigate(`/admin/company/${company.id}`)}
                          className="flex items-center space-x-1 text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                        >
                          <span>Ver</span>
                          <ExternalLink className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
