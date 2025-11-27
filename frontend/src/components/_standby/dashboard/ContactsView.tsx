"use client";

import { Search, Users, Building2, UserCircle, ArrowLeft, ArrowUpRight, ArrowDownLeft, Calendar } from "lucide-react";
import React, { useState, useMemo } from "react";
import { useContacts } from "@/hooks/useContacts";
import { useCompanyDocuments } from "@/hooks/useCompanyDocuments";
import { ChateableWrapper } from "@/components/ui/ChateableWrapper";
import { parseLocalDate, getTimestamp } from "@/shared/lib/date-utils";
import type { Contact } from "@/types/contacts";
import type { DocumentWithType } from "@/types/database";

interface ContactsViewProps {
  companyId?: string;
}

export function ContactsView({ companyId }: ContactsViewProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);

  // Fetch contacts
  const { data: contacts, isLoading } = useContacts({
    companyId: companyId || '',
  });

  // Fetch all documents for contact detail view
  const { data: documents } = useCompanyDocuments({
    companyId: companyId || '',
    limit: 500,
  });

  // Filter contacts based on search term
  const filteredContacts = useMemo(() => {
    if (!contacts) return [];

    return contacts.filter((contact) =>
      contact.business_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (contact.trade_name && contact.trade_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      contact.rut.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (contact.email && contact.email.toLowerCase().includes(searchTerm.toLowerCase()))
    );
  }, [contacts, searchTerm]);

  // Calculate summary stats
  const stats = useMemo(() => {
    if (!contacts) return { total: 0, providers: 0, clients: 0 };

    return {
      total: contacts.length,
      providers: contacts.filter(c => c.contact_type === 'provider' || c.contact_type === 'both').length,
      clients: contacts.filter(c => c.contact_type === 'client' || c.contact_type === 'both').length,
    };
  }, [contacts]);

  // Filter documents by selected contact
  const contactDocuments = useMemo(() => {
    if (!selectedContact || !documents) return [];

    return documents.filter(doc =>
      doc.counterparty_rut === selectedContact.rut
    );
  }, [selectedContact, documents]);

  // Group contact documents by date
  const groupedContactDocuments = useMemo(() => {
    return contactDocuments.reduce((acc, doc) => {
      const dateKey = doc.issue_date;
      if (!acc[dateKey]) {
        acc[dateKey] = [];
      }
      acc[dateKey].push(doc);
      return acc;
    }, {} as Record<string, DocumentWithType[]>);
  }, [contactDocuments]);

  // Helper functions
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("es-CL", {
      style: "currency",
      currency: "CLP",
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    const date = parseLocalDate(dateString);
    return new Intl.DateTimeFormat("es-CL", {
      weekday: "long",
      day: "numeric",
      month: "long",
    }).format(date);
  };

  // If contact is selected, show detail view
  if (selectedContact) {
    return (
      <div className="space-y-6">
        {/* Back Button */}
        <button
          onClick={() => setSelectedContact(null)}
          className="flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          Volver a Contactos
        </button>

        {/* Contact Header */}
        <div className="rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                {selectedContact.business_name}
              </h2>
              {selectedContact.trade_name && (
                <p className="mt-1 text-slate-600 dark:text-slate-400">
                  {selectedContact.trade_name}
                </p>
              )}
            </div>
            <span className={`rounded-full px-3 py-1 text-sm font-medium ${
              selectedContact.contact_type === 'provider'
                ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400'
                : selectedContact.contact_type === 'client'
                ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-400'
                : 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400'
            }`}>
              {selectedContact.contact_type === 'provider' ? 'Proveedor' : selectedContact.contact_type === 'client' ? 'Cliente' : 'Cliente y Proveedor'}
            </span>
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400">RUT</p>
              <p className="mt-1 font-medium text-slate-900 dark:text-white">
                {selectedContact.rut}
              </p>
            </div>
            {selectedContact.email && (
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Email</p>
                <p className="mt-1 font-medium text-slate-900 dark:text-white">
                  {selectedContact.email}
                </p>
              </div>
            )}
            {selectedContact.phone && (
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Teléfono</p>
                <p className="mt-1 font-medium text-slate-900 dark:text-white">
                  {selectedContact.phone}
                </p>
              </div>
            )}
            {selectedContact.address && (
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Dirección</p>
                <p className="mt-1 font-medium text-slate-900 dark:text-white">
                  {selectedContact.address}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Documents Table */}
        <div className="rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
          <h3 className="mb-4 text-lg font-semibold text-slate-900 dark:text-white">
            Movimientos ({contactDocuments.length})
          </h3>

          {contactDocuments.length === 0 ? (
            <div className="py-12 text-center">
              <Building2 className="mx-auto h-12 w-12 text-slate-300 dark:text-slate-600" />
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                No hay movimientos con este contacto
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <tbody className="bg-white dark:bg-slate-900">
                  {Object.entries(groupedContactDocuments)
                    .sort(([dateA], [dateB]) => getTimestamp(dateB) - getTimestamp(dateA))
                    .map(([date, docs]) => (
                      <React.Fragment key={date}>
                        {/* Date Group Header Row */}
                        <tr className="sticky top-0 z-10 bg-slate-100 dark:bg-slate-800/80">
                          <td colSpan={5} className="px-4 py-2">
                            <div className="flex items-center gap-2">
                              <Calendar className="h-4 w-4 text-slate-500" />
                              <span className="text-sm font-semibold text-slate-900 dark:text-white">
                                {formatDate(date)}
                              </span>
                              <div className="h-px flex-1 bg-slate-300 dark:bg-slate-600" />
                              <span className="text-xs text-slate-500">{docs.length} docs</span>
                            </div>
                          </td>
                        </tr>
                        {/* Document Rows */}
                        {docs.map((doc) => (
                          <tr
                            key={doc.id}
                            className="border-b border-slate-200 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800/50"
                          >
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-2">
                                <div className={`flex h-7 w-7 items-center justify-center rounded-lg ${
                                  doc.type === 'sale'
                                    ? 'bg-emerald-100 dark:bg-emerald-900/30'
                                    : 'bg-blue-100 dark:bg-blue-900/30'
                                }`}>
                                  {doc.type === 'sale' ? (
                                    <ArrowUpRight className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                                  ) : (
                                    <ArrowDownLeft className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
                                  )}
                                </div>
                                <span className={`text-xs font-medium ${
                                  doc.type === 'sale'
                                    ? 'text-emerald-700 dark:text-emerald-400'
                                    : 'text-blue-700 dark:text-blue-400'
                                }`}>
                                  {doc.type === 'sale' ? 'Venta' : 'Compra'}
                                </span>
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <div className="text-sm text-slate-900 dark:text-white">
                                {doc.document_type}
                              </div>
                              {doc.folio && (
                                <div className="text-xs text-slate-500 dark:text-slate-400">
                                  N° {doc.folio}
                                </div>
                              )}
                            </td>
                            <td className="px-4 py-3 text-sm text-slate-900 dark:text-white">
                              <div className="max-w-xs truncate">
                                {doc.counterparty_name || 'Sin nombre'}
                              </div>
                            </td>
                            <td className="whitespace-nowrap px-4 py-3 text-right text-sm font-medium text-slate-900 dark:text-white">
                              {formatCurrency(doc.total_amount - doc.tax_amount)}
                            </td>
                            <td className={`whitespace-nowrap px-4 py-3 text-right text-sm font-bold ${
                              doc.type === 'sale'
                                ? 'text-emerald-600 dark:text-emerald-400'
                                : 'text-blue-600 dark:text-blue-400'
                            }`}>
                              {doc.type === 'sale' ? '+' : '-'}{formatCurrency(doc.total_amount)}
                            </td>
                          </tr>
                        ))}
                      </React.Fragment>
                    ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
            Contactos
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Gestiona tus clientes y proveedores
          </p>
        </div>
        <button className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700">
          Agregar Contacto
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
              Total Contactos
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
              Proveedores
            </p>
            <Building2 className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">
            {isLoading ? "-" : stats.providers}
          </p>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
              Clientes
            </p>
            <UserCircle className="h-5 w-5 text-purple-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">
            {isLoading ? "-" : stats.clients}
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          placeholder="Buscar por nombre, RUT o email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full rounded-lg border border-slate-200 bg-white py-2 pl-10 pr-4 text-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
        />
      </div>

      {/* Contacts Table */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent" />
        </div>
      ) : filteredContacts.length === 0 ? (
        <div className="rounded-lg border border-slate-200 bg-white p-12 text-center dark:border-slate-700 dark:bg-slate-900">
          <Building2 className="mx-auto h-12 w-12 text-slate-300 dark:text-slate-600" />
          <p className="mt-2 text-slate-600 dark:text-slate-400">
            {searchTerm ? "No se encontraron contactos" : "No hay contactos registrados"}
          </p>
        </div>
      ) : (
        <div className="rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
          {/* Mobile: Card-based layout */}
          <div className="divide-y divide-slate-100 lg:hidden dark:divide-slate-800">
            {filteredContacts.map((contact) => (
              <ChateableWrapper
                key={contact.id}
                as="fragment"
                message={`Muéstrame información detallada de mi contacto ${contact.business_name} (RUT: ${contact.rut})`}
                contextData={{
                  contactId: contact.id,
                  businessName: contact.business_name,
                  tradeName: contact.trade_name,
                  rut: contact.rut,
                  contactType: contact.contact_type,
                  email: contact.email,
                  phone: contact.phone,
                }}
                uiComponent="contact_card"
                entityId={contact.id}
                entityType="contact"
                onClick={() => setSelectedContact(contact)}
              >
                <div className="cursor-pointer p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-900 dark:text-white truncate">
                        {contact.business_name}
                      </p>
                      {contact.trade_name && (
                        <p className="text-sm text-slate-500 dark:text-slate-400 truncate">
                          {contact.trade_name}
                        </p>
                      )}
                    </div>
                    <span className={`ml-3 rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap ${
                      contact.contact_type === 'provider'
                        ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400'
                        : contact.contact_type === 'client'
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-400'
                        : 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400'
                    }`}>
                      {contact.contact_type === 'provider' ? 'Proveedor' : contact.contact_type === 'client' ? 'Cliente' : 'Ambos'}
                    </span>
                  </div>
                </div>
              </ChateableWrapper>
            ))}
          </div>

          {/* Desktop: Table layout */}
          <div className="hidden lg:block overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="px-6 py-4 text-left text-sm font-medium text-slate-600 dark:text-slate-400">
                    Razón Social
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-slate-600 dark:text-slate-400">
                    RUT
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-slate-600 dark:text-slate-400">
                    Tipo
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-slate-600 dark:text-slate-400">
                    Email
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-slate-600 dark:text-slate-400">
                    Teléfono
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredContacts.map((contact) => (
                  <ChateableWrapper
                    key={contact.id}
                    as="fragment"
                    message={`Muéstrame información detallada de mi contacto ${contact.business_name} (RUT: ${contact.rut})`}
                    contextData={{
                      contactId: contact.id,
                      businessName: contact.business_name,
                      tradeName: contact.trade_name,
                      rut: contact.rut,
                      contactType: contact.contact_type,
                      email: contact.email,
                      phone: contact.phone,
                    }}
                    uiComponent="contact_card"
                    entityId={contact.id}
                    entityType="contact"
                    onClick={() => setSelectedContact(contact)}
                  >
                    <tr className="cursor-pointer border-b border-slate-100 last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50">
                      <td className="px-6 py-4">
                        <div>
                          <p className="font-medium text-slate-900 dark:text-white">
                            {contact.business_name}
                          </p>
                          {contact.trade_name && (
                            <p className="text-sm text-slate-500 dark:text-slate-400">
                              {contact.trade_name}
                            </p>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-slate-600 dark:text-slate-400">
                        {contact.rut}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          contact.contact_type === 'provider'
                            ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400'
                            : contact.contact_type === 'client'
                            ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-400'
                            : 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400'
                        }`}>
                          {contact.contact_type === 'provider' ? 'Proveedor' : contact.contact_type === 'client' ? 'Cliente' : 'Ambos'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate-600 dark:text-slate-400">
                        {contact.email || '-'}
                      </td>
                      <td className="px-6 py-4 text-slate-600 dark:text-slate-400">
                        {contact.phone || '-'}
                      </td>
                    </tr>
                  </ChateableWrapper>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
