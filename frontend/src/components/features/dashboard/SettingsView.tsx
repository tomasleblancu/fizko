"use client";

import { User, Building2, Bell, Shield, Save, LogOut, Plus } from "lucide-react";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useProfile, useUpdateProfile } from "@/hooks/useProfile";
import { useCompanySettings, useUpdateCompanySettings } from "@/hooks/useCompanySettings";
import { useNotificationSubscriptions, useToggleSubscription } from "@/hooks/useNotificationSubscriptions";
import { useNotificationPreferences, useUpdateNotificationPreferences } from "@/hooks/useNotificationPreferences";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";

interface SettingsViewProps {
  userId?: string;
  companyId?: string;
  companyData?: {
    id: string;
    rut: string;
    business_name: string | null;
    trade_name?: string | null;
    tax_regime?: string | null;
    economic_activity?: string | null;
    address?: string | null;
    phone?: string | null;
    email?: string | null;
  };
  onLogout?: () => void;
}

type SettingsTab = 'profile' | 'company' | 'notifications';

export function SettingsView({ userId, companyId, companyData, onLogout }: SettingsViewProps) {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile');

  // Profile state
  const { data: profileData } = useProfile(userId || '');
  const updateProfile = useUpdateProfile(userId || '');
  const [profileForm, setProfileForm] = useState({
    name: '',
    lastname: '',
    phone: '',
  });

  // Company settings state
  const { data: settingsData } = useCompanySettings(companyId || '');
  const updateSettings = useUpdateCompanySettings(companyId || '');
  const [settingsForm, setSettingsForm] = useState({
    has_formal_employees: false,
    has_imports: false,
    has_exports: false,
    has_lease_contracts: false,
    has_bank_loans: false,
    business_description: '',
  });

  // Notification subscriptions
  const { data: subscriptionsData } = useNotificationSubscriptions(companyId || '');
  const toggleSubscription = useToggleSubscription(companyId || '');

  // Notification preferences
  const { data: preferencesData } = useNotificationPreferences(userId || '', companyId);
  const updatePreferences = useUpdateNotificationPreferences(userId || '');
  const [preferencesForm, setPreferencesForm] = useState({
    notifications_enabled: true,
    quiet_hours_start: '',
    quiet_hours_end: '',
    max_notifications_per_day: 20,
    min_interval_minutes: 30,
  });

  // Initialize forms when data loads
  useEffect(() => {
    if (profileData?.data) {
      setProfileForm({
        name: profileData.data.name || '',
        lastname: profileData.data.lastname || '',
        phone: profileData.data.phone || '',
      });
    }
  }, [profileData]);

  useEffect(() => {
    if (settingsData?.data) {
      setSettingsForm({
        has_formal_employees: settingsData.data.has_formal_employees || false,
        has_imports: settingsData.data.has_imports || false,
        has_exports: settingsData.data.has_exports || false,
        has_lease_contracts: settingsData.data.has_lease_contracts || false,
        has_bank_loans: settingsData.data.has_bank_loans || false,
        business_description: settingsData.data.business_description || '',
      });
    }
  }, [settingsData]);

  useEffect(() => {
    if (preferencesData?.data) {
      setPreferencesForm({
        notifications_enabled: preferencesData.data.notifications_enabled,
        quiet_hours_start: preferencesData.data.quiet_hours_start || '',
        quiet_hours_end: preferencesData.data.quiet_hours_end || '',
        max_notifications_per_day: preferencesData.data.max_notifications_per_day,
        min_interval_minutes: preferencesData.data.min_interval_minutes,
      });
    }
  }, [preferencesData]);

  const handleProfileSave = async () => {
    try {
      await updateProfile.mutateAsync(profileForm);
    } catch (error) {
      console.error('Error updating profile:', error);
    }
  };

  const handleSettingsSave = async () => {
    try {
      await updateSettings.mutateAsync(settingsForm);
    } catch (error) {
      console.error('Error updating settings:', error);
    }
  };

  const handlePreferencesSave = async () => {
    try {
      await updatePreferences.mutateAsync({
        ...preferencesForm,
        company_id: companyId || undefined,
      });
    } catch (error) {
      console.error('Error updating preferences:', error);
    }
  };

  const handleToggleSubscription = async (subscriptionId: string, isEnabled: boolean) => {
    try {
      await toggleSubscription.mutateAsync({ subscriptionId, isEnabled });
    } catch (error) {
      console.error('Error toggling subscription:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
          Configuración
        </h2>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Administra tu cuenta y preferencias
        </p>
      </div>

      {/* Tabs Navigation */}
      <div className="border-b border-slate-200 dark:border-slate-700">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab('profile')}
            className={`flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === 'profile'
                ? 'border-emerald-600 text-emerald-600 dark:border-emerald-400 dark:text-emerald-400'
                : 'border-transparent text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'
            }`}
          >
            <User className="h-4 w-4" />
            Perfil
          </button>
          <button
            onClick={() => setActiveTab('company')}
            className={`flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === 'company'
                ? 'border-emerald-600 text-emerald-600 dark:border-emerald-400 dark:text-emerald-400'
                : 'border-transparent text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'
            }`}
          >
            <Building2 className="h-4 w-4" />
            Empresa
          </button>
          <button
            onClick={() => setActiveTab('notifications')}
            className={`flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === 'notifications'
                ? 'border-emerald-600 text-emerald-600 dark:border-emerald-400 dark:text-emerald-400'
                : 'border-transparent text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'
            }`}
          >
            <Bell className="h-4 w-4" />
            Notificaciones
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'profile' && (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* User Profile */}
          <div className="rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
            <div className="mb-4 flex items-center gap-3">
              <div className="rounded-lg bg-emerald-100 p-2 dark:bg-emerald-900/20">
                <User className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                Información Personal
              </h3>
            </div>
            <div className="space-y-4">
              <div>
                <Label htmlFor="name">Nombre</Label>
                <Input
                  id="name"
                  value={profileForm.name}
                  onChange={(e) => setProfileForm({ ...profileForm, name: e.target.value })}
                  placeholder="Juan"
                />
              </div>
              <div>
                <Label htmlFor="lastname">Apellido</Label>
                <Input
                  id="lastname"
                  value={profileForm.lastname}
                  onChange={(e) => setProfileForm({ ...profileForm, lastname: e.target.value })}
                  placeholder="Contador"
                />
              </div>
              <div>
                <Label htmlFor="phone">Teléfono</Label>
                <Input
                  id="phone"
                  value={profileForm.phone}
                  onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                  placeholder="+56912345678"
                />
                {profileData?.data && !profileData.data.phone_verified && profileForm.phone && (
                  <p className="mt-1 text-xs text-yellow-600 dark:text-yellow-400">
                    Teléfono no verificado
                  </p>
                )}
              </div>
              <div>
                <Label>Email</Label>
                <p className="text-sm text-slate-700 dark:text-slate-300">
                  {profileData?.data?.email || '-'}
                </p>
              </div>
              <Button
                onClick={handleProfileSave}
                disabled={updateProfile.isPending}
                className="w-full"
              >
                <Save className="mr-2 h-4 w-4" />
                {updateProfile.isPending ? 'Guardando...' : 'Guardar Perfil'}
              </Button>
            </div>
          </div>

          {/* Security Section */}
          <div className="rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
            <div className="mb-4 flex items-center gap-3">
              <div className="rounded-lg bg-red-100 p-2 dark:bg-red-900/20">
                <Shield className="h-5 w-5 text-red-600 dark:text-red-400" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                Seguridad
              </h3>
            </div>
            <div className="space-y-4">
              <div>
                <Label>Contraseña</Label>
                <p className="text-sm text-slate-700 dark:text-slate-300">
                  ••••••••
                </p>
                <button
                  className="mt-2 w-full rounded-lg bg-slate-100 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                  onClick={() => {
                    // TODO: Implement password change
                    console.log('Change password');
                  }}
                >
                  Cambiar Contraseña
                </button>
              </div>

              {onLogout && (
                <div className="border-t border-slate-200 pt-4 dark:border-slate-700">
                  <button
                    onClick={onLogout}
                    className="flex w-full items-center justify-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
                  >
                    <LogOut className="h-4 w-4" />
                    Cerrar Sesión
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'company' && (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Company Information */}
          <div className="rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
            <div className="mb-4 flex items-center gap-3">
              <div className="rounded-lg bg-blue-100 p-2 dark:bg-blue-900/20">
                <Building2 className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                Datos de la Empresa
              </h3>
            </div>
            <div className="space-y-4">
              <div>
                <Label>RUT</Label>
                <p className="text-sm font-medium text-slate-900 dark:text-white">
                  {companyData?.rut || '-'}
                </p>
              </div>
              <div>
                <Label>Razón Social</Label>
                <p className="text-sm font-medium text-slate-900 dark:text-white">
                  {companyData?.business_name || '-'}
                </p>
              </div>
              <div>
                <Label>Nombre de Fantasía</Label>
                <p className="text-sm font-medium text-slate-900 dark:text-white">
                  {companyData?.trade_name || '-'}
                </p>
              </div>
              <div>
                <Label>Régimen Tributario</Label>
                <p className="text-sm font-medium text-slate-900 dark:text-white">
                  {companyData?.tax_regime || '-'}
                </p>
              </div>
              <div>
                <Label>Actividad Económica</Label>
                <p className="text-sm font-medium text-slate-900 dark:text-white">
                  {companyData?.economic_activity || '-'}
                </p>
              </div>
              <div>
                <Label>Dirección</Label>
                <p className="text-sm text-slate-700 dark:text-slate-300">
                  {companyData?.address || '-'}
                </p>
              </div>
              <div>
                <Label>Teléfono</Label>
                <p className="text-sm text-slate-700 dark:text-slate-300">
                  {companyData?.phone || '-'}
                </p>
              </div>
              <div>
                <Label>Email</Label>
                <p className="text-sm text-slate-700 dark:text-slate-300">
                  {companyData?.email || '-'}
                </p>
              </div>

              {/* Add New Company Button */}
              <div className="border-t border-slate-200 pt-4 dark:border-slate-700">
                <Button
                  onClick={() => router.push('/onboarding/sii')}
                  variant="outline"
                  className="w-full"
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Agregar Nueva Empresa
                </Button>
              </div>
            </div>
          </div>

          {/* Company Settings */}
          <div className="rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
            <div className="mb-4 flex items-center gap-3">
              <div className="rounded-lg bg-purple-100 p-2 dark:bg-purple-900/20">
                <Shield className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                Configuración del Negocio
              </h3>
            </div>
            <div className="space-y-4">
              <div className="space-y-3">
                <label className="flex items-center gap-2">
                  <Checkbox
                    checked={settingsForm.has_formal_employees}
                    onCheckedChange={(checked) =>
                      setSettingsForm({ ...settingsForm, has_formal_employees: !!checked })
                    }
                  />
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    Tiene empleados con contrato formal
                  </span>
                </label>
                <label className="flex items-center gap-2">
                  <Checkbox
                    checked={settingsForm.has_imports}
                    onCheckedChange={(checked) =>
                      setSettingsForm({ ...settingsForm, has_imports: !!checked })
                    }
                  />
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    Realiza importaciones
                  </span>
                </label>
                <label className="flex items-center gap-2">
                  <Checkbox
                    checked={settingsForm.has_exports}
                    onCheckedChange={(checked) =>
                      setSettingsForm({ ...settingsForm, has_exports: !!checked })
                    }
                  />
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    Realiza exportaciones
                  </span>
                </label>
                <label className="flex items-center gap-2">
                  <Checkbox
                    checked={settingsForm.has_lease_contracts}
                    onCheckedChange={(checked) =>
                      setSettingsForm({ ...settingsForm, has_lease_contracts: !!checked })
                    }
                  />
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    Tiene contratos de arriendo
                  </span>
                </label>
                <label className="flex items-center gap-2">
                  <Checkbox
                    checked={settingsForm.has_bank_loans}
                    onCheckedChange={(checked) =>
                      setSettingsForm({ ...settingsForm, has_bank_loans: !!checked })
                    }
                  />
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    Tiene créditos bancarios
                  </span>
                </label>
              </div>
              <div>
                <Label htmlFor="business_description">Descripción del negocio</Label>
                <textarea
                  id="business_description"
                  value={settingsForm.business_description}
                  onChange={(e) =>
                    setSettingsForm({ ...settingsForm, business_description: e.target.value })
                  }
                  className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-slate-600 dark:bg-slate-800 dark:text-white dark:placeholder-slate-500"
                  placeholder="Breve descripción de tu actividad comercial"
                  rows={3}
                />
              </div>
              <Button
                onClick={handleSettingsSave}
                disabled={updateSettings.isPending}
                className="w-full"
              >
                <Save className="mr-2 h-4 w-4" />
                {updateSettings.isPending ? 'Guardando...' : 'Guardar Configuración'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'notifications' && (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Notification Subscriptions */}
          <div className="rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
            <div className="mb-4 flex items-center gap-3">
              <div className="rounded-lg bg-yellow-100 p-2 dark:bg-yellow-900/20">
                <Bell className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                Notificaciones por Tipo
              </h3>
            </div>
            <div className="space-y-3">
              {subscriptionsData?.data && subscriptionsData.data.length > 0 ? (
                subscriptionsData.data.map((subscription) => (
                  <label key={subscription.id} className="flex items-center justify-between">
                    <div className="flex-1">
                      <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                        {subscription.template.name}
                      </span>
                      {subscription.template.description && (
                        <p className="text-xs text-slate-500 dark:text-slate-400">
                          {subscription.template.description}
                        </p>
                      )}
                    </div>
                    <Checkbox
                      checked={subscription.is_enabled}
                      onCheckedChange={(checked) =>
                        handleToggleSubscription(subscription.id, !!checked)
                      }
                    />
                  </label>
                ))
              ) : (
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  No hay notificaciones configuradas
                </p>
              )}
            </div>
          </div>

          {/* Notification Preferences */}
          <div className="rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
            <div className="mb-4 flex items-center gap-3">
              <div className="rounded-lg bg-purple-100 p-2 dark:bg-purple-900/20">
                <Shield className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                Preferencias de Notificación
              </h3>
            </div>
            <div className="space-y-4">
              <label className="flex items-center gap-2">
                <Checkbox
                  checked={preferencesForm.notifications_enabled}
                  onCheckedChange={(checked) =>
                    setPreferencesForm({ ...preferencesForm, notifications_enabled: !!checked })
                  }
                />
                <span className="text-sm text-slate-700 dark:text-slate-300">
                  Recibir notificaciones
                </span>
              </label>

              <div className="space-y-2">
                <Label className="text-xs">Horario silencioso</Label>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Input
                      type="time"
                      value={preferencesForm.quiet_hours_start}
                      onChange={(e) =>
                        setPreferencesForm({ ...preferencesForm, quiet_hours_start: e.target.value })
                      }
                      placeholder="Desde"
                    />
                  </div>
                  <div>
                    <Input
                      type="time"
                      value={preferencesForm.quiet_hours_end}
                      onChange={(e) =>
                        setPreferencesForm({ ...preferencesForm, quiet_hours_end: e.target.value })
                      }
                      placeholder="Hasta"
                    />
                  </div>
                </div>
              </div>

              <div>
                <Label htmlFor="max_notifications">Máximo de notificaciones por día</Label>
                <Input
                  id="max_notifications"
                  type="number"
                  min="1"
                  max="100"
                  value={preferencesForm.max_notifications_per_day}
                  onChange={(e) =>
                    setPreferencesForm({
                      ...preferencesForm,
                      max_notifications_per_day: parseInt(e.target.value, 10) || 20,
                    })
                  }
                />
              </div>

              <div>
                <Label htmlFor="min_interval">Intervalo mínimo entre notificaciones (minutos)</Label>
                <Input
                  id="min_interval"
                  type="number"
                  min="1"
                  max="1440"
                  value={preferencesForm.min_interval_minutes}
                  onChange={(e) =>
                    setPreferencesForm({
                      ...preferencesForm,
                      min_interval_minutes: parseInt(e.target.value, 10) || 30,
                    })
                  }
                />
              </div>

              <Button
                onClick={handlePreferencesSave}
                disabled={updatePreferences.isPending}
                className="w-full"
              >
                <Save className="mr-2 h-4 w-4" />
                {updatePreferences.isPending ? 'Guardando...' : 'Guardar Preferencias'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
