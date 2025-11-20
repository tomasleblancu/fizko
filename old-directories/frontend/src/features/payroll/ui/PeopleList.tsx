import { useState, useMemo } from 'react';
import clsx from 'clsx';
import { UserPlus, Mail, Phone, Briefcase, DollarSign } from 'lucide-react';
import { usePeopleQuery, type Person } from "@/shared/hooks/usePeopleQuery";
import { ChateableWrapper } from "@/shared/ui/ChateableWrapper";
import type { ColorScheme } from "@/shared/hooks/useColorScheme";
import type { Company } from "@/shared/types/fizko";

interface PeopleListProps {
  scheme: ColorScheme;
  company: Company | null;
}

export function PeopleList({ scheme, company }: PeopleListProps) {
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive' | 'terminated'>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch ALL people once, filter in frontend
  const { data, isLoading: loading, error } = usePeopleQuery();
  const allPeople = data?.people || [];

  // Filter people in frontend
  const people = useMemo(() => {
    let filtered = allPeople;

    // Filter by status
    if (statusFilter !== 'all') {
      filtered = filtered.filter((person) => person.status === statusFilter);
    }

    // Filter by search term (name or RUT)
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase().trim();
      filtered = filtered.filter((person) => {
        const fullName = `${person.first_name} ${person.last_name}`.toLowerCase();
        const rut = person.rut.toLowerCase();
        return fullName.includes(searchLower) || rut.includes(searchLower);
      });
    }

    return filtered;
  }, [allPeople, statusFilter, searchTerm]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-CL', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getStatusBadge = (status: string) => {
    const baseClasses = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium';

    switch (status) {
      case 'active':
        return (
          <span className={clsx(baseClasses, 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400')}>
            Activo
          </span>
        );
      case 'inactive':
        return (
          <span className={clsx(baseClasses, 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400')}>
            Inactivo
          </span>
        );
      case 'terminated':
        return (
          <span className={clsx(baseClasses, 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400')}>
            Desvinculado
          </span>
        );
      default:
        return (
          <span className={clsx(baseClasses, 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400')}>
            {status}
          </span>
        );
    }
  };

  if (!company) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-slate-500 dark:text-slate-400">
          Selecciona una empresa para ver el personal
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Filters and Search - Fixed header */}
      <div className="flex-shrink-0 py-4 border-b border-slate-200/50 dark:border-slate-700/50">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <input
              type="text"
              placeholder="Buscar por nombre o RUT..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className={clsx(
                "w-full rounded-lg border px-4 py-2.5 pl-10 text-base transition-colors",
                "border-slate-200 bg-white placeholder-slate-400",
                "focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20",
                "dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500"
              )}
            />
            <svg
              className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>

          {/* Filter buttons */}
          <div className="flex gap-2">
            {[
              { value: 'all' as const, label: 'Todos' },
              { value: 'active' as const, label: 'Activos' },
              { value: 'inactive' as const, label: 'Inactivos' },
              { value: 'terminated' as const, label: 'Desvinculados' },
            ].map((filterOption) => (
              <button
                key={filterOption.value}
                onClick={() => setStatusFilter(filterOption.value)}
                className={clsx(
                  "rounded-lg px-4 py-2 text-sm font-medium transition-colors",
                  statusFilter === filterOption.value
                    ? "bg-emerald-600 text-white shadow-sm"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                )}
              >
                {filterOption.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content area - Scrollable */}
      <div className="flex-1 overflow-y-auto">
        {/* Loading state */}
        {loading && (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="m-4 rounded-lg bg-red-50 dark:bg-red-900/20 p-4">
            <p className="text-red-800 dark:text-red-400">{error.message}</p>
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && people.length === 0 && (
        <div className="flex flex-col items-center justify-center h-64 space-y-3">
          <Briefcase className="h-16 w-16 text-slate-300 dark:text-slate-600" />
          <p className="text-slate-500 dark:text-slate-400 text-center">
            {searchTerm || statusFilter !== 'all'
              ? 'No se encontraron empleados con los filtros aplicados'
              : 'No hay empleados registrados aún'}
          </p>
          {!searchTerm && statusFilter === 'all' && (
            <ChateableWrapper
              message="Quiero agregar un nuevo empleado a mi nómina"
              uiComponent="add_employee_button"
              entityType="person"
              contextData={{
                companyId: company.id,
                companyName: company.business_name || company.rut,
              }}
            >
              <button
                className={clsx(
                  'inline-flex items-center gap-2 px-4 py-2 rounded-lg',
                  'bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-700 dark:hover:bg-emerald-600',
                  'text-white font-medium',
                  'transition-colors'
                )}
              >
                <UserPlus className="h-4 w-4" />
                <span>Agregar Primer Empleado</span>
              </button>
            </ChateableWrapper>
          )}
        </div>
      )}

      {/* Desktop table view */}
      {!loading && !error && people.length > 0 && (
        <>
          <div className="hidden md:block overflow-x-auto pt-4">
            <div className="rounded-lg border border-slate-200 dark:border-slate-700">
              <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
              <thead className="bg-slate-50 dark:bg-slate-800/50">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Empleado
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    RUT
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Contacto
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Salario Base
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    AFP / Salud
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Estado
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-slate-900 divide-y divide-slate-200 dark:divide-slate-700">
                {people.map((person) => (
                  <ChateableWrapper
                    key={person.id}
                    as="fragment"
                    message={`Muéstrame la información completa de ${person.first_name} ${person.last_name} (RUT: ${person.rut})`}
                    uiComponent="person_detail"
                    entityId={person.id}
                    entityType="person"
                    contextData={{
                      personId: person.id,
                      rut: person.rut,
                      fullName: `${person.first_name} ${person.last_name}`,
                    }}
                  >
                    <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors cursor-pointer">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-base font-medium text-slate-900 dark:text-slate-100">
                            {person.first_name} {person.last_name}
                          </div>
                          <div className="text-sm text-slate-500 dark:text-slate-400">
                            Ingreso: {formatDate(person.hire_date)}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-base text-slate-900 dark:text-slate-100">
                        {person.rut}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm space-y-1">
                          {person.email && (
                            <div className="flex items-center gap-1 text-slate-600 dark:text-slate-400">
                              <Mail className="h-4 w-4" />
                              <span className="truncate max-w-[150px]">{person.email}</span>
                            </div>
                          )}
                          {person.phone && (
                            <div className="flex items-center gap-1 text-slate-600 dark:text-slate-400">
                              <Phone className="h-4 w-4" />
                              <span>{person.phone}</span>
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-base font-medium text-slate-900 dark:text-slate-100">
                          {formatCurrency(person.base_salary)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm space-y-1">
                          {person.afp_provider && (
                            <div className="text-slate-600 dark:text-slate-400">
                              {person.afp_provider}
                            </div>
                          )}
                          {person.health_provider && (
                            <div className="text-slate-600 dark:text-slate-400">
                              {person.health_provider}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(person.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={(e) => e.stopPropagation()}
                          className="text-emerald-600 hover:text-emerald-900 dark:text-emerald-400 dark:hover:text-emerald-300"
                        >
                          Ver detalles
                        </button>
                      </td>
                    </tr>
                  </ChateableWrapper>
                ))}
              </tbody>
            </table>
            </div>
          </div>

          {/* Mobile card view */}
          <div className="md:hidden space-y-3 p-4">
            {people.map((person) => (
              <ChateableWrapper
                key={person.id}
                message={`Muéstrame la información completa de ${person.first_name} ${person.last_name} (RUT: ${person.rut})`}
                uiComponent="person_detail"
                entityId={person.id}
                entityType="person"
                contextData={{
                  personId: person.id,
                  rut: person.rut,
                  fullName: `${person.first_name} ${person.last_name}`,
                }}
              >
                <div
                  className={clsx(
                    'rounded-lg p-4 space-y-3',
                    'bg-white dark:bg-slate-800',
                    'border border-slate-200 dark:border-slate-700',
                    'shadow-sm cursor-pointer',
                    'hover:border-emerald-500 dark:hover:border-emerald-500',
                    'transition-colors'
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
                        {person.first_name} {person.last_name}
                      </h3>
                      <p className="text-sm text-slate-500 dark:text-slate-400">
                        {person.rut}
                      </p>
                    </div>
                    {getStatusBadge(person.status)}
                  </div>

                  <div className="space-y-2 text-sm">
                    {person.email && (
                      <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                        <Mail className="h-4 w-4 flex-shrink-0" />
                        <span className="truncate">{person.email}</span>
                      </div>
                    )}
                    {person.phone && (
                      <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                        <Phone className="h-4 w-4 flex-shrink-0" />
                        <span>{person.phone}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                      <DollarSign className="h-4 w-4 flex-shrink-0" />
                      <span className="font-medium text-slate-900 dark:text-slate-100">
                        {formatCurrency(person.base_salary)}
                      </span>
                    </div>
                  </div>

                  {(person.afp_provider || person.health_provider) && (
                    <div className="pt-2 border-t border-slate-200 dark:border-slate-700 space-y-1 text-sm">
                      {person.afp_provider && (
                        <div className="text-slate-600 dark:text-slate-400">
                          AFP: {person.afp_provider}
                        </div>
                      )}
                      {person.health_provider && (
                        <div className="text-slate-600 dark:text-slate-400">
                          Salud: {person.health_provider}
                        </div>
                      )}
                    </div>
                  )}

                  <div className="pt-2 border-t border-slate-200 dark:border-slate-700">
                    <button
                      onClick={(e) => e.stopPropagation()}
                      className="w-full text-center py-2 text-sm font-medium text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300"
                    >
                      Ver detalles
                    </button>
                  </div>
                </div>
              </ChateableWrapper>
            ))}
          </div>

          {/* Results count */}
          <div className="p-4 text-sm text-slate-500 dark:text-slate-400 text-center border-t border-slate-200/50 dark:border-slate-700/50">
            Mostrando {people.length} empleado{people.length !== 1 ? 's' : ''}
          </div>
        </>
        )}
      </div>
    </div>
  );
}
