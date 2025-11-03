# useSession Migration - React Query Optimization

## 📊 Overview

This document describes the migration of `useSession` hook from a custom implementation to React Query, resulting in significant code simplification and improved maintainability.

## 🎯 Goals

1. Reduce code complexity and lines of code
2. Improve consistency with other data hooks
3. Leverage React Query's built-in features (caching, retry, deduplication)
4. Eliminate manual state management
5. Improve type safety with centralized query keys

## 📉 Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Lines of Code | 177 | 80 | **-55%** |
| useState hooks | 5 | 0 | **-100%** |
| useEffect hooks | 1 | 0 | **-100%** |
| useRef hooks | 1 | 0 | **-100%** |
| Manual cache logic | Yes | No | Removed |
| Duplicate request prevention | Manual | Automatic | Simplified |

## 🔄 Changes

### Before (Custom Implementation)

```typescript
export function useSession() {
  const [session, setSession] = useState<SIISession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [needsOnboarding, setNeedsOnboarding] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const lastFetchKeyRef = useRef<string>('');

  const fetchSession = useCallback(async (force: boolean = false) => {
    // Manual deduplication logic
    const fetchKey = `${user.id}-${authSession.access_token.slice(0, 10)}`;
    if (lastFetchKeyRef.current === fetchKey && !force) {
      return; // Skip duplicate
    }

    // Manual state management
    setLoading(true);
    setError(null);
    // ... 50+ lines of manual fetch logic
  }, [user, authSession]);

  useEffect(() => {
    fetchSession();
  }, [fetchSession]);

  // 177 total lines
}
```

### After (React Query)

```typescript
export function useSession() {
  const { user, session: authSession } = useAuth();
  const queryClient = useQueryClient();

  // Query handles all state automatically
  const sessionsQuery = useQuery({
    queryKey: queryKeys.sessions.byUser(user?.id),
    queryFn: async () => {
      // Simplified fetch logic
      const response = await apiFetch(`${API_BASE_URL}/sessions`, {
        headers: { 'Authorization': `Bearer ${authSession.access_token}` }
      });
      // Transform and return data
      return transformSessionData(response);
    },
    enabled: !!user && !!authSession?.access_token,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  // Mutation for saving credentials
  const saveMutation = useMutation({
    mutationFn: async (credentials) => {
      // API call
    },
    onSuccess: () => {
      // Automatic cache invalidation
      queryClient.invalidateQueries({
        queryKey: queryKeys.sessions.byUser(user?.id)
      });
    },
  });

  return {
    session: sessionsQuery.data?.session ?? null,
    loading: sessionsQuery.isLoading,
    error: sessionsQuery.error?.message ?? null,
    needsOnboarding: sessionsQuery.data?.needsOnboarding ?? false,
    isInitialized: !sessionsQuery.isLoading,
    saveSIICredentials: saveMutation.mutateAsync,
    refresh: () => sessionsQuery.refetch(),
  };
}

// 80 total lines
```

## ✨ Benefits

### 1. **Automatic Deduplication**
- **Before:** Manual tracking with `useRef` and custom logic
- **After:** React Query automatically deduplicates requests with the same query key

### 2. **Built-in Caching**
- **Before:** No caching - every component mount triggered a new fetch
- **After:** 5-minute cache with automatic stale data management

### 3. **Simplified State Management**
- **Before:** 5 useState, 1 useEffect, 1 useRef, manual synchronization
- **After:** React Query manages all state internally

### 4. **Consistent Error Handling**
- **Before:** Custom error handling with manual state updates
- **After:** Consistent with all other hooks, automatic retry logic

### 5. **Type-Safe Query Keys**
- **Before:** String literals scattered across code
- **After:** Centralized `queryKeys` factory with TypeScript support

```typescript
// Centralized query keys
export const queryKeys = {
  sessions: {
    all: ['sessions'] as const,
    byUser: (userId: string | undefined) =>
      userId ? [...queryKeys.sessions.all, userId] as const : queryKeys.sessions.all,
  },
  // ... other keys
}
```

### 6. **Automatic Cache Invalidation**
- **Before:** Manual state updates after mutations
- **After:** Declarative invalidation with React Query

```typescript
// After saving credentials
onSuccess: () => {
  queryClient.invalidateQueries({
    queryKey: queryKeys.sessions.byUser(user?.id)
  });
}
```

## 🔍 API Compatibility

The new implementation maintains 100% API compatibility:

```typescript
// Usage remains identical
const {
  session,           // SIISession | null
  loading,           // boolean
  error,             // string | null
  needsOnboarding,   // boolean
  isInitialized,     // boolean
  saveSIICredentials, // (credentials) => Promise<any>
  refresh,           // () => Promise<void>
} = useSession();
```

## 📁 Files Changed

1. **Created:**
   - `frontend/src/shared/lib/query-keys.ts` - Centralized query key factory
   - `frontend/src/shared/hooks/useSession.old.ts` - Backup of old implementation

2. **Modified:**
   - `frontend/src/shared/hooks/useSession.ts` - New React Query implementation

3. **Unchanged:**
   - `frontend/src/features/dashboard/ui/Home.tsx` - Uses same API

## 🧪 Testing Checklist

- [x] Build compiles successfully (`npm run build`)
- [ ] Login flow works correctly
- [ ] Onboarding modal appears for new users
- [ ] SII credentials save successfully
- [ ] Session persists across page refreshes
- [ ] Multiple tabs don't trigger duplicate fetches
- [ ] Error states display correctly
- [ ] Loading states work as expected

## 🚀 Deployment Notes

1. The migration is **backward compatible** - no breaking changes
2. Query key structure is designed for future extensibility
3. Old implementation backed up as `useSession.old.ts`
4. Can roll back by restoring from backup if needed

## 📚 Next Steps

After confirming this migration works well, consider:

1. **Apply pattern to other hooks:**
   - Consider if any other hooks have complex manual state management
   - Apply query keys factory to existing hooks for consistency

2. **Enable StrictMode:**
   - Now safe to re-enable since React Query handles double-fetching

3. **Add prefetching:**
   - Prefetch session data on auth success for instant load

4. **Monitor performance:**
   - Check bundle size impact (should be minimal)
   - Verify cache hit rates in development

## 🔗 References

- [React Query Documentation](https://tanstack.com/query/latest)
- [Query Keys Guide](https://tanstack.com/query/latest/docs/react/guides/query-keys)
- [Mutations Guide](https://tanstack.com/query/latest/docs/react/guides/mutations)

---

**Migration Date:** 2025-10-31
**Migrated By:** Claude Code
**Reviewed By:** _Pending_
