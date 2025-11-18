import { Building2, Phone, Mail, MapPin, MessageCircle, ArrowLeft } from 'lucide-react';
import clsx from 'clsx';
import type { Contact } from "@/shared/hooks/useContactsQuery";
import { useTaxDocumentsQuery } from "@/shared/hooks/useTaxDocumentsQuery";
import { RecentDocumentsCard } from '@/features/dashboard/ui/RecentDocumentsCard';
import { ChateableWrapper } from '@/shared/ui/ChateableWrapper';
import type { ColorScheme } from "@/shared/hooks/useColorScheme";

interface ContactDetailProps {
  contact: Contact;
  onBack: () => void;
  scheme: ColorScheme;
  companyId?: string | null;
}

export function ContactDetail({ contact, onBack, scheme, companyId }: ContactDetailProps) {
  // Fetch documents for this specific contact using the RUT filter
  const { data: documents = [], isLoading: docsLoading } = useTaxDocumentsQuery(
    100, // Fetch up to 100 documents for this contact
    undefined, // No period filter
    contact.rut, // Filter by contact RUT
    true // enabled
  );

  const getContactTypeLabel = (type: string) => {
    switch (type) {
      case 'provider': return 'Proveedor';
      case 'client': return 'Cliente';
      case 'both': return 'Proveedor y Cliente';
      default: return type;
    }
  };

  const getContactTypeBadge = (type: string) => {
    const baseClasses = "inline-flex items-center gap-1 rounded-full px-3 py-1 text-sm font-medium";
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
    <div className="flex h-full flex-col overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-slate-200/60 bg-white/30 pb-4 pt-4 dark:border-slate-800/60 dark:bg-slate-900/30">
        {/* Contact Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-2">
              <button
                onClick={onBack}
                className="flex h-10 w-10 items-center justify-center rounded-full text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
                aria-label="Volver a contactos"
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-lg">
                <Building2 className="h-6 w-6" />
              </div>
              <div className="flex-1 min-w-0">
                <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 truncate">
                  {contact.business_name}
                </h2>
                {contact.trade_name && (
                  <p className="text-sm text-slate-500 dark:text-slate-500 truncate">
                    {contact.trade_name}
                  </p>
                )}
              </div>
              <ChateableWrapper
                message={`Dame información sobre mi contacto ${contact.business_name} (RUT: ${contact.rut})`}
                contextData={{
                  contactId: contact.id,
                  contactName: contact.business_name,
                  contactRut: contact.rut,
                  contactType: contact.contact_type,
                }}
                uiComponent="contact_card"
                entityId={contact.rut}
                entityType="contact"
              >
                <button
                  className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-emerald-700 flex-shrink-0"
                >
                  <MessageCircle className="h-4 w-4" />
                  Consultar
                </button>
              </ChateableWrapper>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <span className="font-mono text-slate-700 dark:text-slate-300">
                RUT: {contact.rut}
              </span>
              <span className={getContactTypeBadge(contact.contact_type)}>
                {getContactTypeLabel(contact.contact_type)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Contact Information */}
      {(contact.email || contact.phone || contact.address) && (
        <div className="flex-shrink-0 border-b border-slate-200/60 bg-white/30 py-4 dark:border-slate-800/60 dark:bg-slate-900/30">
          <h3 className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-300">
            Información de Contacto
          </h3>
          <div className="space-y-2">
            {contact.email && (
              <div className="flex items-center gap-2 text-sm">
                <Mail className="h-4 w-4 text-slate-400" />
                <a
                  href={`mailto:${contact.email}`}
                  className="text-slate-600 hover:text-emerald-600 dark:text-slate-400 dark:hover:text-emerald-400"
                >
                  {contact.email}
                </a>
              </div>
            )}
            {contact.phone && (
              <div className="flex items-center gap-2 text-sm">
                <Phone className="h-4 w-4 text-slate-400" />
                <a
                  href={`tel:${contact.phone}`}
                  className="text-slate-600 hover:text-emerald-600 dark:text-slate-400 dark:hover:text-emerald-400"
                >
                  {contact.phone}
                </a>
              </div>
            )}
            {contact.address && (
              <div className="flex items-start gap-2 text-sm">
                <MapPin className="h-4 w-4 text-slate-400 mt-0.5" />
                <span className="text-slate-600 dark:text-slate-400">
                  {contact.address}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Documents Section */}
      <div className="flex-1 flex flex-col min-h-0 py-4">
        <h3 className="mb-4 text-sm font-semibold text-slate-700 dark:text-slate-300 flex-shrink-0">
          Documentos Asociados
        </h3>
        <div className="flex-1 overflow-y-auto pb-4">
          <RecentDocumentsCard
            documents={documents}
            loading={docsLoading}
            scheme={scheme}
            isExpanded={true}
            isInDrawer={false}
          />
        </div>
      </div>
    </div>
  );
}
