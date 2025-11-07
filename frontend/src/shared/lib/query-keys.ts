/**
 * Centralized Query Keys Factory
 *
 * This file provides type-safe, consistent query keys for React Query.
 * Using a factory pattern ensures:
 * - No typos in query keys
 * - Easy refactoring
 * - Precise cache invalidation
 * - Better IDE autocomplete
 *
 * @example
 * ```typescript
 * // In a hook
 * useQuery({
 *   queryKey: queryKeys.sessions.byUser(userId),
 *   queryFn: fetchSessions
 * });
 *
 * // Invalidating cache
 * queryClient.invalidateQueries({
 *   queryKey: queryKeys.sessions.byUser(userId)
 * });
 * ```
 */

export const queryKeys = {
  // Sessions
  sessions: {
    all: ['sessions'] as const,
    byUser: (userId: string | undefined) =>
      userId ? [...queryKeys.sessions.all, userId] as const : queryKeys.sessions.all,
  },

  // Company
  company: {
    all: ['home', 'company'] as const,
    byId: (id: string) => [...queryKeys.company.all, id] as const,
    byUser: (userId: string | undefined) =>
      userId ? [...queryKeys.company.all, 'user', userId] as const : queryKeys.company.all,
  },

  // Tax Summary
  taxSummary: {
    all: ['home', 'tax-summary'] as const,
    byCompany: (companyId: string) => [...queryKeys.taxSummary.all, companyId] as const,
    byPeriod: (companyId: string | null, period?: string) =>
      companyId
        ? [...queryKeys.taxSummary.byCompany(companyId), period] as const
        : queryKeys.taxSummary.all,
  },

  // Payroll
  payroll: {
    all: ['home', 'payroll'] as const,
    byCompany: (companyId: string) => [...queryKeys.payroll.all, companyId] as const,
    byPeriod: (companyId: string | null, period?: string) =>
      companyId
        ? [...queryKeys.payroll.byCompany(companyId), period] as const
        : queryKeys.payroll.all,
  },

  // Calendar
  calendar: {
    all: ['admin', 'calendar-events'] as const,
    byCompany: (companyId: string) => [...queryKeys.calendar.all, companyId] as const,
    filtered: (companyId: string, status?: string, startDate?: string, endDate?: string) =>
      [...queryKeys.calendar.byCompany(companyId), status, startDate, endDate] as const,
  },

  // Contacts
  contacts: {
    all: ['home', 'contacts'] as const,
    byCompany: (companyId: string) => [...queryKeys.contacts.all, companyId] as const,
  },

  // Tax Documents
  taxDocuments: {
    all: ['home', 'tax-documents'] as const,
    byCompany: (companyId: string) => [...queryKeys.taxDocuments.all, companyId] as const,
    paginated: (companyId: string, limit: number) =>
      [...queryKeys.taxDocuments.byCompany(companyId), limit] as const,
  },

  // People/Personnel
  people: {
    all: ['home', 'people'] as const,
    byCompany: (companyId: string) => [...queryKeys.people.all, companyId] as const,
  },

  // Calendar Query (different from calendar events)
  calendarQuery: {
    all: ['home', 'calendar'] as const,
    byCompany: (companyId: string, days: number, includeCompleted: boolean) =>
      [...queryKeys.calendarQuery.all, companyId, days, includeCompleted] as const,
  },

  // User Profile
  userProfile: {
    all: ['user-profile'] as const,
    byUser: (userId: string | undefined) =>
      userId ? [...queryKeys.userProfile.all, userId] as const : queryKeys.userProfile.all,
  },

  // Company Settings
  companySettings: {
    all: ['company-settings'] as const,
    byId: (companyId: string) => [...queryKeys.companySettings.all, companyId] as const,
  },

  // Subscription
  subscription: {
    all: ['subscription'] as const,
    current: ['subscription', 'current'] as const,
    plans: ['subscription', 'plans'] as const,
  },
} as const;
