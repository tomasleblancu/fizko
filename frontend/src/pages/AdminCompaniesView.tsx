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
} from 'lucide-react';
import { useAdminCompanies } from '../hooks/useAdminCompanies';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE_URL } from '../lib/config';
import { apiFetch } from '../lib/api-client';

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

      {/* Companies Grid */}
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
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filteredCompanies.map((company) => (
              <div
                key={company.id}
                onMouseEnter={() => handlePrefetchCompany(company.id)}
                onClick={() => navigate(`/admin/company/${company.id}`)}
                className="group cursor-pointer rounded-lg border border-gray-200 bg-white p-6 shadow-sm transition-all hover:border-blue-500 hover:shadow-md dark:border-gray-700 dark:bg-gray-800 dark:hover:border-blue-600"
              >
                {/* Company Header */}
                <div className="mb-4 flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <Building2 className="h-5 w-5 text-blue-600" />
                      <h3 className="font-semibold text-gray-900 dark:text-white">
                        {company.business_name}
                      </h3>
                    </div>
                    {company.trade_name && (
                      <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                        {company.trade_name}
                      </p>
                    )}
                  </div>
                  <ArrowRight className="h-5 w-5 text-gray-400 transition-transform group-hover:translate-x-1" />
                </div>

                {/* RUT */}
                <div className="mb-4">
                  <p className="text-sm font-mono text-gray-600 dark:text-gray-400">
                    RUT: {company.rut}
                  </p>
                  {company.tax_regime && (
                    <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                      Régimen: {company.tax_regime}
                    </p>
                  )}
                </div>

                {/* Stats */}
                <div className="space-y-2 border-t border-gray-200 pt-4 dark:border-gray-700">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center space-x-2 text-gray-600 dark:text-gray-400">
                      <Users className="h-4 w-4" />
                      <span>Usuarios</span>
                    </div>
                    <span className="font-semibold text-gray-900 dark:text-white">
                      {company.total_users}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center space-x-2 text-gray-600 dark:text-gray-400">
                      <FileText className="h-4 w-4" />
                      <span>Documentos</span>
                    </div>
                    <span className="font-semibold text-gray-900 dark:text-white">
                      {company.total_documents}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center space-x-2 text-gray-600 dark:text-gray-400">
                      <Activity className="h-4 w-4" />
                      <span>Última actividad</span>
                    </div>
                    <span className="text-xs text-gray-600 dark:text-gray-400">
                      {formatDateTime(company.last_activity)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center space-x-2 text-gray-600 dark:text-gray-400">
                      <Calendar className="h-4 w-4" />
                      <span>Creada</span>
                    </div>
                    <span className="text-xs text-gray-600 dark:text-gray-400">
                      {formatDate(company.created_at)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
