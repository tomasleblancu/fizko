"use client";

import { Users, DollarSign, FileText } from "lucide-react";
import { useMemo } from "react";
import { usePersonnel } from "@/hooks/usePersonnel";

interface PersonnelViewProps {
  companyId?: string;
}

export function PersonnelView({ companyId }: PersonnelViewProps) {
  // Fetch personnel
  const { data: personnelData, isLoading } = usePersonnel({
    companyId: companyId || '',
  });

  const personnel = personnelData?.data || [];

  // Calculate summary stats
  const stats = useMemo(() => {
    if (!personnel.length) return { total: 0, totalSalary: 0, indefiniteContracts: 0 };

    return {
      total: personnel.length,
      totalSalary: personnel.reduce((sum, p) => sum + p.base_salary, 0),
      indefiniteContracts: personnel.filter(p => p.contract_type === 'indefinido').length,
    };
  }, [personnel]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("es-CL", {
      style: "currency",
      currency: "CLP",
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatContractType = (contractType: string | null) => {
    if (!contractType) return '-';

    const types: Record<string, string> = {
      'indefinido': 'Indefinido',
      'plazo_fijo': 'Plazo Fijo',
      'honorarios': 'Honorarios',
      'por_obra': 'Por Obra',
      'part_time': 'Part Time',
    };

    return types[contractType] || contractType;
  };
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
            Personal
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Gestiona tu nómina y empleados
          </p>
        </div>
        <button className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700">
          Agregar Empleado
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
              Total Empleados
            </p>
            <Users className="h-5 w-5 text-emerald-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">
            {isLoading ? "-" : stats.total}
          </p>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
              Gasto Mensual
            </p>
            <DollarSign className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">
            {isLoading ? "-" : formatCurrency(stats.totalSalary)}
          </p>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
              Contratos Indefinidos
            </p>
            <FileText className="h-5 w-5 text-purple-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">
            {isLoading ? "-" : stats.indefiniteContracts}
          </p>
        </div>
      </div>

      {/* Personnel Table */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent" />
        </div>
      ) : personnel.length === 0 ? (
        <div className="rounded-lg border border-slate-200 bg-white p-12 text-center dark:border-slate-700 dark:bg-slate-900">
          <Users className="mx-auto h-12 w-12 text-slate-300 dark:text-slate-600" />
          <p className="mt-2 text-slate-600 dark:text-slate-400">
            No hay empleados registrados
          </p>
        </div>
      ) : (
        <div className="rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="px-6 py-4 text-left text-sm font-medium text-slate-600 dark:text-slate-400">
                    Nombre
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-slate-600 dark:text-slate-400">
                    RUT
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-slate-600 dark:text-slate-400">
                    Cargo
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-slate-600 dark:text-slate-400">
                    Tipo Contrato
                  </th>
                  <th className="px-6 py-4 text-right text-sm font-medium text-slate-600 dark:text-slate-400">
                    Sueldo Base
                  </th>
                  <th className="px-6 py-4 text-right text-sm font-medium text-slate-600 dark:text-slate-400">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody>
                {personnel.map((person) => (
                  <tr
                    key={person.id}
                    className="border-b border-slate-100 last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                  >
                    <td className="px-6 py-4 font-medium text-slate-900 dark:text-white">
                      {person.first_name} {person.last_name}
                    </td>
                    <td className="px-6 py-4 text-slate-600 dark:text-slate-400">
                      {person.rut}
                    </td>
                    <td className="px-6 py-4 text-slate-600 dark:text-slate-400">
                      {person.position_title || '-'}
                    </td>
                    <td className="px-6 py-4">
                      <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-400">
                        {formatContractType(person.contract_type)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right font-medium text-slate-900 dark:text-white">
                      {formatCurrency(person.base_salary)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button className="text-sm font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400">
                        Ver Detalles
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
  );
}
