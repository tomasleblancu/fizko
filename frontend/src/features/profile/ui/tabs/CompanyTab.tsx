import { useState, useEffect } from 'react';
import { Building2, FileText, Edit2, CheckCircle2, XCircle, HelpCircle } from 'lucide-react';
import { ChateableWrapper } from '@/shared/ui/ChateableWrapper';
import { useCompanySettings } from '@/shared/hooks/useCompanySettings';
import type { ColorScheme } from '@/shared/hooks/useColorScheme';
import type { Company } from '@/shared/types/fizko';

interface CompanyTabProps {
  company: Company | null;
  scheme: ColorScheme;
  isInDrawer?: boolean;
  preloadedSettings?: any;
  preloadedLoading?: boolean;
}

export function CompanyTab({
  company,
  scheme,
  isInDrawer = false,
  preloadedSettings,
  preloadedLoading
}: CompanyTabProps) {
  const { settings: fetchedSettings, updateSettings, loading: fetchedLoading } = useCompanySettings(company?.id);
  const settings = preloadedSettings !== undefined ? preloadedSettings : fetchedSettings;
  const settingsLoading = preloadedLoading !== undefined ? preloadedLoading : fetchedLoading;
  const [isEditing, setIsEditing] = useState(false);
  const [editedSettings, setEditedSettings] = useState(settings);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setEditedSettings(settings);
  }, [settings]);

  const handleToggleSetting = (key: keyof typeof editedSettings) => {
    if (!editedSettings) return;
    const currentValue = editedSettings[key];
    let newValue: boolean | null;
    if (currentValue === null) {
      newValue = true;
    } else if (currentValue === true) {
      newValue = false;
    } else {
      newValue = null;
    }
    setEditedSettings({ ...editedSettings, [key]: newValue });
  };

  const handleSave = async () => {
    if (!editedSettings || !company?.id) return;
    setIsSaving(true);
    try {
      await updateSettings.mutateAsync({
        has_formal_employees: editedSettings.has_formal_employees,
        has_imports: editedSettings.has_imports,
        has_exports: editedSettings.has_exports,
        has_lease_contracts: editedSettings.has_lease_contracts,
      });
      setIsEditing(false);
    } catch (error) {
      console.error('Error saving settings:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setEditedSettings(settings);
    setIsEditing(false);
  };

  const renderSettingIcon = (value: boolean | null) => {
    if (value === true) {
      return <CheckCircle2 className="h-5 w-5 text-emerald-500" />;
    } else if (value === false) {
      return <XCircle className="h-5 w-5 text-rose-500" />;
    }
    return <HelpCircle className="h-5 w-5 text-slate-400" />;
  };

  return (
    <div className="space-y-6">
      {/* Company Info */}
      {company ? (
        <>
          <div>
            <h3 className="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">
              Mi Empresa
            </h3>

            <div className="space-y-4">
              {/* Company Header */}
              <div className="flex items-center gap-4">
                <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-600 to-teal-700 text-xl font-bold text-white shadow-md">
                  {company.business_name?.charAt(0).toUpperCase() || 'E'}
                </div>
                <div className="min-w-0 flex-1">
                  <h4 className="truncate text-base font-semibold text-slate-900 dark:text-slate-100">
                    {company.business_name || 'Empresa'}
                  </h4>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    RUT: {company.rut || 'N/A'}
                  </p>
                </div>
              </div>

              {/* Company Details */}
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                    Razón Social
                  </label>
                  <input
                    type="text"
                    value={company.business_name || ''}
                    disabled
                    className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-100"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                    RUT
                  </label>
                  <input
                    type="text"
                    value={company.rut || ''}
                    disabled
                    className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-100"
                  />
                </div>

                {company.trade_name && (
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                      Nombre de Fantasía
                    </label>
                    <input
                      type="text"
                      value={company.trade_name}
                      disabled
                      className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-100"
                    />
                  </div>
                )}
              </div>

              {/* SII Details button */}
              <ChateableWrapper
                message="Muéstrame la información detallada de mi empresa registrada en el SII, incluyendo socios, representantes, actividades económicas, direcciones, timbrajes y cumplimiento tributario"
                contextData={{
                  companyId: company.id,
                  companyRut: company.rut,
                  companyName: company.business_name,
                }}
                uiComponent="company_sii_details"
                entityId={company.id}
                entityType="company"
              >
                <button className="flex items-center gap-2 rounded-lg bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-700 transition-colors hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400 dark:hover:bg-emerald-900/50">
                  <FileText className="h-4 w-4" />
                  Ver Información Completa del SII
                </button>
              </ChateableWrapper>
            </div>
          </div>

          {/* Business Configuration */}
          <div>
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                  Configuración del Negocio
                </h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
                  Características operacionales de tu empresa
                </p>
              </div>
              {!isEditing ? (
                <button
                  onClick={() => setIsEditing(true)}
                  className="flex items-center gap-1.5 text-sm font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300"
                >
                  <Edit2 className="h-4 w-4" />
                  Editar
                </button>
              ) : null}
            </div>

            {settingsLoading ? (
              <div className="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
                Cargando configuración...
              </div>
            ) : editedSettings ? (
              <div className="space-y-3">
                {[
                  { key: 'has_formal_employees', label: 'Empleados con contrato formal' },
                  { key: 'has_imports', label: 'Realiza importaciones' },
                  { key: 'has_exports', label: 'Realiza exportaciones' },
                  { key: 'has_lease_contracts', label: 'Tiene contratos de arriendo' },
                ].map(({ key, label }) => (
                  <div
                    key={key}
                    className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3.5 dark:border-slate-700 dark:bg-slate-800/50"
                  >
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                      {label}
                    </span>
                    {isEditing ? (
                      <button
                        onClick={() => handleToggleSetting(key as any)}
                        className="transition-transform hover:scale-110"
                      >
                        {renderSettingIcon(editedSettings[key as keyof typeof editedSettings] as boolean | null)}
                      </button>
                    ) : (
                      renderSettingIcon(editedSettings[key as keyof typeof editedSettings] as boolean | null)
                    )}
                  </div>
                ))}

                {isEditing && (
                  <div className="flex gap-3 pt-2">
                    <button
                      onClick={handleSave}
                      disabled={isSaving}
                      className="flex-1 rounded-lg bg-emerald-600 py-2.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50 dark:bg-emerald-500 dark:hover:bg-emerald-600"
                    >
                      {isSaving ? 'Guardando...' : 'Guardar cambios'}
                    </button>
                    <button
                      onClick={handleCancel}
                      disabled={isSaving}
                      className="flex-1 rounded-lg border border-slate-200 bg-white py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                    >
                      Cancelar
                    </button>
                  </div>
                )}

                <div className="mt-3 rounded-lg bg-amber-50 p-3 dark:bg-amber-950/30">
                  <p className="text-xs text-amber-800 dark:text-amber-200">
                    Los datos de la empresa son obtenidos del SII y no pueden ser modificados desde aquí.
                  </p>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
                No hay configuración disponible
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="py-12 text-center">
          <Building2 className="mx-auto h-12 w-12 text-slate-400 mb-4" />
          <p className="text-sm text-slate-600 dark:text-slate-400">
            No hay información de empresa disponible
          </p>
        </div>
      )}
    </div>
  );
}
