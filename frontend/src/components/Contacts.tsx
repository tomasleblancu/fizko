import { useState, useCallback } from 'react';
import clsx from 'clsx';
import { Building2, Phone, Mail, MapPin, User, Users } from 'lucide-react';
import { ChateableWrapper } from './ChateableWrapper';
import { useContacts, type Contact } from '../hooks/useContacts';
import { ViewContainer } from './layout/ViewContainer';
import { FizkoLogo } from './FizkoLogo';
import type { ViewType } from './layout/NavigationPills';
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
  currentView?: ViewType;
}

export function Contacts({ scheme, isInDrawer = false, onNavigateBack, company, onThemeChange, onNavigateToDashboard, onNavigateToSettings, currentView = 'contacts' }: ContactsProps) {
  const { contacts, loading, error } = useContacts(company?.id);
  const [filter, setFilter] = useState<'all' | 'provider' | 'client' | 'both'>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Handle navigation
  const handleNavigate = useCallback((view: ViewType) => {
    if (view === 'dashboard' && onNavigateToDashboard) onNavigateToDashboard();
    if (view === 'settings' && onNavigateToSettings) onNavigateToSettings();
  }, [onNavigateToDashboard, onNavigateToSettings]);

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

  // Content component (shared between drawer and normal mode)
  const renderContent = () => (
    <>
      {/* Filters and Search */}
      <div className="flex-shrink-0 border-b border-slate-200/60 bg-white/30 py-4 dark:border-slate-800/60 dark:bg-slate-900/30">
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
      <div className="flex-1 py-4 sm:py-6">
        {loading ? (
          <div className="grid w-full gap-3 sm:gap-4 md:grid-cols-2 auto-rows-fr">
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-4"
              >
                {/* Header with title and badge - stacked on mobile */}
                <div className="mb-2">
                  <div className="flex flex-col gap-1.5 sm:flex-row sm:items-start sm:justify-between sm:gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="h-4 w-3/4 animate-pulse rounded bg-slate-200 dark:bg-slate-700 sm:h-5" />
                      <div className="mt-1 h-3 w-1/2 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
                    </div>
                    <div className="h-5 w-24 animate-pulse rounded-full bg-slate-200 dark:bg-slate-700 flex-shrink-0" />
                  </div>
                </div>

                {/* Info rows skeleton */}
                <div className="space-y-1.5">
                  <div className="h-3 w-32 animate-pulse rounded bg-slate-200 dark:bg-slate-700 sm:h-4" />
                  <div className="h-3 w-48 animate-pulse rounded bg-slate-200 dark:bg-slate-700 sm:h-4" />
                  <div className="h-3 w-36 animate-pulse rounded bg-slate-200 dark:bg-slate-700 sm:h-4" />
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
          <div className="grid w-full gap-3 sm:gap-4 md:grid-cols-2 auto-rows-fr">
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
                    "rounded-lg border p-3 transition-all text-left w-full max-w-full cursor-pointer shadow-sm overflow-hidden min-w-0",
                    "border-slate-200 bg-white hover:border-emerald-500 hover:shadow-md",
                    "dark:border-slate-800 dark:bg-slate-900 dark:hover:border-emerald-500",
                    "sm:p-4"
                  )}
                >
                  {/* Header - stacked on mobile, side by side on sm+ */}
                  <div className="mb-2">
                    <div className="flex flex-col gap-1.5 sm:flex-row sm:items-start sm:justify-between sm:gap-2">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-slate-900 dark:text-slate-100 truncate text-sm sm:text-base">
                          {contact.business_name}
                        </h3>
                        {contact.trade_name && (
                          <p className="text-xs text-slate-500 dark:text-slate-500 truncate mt-0.5">
                            {contact.trade_name}
                          </p>
                        )}
                      </div>
                      <span className={clsx(getContactTypeBadge(contact.contact_type), "flex-shrink-0 self-start")}>
                        {getContactTypeLabel(contact.contact_type)}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-1.5 text-xs sm:text-sm">
                    <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400 min-w-0">
                      <Building2 className="h-3.5 w-3.5 sm:h-4 sm:w-4 flex-shrink-0" />
                      <span className="truncate">{contact.rut}</span>
                    </div>

                    {contact.email && (
                      <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400 min-w-0">
                        <Mail className="h-3.5 w-3.5 sm:h-4 sm:w-4 flex-shrink-0" />
                        <span className="truncate">{contact.email}</span>
                      </div>
                    )}

                    {contact.phone && (
                      <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400 min-w-0">
                        <Phone className="h-3.5 w-3.5 sm:h-4 sm:w-4 flex-shrink-0" />
                        <span className="truncate">{contact.phone}</span>
                      </div>
                    )}

                    {contact.address && (
                      <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400 min-w-0">
                        <MapPin className="h-3.5 w-3.5 sm:h-4 sm:w-4 flex-shrink-0" />
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
        <div className="flex-shrink-0 border-t border-slate-200/60 bg-white/30 py-3 dark:border-slate-800/60 dark:bg-slate-900/30">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Mostrando {filteredContacts.length} {filteredContacts.length === 1 ? 'contacto' : 'contactos'}
            {filter !== 'all' && ` (${getContactTypeLabel(filter).toLowerCase()})`}
          </p>
        </div>
      )}
    </>
  );

  // Drawer mode - simple container with padding
  if (isInDrawer) {
    return (
      <div className="flex h-full flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto px-4 sm:px-6">
          {renderContent()}
        </div>
      </div>
    );
  }

  // Normal mode - with ViewContainer
  return (
    <ViewContainer
      icon={<FizkoLogo className="h-7 w-7" />}
      iconGradient="from-white to-white"
      title="Contactos"
      subtitle="Gestiona tus proveedores y clientes"
      currentView={currentView}
      onNavigate={handleNavigate}
      scheme={scheme}
      onThemeChange={onThemeChange}
      isInDrawer={false}
      contentClassName="flex-1 overflow-y-auto flex flex-col px-4 sm:px-6"
    >
      {renderContent()}
    </ViewContainer>
  );
}
