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
  ArrowRight,
  Bell,
  ListTodo,
} from 'lucide-react';
import { useAdminCompanies } from "@/shared/hooks/useAdminCompanies";
import { useAuth } from "@/app/providers/AuthContext";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";

export default function AdminCompaniesView() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
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

  const filteredCompanies = companies.filter((company) =>
    company.business_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    company.rut.includes(searchTerm) ||
    (company.trade_name?.toLowerCase() || '').includes(searchTerm.toLowerCase())
  );

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

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Empresas
              </h1>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                {companies.length} {companies.length === 1 ? 'empresa' : 'empresas'} disponibles
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate('/admin/task-manager')}
                className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
              >
                <ListTodo className="h-4 w-4" />
                Gestor de Tareas
              </button>
              <button
                onClick={() => navigate('/admin/event-templates')}
                className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
              >
                <Calendar className="h-4 w-4" />
                Templates de Eventos
              </button>
              <button
                onClick={() => navigate('/admin/notification-templates')}
                className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
              >
                <Bell className="h-4 w-4" />
                Templates de Notificaciones
              </button>
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
        {filteredCompanies.length === 0 ? (
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
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                      Empresa
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                      RUT
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                      Régimen
                    </th>
                    <th scope="col" className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                      Usuarios
                    </th>
                    <th scope="col" className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                      Documentos
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                      F29
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                      Última Actividad
                    </th>
                    <th scope="col" className="relative px-6 py-3">
                      <span className="sr-only">Ver</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800">
                  {filteredCompanies.map((company) => (
                    <tr
                      key={company.id}
                      onMouseEnter={() => handlePrefetchCompany(company.id)}
                      onClick={() => navigate(`/admin/company/${company.id}`)}
                      className="cursor-pointer transition-colors hover:bg-gray-50 dark:hover:bg-gray-700/50"
                    >
                      <td className="whitespace-nowrap px-6 py-4">
                        <div className="flex items-center">
                          <Building2 className="h-5 w-5 text-blue-600 mr-3 flex-shrink-0" />
                          <div>
                            <div className="font-medium text-gray-900 dark:text-white">
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
                      <td className="whitespace-nowrap px-6 py-4 text-sm font-mono text-gray-900 dark:text-white">
                        {company.rut}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                        {company.tax_regime || '-'}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-center text-sm text-gray-900 dark:text-white">
                        {company.total_users}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-center text-sm text-gray-900 dark:text-white">
                        {company.total_documents}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        {company.latest_f29_status ? (
                          <div className="flex flex-col">
                            <span className={`inline-flex w-fit rounded-full px-2 py-0.5 text-xs font-medium ${
                              company.latest_f29_status === 'saved' || company.latest_f29_status === 'paid'
                                ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                                : company.latest_f29_status === 'draft'
                                ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
                                : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400'
                            }`}>
                              {company.latest_f29_status === 'draft' ? 'Borrador' :
                               company.latest_f29_status === 'saved' ? 'Guardado' :
                               company.latest_f29_status === 'paid' ? 'Pagado' :
                               company.latest_f29_status}
                            </span>
                            <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                              {company.latest_f29_period}
                            </span>
                          </div>
                        ) : (
                          <span className="text-sm text-gray-400 dark:text-gray-500">-</span>
                        )}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                        {formatDateTime(company.last_activity)}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-right text-sm font-medium">
                        <ArrowRight className="inline h-5 w-5 text-gray-400 transition-transform group-hover:translate-x-1" />
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
