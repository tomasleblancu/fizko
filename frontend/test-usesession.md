# useSession Testing Guide

## Manual Testing Checklist

### 1. Initial Load - New User (No Session)
- [ ] Open app in incognito/private window
- [ ] Should see loading spinner initially
- [ ] Should show onboarding modal after auth
- [ ] `needsOnboarding` should be `true`
- [ ] Console should log: `[useSession] Fetching sessions for user: <user-id>`

### 2. Onboarding Flow
- [ ] Fill in SII credentials (RUT + password)
- [ ] Click submit
- [ ] Console should log: `[useSession] Saving SII credentials...`
- [ ] On success, should log: `[useSession] SII credentials saved successfully`
- [ ] Onboarding modal should close
- [ ] Dashboard should appear
- [ ] `needsOnboarding` should become `false`

### 3. Existing User (Has Session)
- [ ] Refresh page
- [ ] Should load without showing onboarding
- [ ] Session data should be available immediately (from cache on subsequent loads)
- [ ] `needsOnboarding` should be `false`

### 4. Multiple Tabs (Deduplication Test)
- [ ] Open app in two tabs
- [ ] Both tabs should use same cached data
- [ ] Console should NOT show duplicate fetch logs
- [ ] Only one request should hit the backend

### 5. Error Handling
- [ ] Disconnect internet
- [ ] Refresh page
- [ ] Should show appropriate error state
- [ ] Should NOT crash the app
- [ ] `needsOnboarding` should be `true` (safe fallback)

### 6. Cache Behavior
- [ ] Load app
- [ ] Wait 6 minutes (beyond 5min staleTime)
- [ ] Focus window or navigate away and back
- [ ] Should trigger background refetch
- [ ] UI should remain responsive during refetch

### 7. Session Refresh
- [ ] Call `refresh()` function manually (via React DevTools)
- [ ] Should trigger immediate refetch
- [ ] Loading state should update briefly
- [ ] New data should appear

## React Query DevTools

Enable React Query DevTools to inspect:
1. Query state (loading, success, error, stale)
2. Cache contents
3. Query execution timeline
4. Mutation state

Look for:
- Query Key: `["sessions", "<user-id>"]`
- Status: Should be "success" for logged-in users
- Data: Should contain `session` and `needsOnboarding`

## Console Logs to Monitor

```
✅ Good logs:
[useSession] Fetching sessions for user: abc-123
[useSession] Saving SII credentials...
[useSession] SII credentials saved successfully: { ... }

❌ Bad logs (shouldn't appear):
[useSession] Skipping duplicate fetch for... (old implementation)
Multiple consecutive fetch logs (indicates deduplication not working)
```

## Network Tab

Check browser Network tab:
1. Should see `/sessions` request on first load
2. Should NOT see duplicate requests in quick succession
3. After cache expires (5min), should see background refetch
4. After saving credentials, should see `/sii/auth/login` POST

## Performance Check

Before vs After:
- Number of `/sessions` API calls should decrease
- Page load time should remain similar
- No memory leaks (check Memory tab after multiple refreshes)

## Rollback Procedure

If issues are found:

```bash
# Restore old implementation
cd frontend/src/shared/hooks
cp useSession.old.ts useSession.ts

# Rebuild
npm run build
```

## Debug Tips

### If queries don't execute:
1. Check that `enabled` condition is met
2. Verify `user` and `authSession` are available
3. Check React Query DevTools for query state

### If mutations fail:
1. Check console for error messages
2. Verify API endpoint is correct
3. Check network tab for actual request/response
4. Ensure `authSession.access_token` is valid

### If cache doesn't work:
1. Verify query keys are consistent
2. Check `staleTime` configuration
3. Look for manual `invalidateQueries` calls that might be too aggressive

---

**Test Status:** ⏳ Pending Manual Testing
**Last Updated:** 2025-10-31
