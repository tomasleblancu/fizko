/**
 * Centralized query keys factory for React Query
 * Following the pattern from the Vite frontend
 */

export const queryKeys = {
  sessions: {
    all: ['sessions'] as const,
    byUser: (userId: string) => [...queryKeys.sessions.all, 'user', userId] as const,
    active: (userId: string) => [...queryKeys.sessions.byUser(userId), 'active'] as const,
  },
  companies: {
    all: ['companies'] as const,
    byId: (id: string) => [...queryKeys.companies.all, id] as const,
  },
  documents: {
    all: ['documents'] as const,
    byCompany: (companyId: string) => [...queryKeys.documents.all, 'company', companyId] as const,
    sales: (companyId: string) => [...queryKeys.documents.byCompany(companyId), 'sales'] as const,
    purchases: (companyId: string) => [...queryKeys.documents.byCompany(companyId), 'purchases'] as const,
  },
  taxSummary: {
    all: ['taxSummary'] as const,
    byCompany: (companyId: string, period?: string) =>
      period
        ? [...queryKeys.taxSummary.all, 'company', companyId, 'period', period] as const
        : [...queryKeys.taxSummary.all, 'company', companyId] as const,
  },
  calendar: {
    all: ['calendar'] as const,
    upcoming: (companyId: string, daysAhead?: number) =>
      daysAhead
        ? [...queryKeys.calendar.all, 'upcoming', companyId, 'days', daysAhead] as const
        : [...queryKeys.calendar.all, 'upcoming', companyId] as const,
  },
  contacts: {
    all: ['contacts'] as const,
    byCompany: (companyId: string, contactType?: string) =>
      contactType
        ? [...queryKeys.contacts.all, 'company', companyId, 'type', contactType] as const
        : [...queryKeys.contacts.all, 'company', companyId] as const,
  },
  personnel: {
    all: ['personnel'] as const,
    byCompany: (companyId: string, status?: string, search?: string, page?: number) =>
      [...queryKeys.personnel.all, 'company', companyId, { status, search, page }] as const,
  },
  f29: {
    all: ['f29'] as const,
    byCompany: (companyId: string, year?: number, month?: number) =>
      [...queryKeys.f29.all, 'company', companyId, { year, month }] as const,
  },
  f29SIIDownloads: {
    all: ['f29SIIDownloads'] as const,
    byCompany: (companyId: string, year?: number, month?: number) =>
      [...queryKeys.f29SIIDownloads.all, 'company', companyId, { year, month }] as const,
  },
  profile: {
    all: ['profile'] as const,
    byUser: (userId: string) => [...queryKeys.profile.all, userId] as const,
  },
  companySettings: {
    all: ['companySettings'] as const,
    byCompany: (companyId: string) => [...queryKeys.companySettings.all, companyId] as const,
  },
  notificationSubscriptions: {
    all: ['notificationSubscriptions'] as const,
    byCompany: (companyId: string) => [...queryKeys.notificationSubscriptions.all, companyId] as const,
  },
  notificationPreferences: {
    all: ['notificationPreferences'] as const,
    byUser: (userId: string, companyId?: string) =>
      companyId
        ? [...queryKeys.notificationPreferences.all, userId, companyId] as const
        : [...queryKeys.notificationPreferences.all, userId] as const,
  },
} as const;
