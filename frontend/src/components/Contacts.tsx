import { useState } from 'react';
import clsx from 'clsx';
import { Building2, Phone, Mail, MapPin, User, Users, Sun, Moon, Home, Settings } from 'lucide-react';
import { ChateableWrapper } from './ChateableWrapper';
import { useContacts, type Contact } from '../hooks/useContacts';
import type { ColorScheme } from '../hooks/useColorScheme';
import type { Company } from '../types/fizko';

interface ContactsProps {
  scheme: ColorScheme;
  isInDrawer?: boolean;
  onNavigateBack?: () => void;
  company: Company | null;
  onThemeChange?: (scheme: ColorScheme) => void;
  onNavigateToDashboard?: () => void;
  onNavigateToSettings?: () => void;
  currentView?: 'dashboard' | 'contacts' | 'settings';
}

export function Contacts({ scheme, isInDrawer = false, onNavigateBack, company, onThemeChange, onNavigateToDashboard, onNavigateToSettings, currentView = 'contacts' }: ContactsProps) {
  const { contacts, loading, error } = useContacts(company?.id);
  const [filter, setFilter] = useState<'all' | 'provider' | 'client' | 'both'>('all');
  const [searchTerm, setSearchTerm] = useState('');

  const toggleTheme = () => {
    if (onThemeChange) {
      onThemeChange(scheme === 'dark' ? 'light' : 'dark');
    }
  };

  const filteredContacts = contacts.filter(contact => {
    const matchesFilter = filter === 'all' || contact.contact_type === filter || contact.contact_type === 'both';
    const matchesSearch = searchTerm === '' ||
      contact.business_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      contact.rut.includes(searchTerm) ||
      (contact.trade_name?.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesFilter && matchesSearch;
  });

  const getContactTypeLabel = (type: string) => {
    switch (type) {
      case 'provider': return 'Proveedor';
      case 'client': return 'Cliente';
      case 'both': return 'Proveedor y Cliente';
      default: return type;
    }
  };

  const getContactTypeBadge = (type: string) => {
    const baseClasses = "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium";
    switch (type) {
      case 'provider':
        return `${baseClasses} bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400`;
      case 'client':
        return `${baseClasses} bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400`;
      case 'both':
        return `${baseClasses} bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400`;
      default:
        return `${baseClasses} bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400`;
    }
  };

  return (
    <section className="flex h-full w-full flex-col overflow-hidden">
      {/* Header */}
      {!isInDrawer && (
        <div className="flex-shrink-0 border-b border-slate-200/70 bg-white/50 px-6 py-3 backdrop-blur dark:border-slate-800/70 dark:bg-slate-900/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-md">
                <Users className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                  Contactos
                </h2>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  Gestiona tus proveedores y clientes
                </p>
              </div>
            </div>

            {/* Controls - Right side */}
            <div className="flex items-center gap-3">
              {/* Theme Toggle */}
              {onThemeChange && (
                <button
                  onClick={toggleTheme}
                  className={clsx(
                    'rounded-lg p-2 transition-colors',
                    'hover:bg-slate-100 dark:hover:bg-slate-800',
                    'text-slate-600 dark:text-slate-300'
                  )}
                  aria-label="Toggle theme"
                  title="Cambiar tema"
                >
                  {scheme === 'dark' ? (
                    <Sun className="h-5 w-5" />
                  ) : (
                    <Moon className="h-5 w-5" />
                  )}
                </button>
              )}

              {/* Navigation Pills */}
              <div className="flex items-center gap-1 rounded-lg bg-slate-100 p-1 dark:bg-slate-800">
                {/* Dashboard Button */}
                {onNavigateToDashboard && (
                  <button
                    onClick={onNavigateToDashboard}
                    className={clsx(
                      'rounded-md p-2 transition-colors',
                      currentView === 'dashboard'
                        ? 'bg-white text-emerald-600 shadow-sm dark:bg-slate-900 dark:text-emerald-400'
                        : 'text-slate-600 hover:bg-slate-200/50 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-700/50 dark:hover:text-slate-100'
                    )}
                    aria-label="Dashboard"
                    title="Dashboard"
                  >
                    <Home className="h-5 w-5" />
                  </button>
                )}

                {/* Contacts Button */}
                <button
                  onClick={() => {}} // Already on contacts
                  disabled
                  className={clsx(
                    'rounded-md p-2 transition-colors cursor-default',
                    currentView === 'contacts'
                      ? 'bg-white text-emerald-600 shadow-sm dark:bg-slate-900 dark:text-emerald-400'
                      : 'text-slate-400 dark:text-slate-600'
                  )}
                  aria-label="Contactos"
                  title="Contactos"
                >
                  <Users className="h-5 w-5" />
                </button>

                {/* Settings Button */}
                {onNavigateToSettings && (
                  <button
                    onClick={onNavigateToSettings}
                    className={clsx(
                      'rounded-md p-2 transition-colors',
                      currentView === 'settings'
                        ? 'bg-white text-emerald-600 shadow-sm dark:bg-slate-900 dark:text-emerald-400'
                        : 'text-slate-600 hover:bg-slate-200/50 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-700/50 dark:hover:text-slate-100'
                    )}
                    aria-label="Configuración"
                    title="Configuración"
                  >
                    <Settings className="h-5 w-5" />
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters and Search */}
      <div className="flex-shrink-0 border-b border-slate-200/60 bg-white/30 px-6 py-4 dark:border-slate-800/60 dark:bg-slate-900/30">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <input
              type="text"
              placeholder="Buscar por nombre o RUT..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className={clsx(
                "w-full rounded-lg border px-4 py-2 pl-10 text-sm transition-colors",
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
              { value: 'provider' as const, label: 'Proveedores' },
              { value: 'client' as const, label: 'Clientes' },
              { value: 'both' as const, label: 'Ambos' },
            ].map((filterOption) => (
              <button
                key={filterOption.value}
                onClick={() => setFilter(filterOption.value)}
                className={clsx(
                  "rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
                  filter === filterOption.value
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

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2">
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
              >
                {/* Title skeleton */}
                <div className="h-5 w-3/4 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />

                {/* Subtitle skeleton */}
                <div className="mt-2 h-3 w-1/2 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />

                {/* Info rows skeleton */}
                <div className="mt-3 space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <div className="h-4 w-32 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
                    <div className="h-5 w-20 animate-pulse rounded-full bg-slate-200 dark:bg-slate-700" />
                  </div>
                  <div className="h-4 w-48 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
                  <div className="h-4 w-36 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
                </div>
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          </div>
        ) : filteredContacts.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <Users className="mx-auto h-12 w-12 text-slate-300 dark:text-slate-700" />
              <p className="mt-4 text-sm text-slate-600 dark:text-slate-400">
                {searchTerm || filter !== 'all' ? 'No se encontraron contactos' : 'Aún no hay contactos'}
              </p>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-500">
                Los contactos se crean automáticamente al sincronizar documentos
              </p>
            </div>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {filteredContacts.map((contact) => (
              <ChateableWrapper
                key={contact.id}
                message={`Dame información sobre mi contacto ${contact.business_name} (RUT: ${contact.rut})`}
                contextData={{
                  contactId: contact.id,
                  contactName: contact.business_name,
                  contactRut: contact.rut,
                  contactType: contact.contact_type,
                }}
                uiComponent="contact_card"
              >
                <div
                  className={clsx(
                    "rounded-lg border p-4 transition-all text-left w-full cursor-pointer",
                    "border-slate-200 bg-white hover:border-emerald-500 hover:shadow-md",
                    "dark:border-slate-800 dark:bg-slate-900 dark:hover:border-emerald-500"
                  )}
                >
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-slate-900 dark:text-slate-100 truncate">
                      {contact.business_name}
                    </h3>
                    {contact.trade_name && (
                      <p className="text-xs text-slate-500 dark:text-slate-500 truncate">
                        {contact.trade_name}
                      </p>
                    )}
                  </div>

                  <div className="mt-3 space-y-2 text-sm">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                        <Building2 className="h-4 w-4 flex-shrink-0" />
                        <span className="truncate">{contact.rut}</span>
                      </div>
                      <span className={getContactTypeBadge(contact.contact_type)}>
                        {getContactTypeLabel(contact.contact_type)}
                      </span>
                    </div>

                    {contact.email && (
                      <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                        <Mail className="h-4 w-4 flex-shrink-0" />
                        <span className="truncate">{contact.email}</span>
                      </div>
                    )}

                    {contact.phone && (
                      <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                        <Phone className="h-4 w-4 flex-shrink-0" />
                        <span className="truncate">{contact.phone}</span>
                      </div>
                    )}

                    {contact.address && (
                      <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                        <MapPin className="h-4 w-4 flex-shrink-0" />
                        <span className="truncate">{contact.address}</span>
                      </div>
                    )}
                  </div>
                </div>
              </ChateableWrapper>
            ))}
          </div>
        )}
      </div>

      {/* Footer with count */}
      {!loading && !error && filteredContacts.length > 0 && (
        <div className="flex-shrink-0 border-t border-slate-200/60 bg-white/30 px-6 py-3 dark:border-slate-800/60 dark:bg-slate-900/30">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Mostrando {filteredContacts.length} {filteredContacts.length === 1 ? 'contacto' : 'contactos'}
            {filter !== 'all' && ` (${getContactTypeLabel(filter).toLowerCase()})`}
          </p>
        </div>
      )}
    </section>
  );
}
