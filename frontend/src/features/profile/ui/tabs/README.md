# Profile Settings Tabs

This directory contains modular components for the different tabs in the Profile Settings page.

## Structure

Each tab component is a self-contained module that handles its own state, UI, and business logic.

### Current Components

- **AccountSettings.tsx** - User account information, phone verification, email, and logout functionality
  - Manages user profile data (name, lastname, phone)
  - Phone number verification via WhatsApp
  - SII credentials information
  - Logout functionality

### Planned Components (To Be Extracted)

The following components should be extracted from `ProfileSettings.tsx` following the same pattern as `AccountSettings`:

- **CompanySettings.tsx** - Company information and business configuration
  - Company details (business name, RUT, trade name)
  - Business configuration toggles (employees, imports, exports, leases)
  - SII detailed information integration

- **PreferencesSettings.tsx** - User preferences and notification settings
  - Theme/appearance preferences
  - Notification preferences integration

- **DangerZoneSettings.tsx** - Dangerous actions like account deletion
  - Account deletion with confirmation
  - Warning banners for irreversible actions

## Component Props Pattern

All tab components should follow this interface pattern:

```typescript
interface TabSettingsProps {
  user?: any;                    // User data from auth
  scheme: ColorScheme;           // Theme scheme
  company?: Company | null;      // Company data (if needed)
  isInDrawer?: boolean;          // Whether rendered in drawer or full page
  // Add other specific props as needed
}
```

## Usage Example

```typescript
import { AccountSettings } from './tabs/AccountSettings';

// In parent component
<AccountSettings
  user={user}
  scheme={scheme}
  profileLoading={profileLoading}
  profile={profile}
  isInDrawer={isInDrawer}
/>
```

## Benefits of Modularization

1. **Separation of Concerns** - Each tab has its own file and logic
2. **Easier Maintenance** - Changes to one tab don't affect others
3. **Better Code Organization** - Clear structure following Feature-Sliced Design
4. **Improved Testability** - Each component can be tested independently
5. **Reduced File Size** - Main ProfileSettings.tsx is much smaller and more manageable

## Next Steps

1. Extract remaining components from ProfileSettings.tsx
2. Ensure all imports are updated
3. Add unit tests for each tab component
4. Consider extracting shared UI components if patterns emerge
