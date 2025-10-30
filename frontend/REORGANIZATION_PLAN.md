# 📦 Frontend Reorganization Plan

## 🎯 Objetivo

Reorganizar el frontend de Fizko para mejorar:
- ✅ **Legibilidad**: Encontrar componentes fácilmente
- ✅ **Escalabilidad**: Agregar features sin crear caos
- ✅ **Mantenibilidad**: Modificar sin romper otras partes
- ✅ **DX (Developer Experience)**: Imports claros y concisos

---

## 📊 Análisis de Estructura Actual

### Problemas Identificados

1. **Components dispersos** (43 archivos en `/components` sin organización)
   - Mezcla de features, UI, layout, business logic
   - Difícil encontrar componentes relacionados
   - No hay separación clara de responsabilidades

2. **Pages planas** (10 archivos en `/pages` sin subdirectorios)
   - No agrupa páginas por dominio (admin, tax, payroll)
   - Nombres largos con prefijos (`AdminCompaniesView`, `AdminTaskManager`)

3. **No hay separación entre UI y Features**
   - UI components (buttons, cards) mezclados con business components
   - Difícil reutilizar componentes

4. **Estructura actual:**
```
src/
├── components/          # ❌ 39 archivos sin organización
│   ├── admin/          # ✅ Bien (task-manager)
│   └── layout/         # ✅ Bien
├── pages/              # ❌ 10 archivos planos
├── hooks/
├── contexts/
├── lib/
└── types/
```

---

## 🏗️ Nueva Estructura Propuesta

### Arquitectura: **Feature-Based** + **Shared**

```
src/
├── features/                    # ⭐ Feature modules (domain-driven)
│   ├── admin/                  # Admin panel features
│   │   ├── companies/
│   │   │   ├── components/
│   │   │   │   ├── CompanyCard.tsx
│   │   │   │   ├── CompanyForm.tsx
│   │   │   │   └── CompanyFilters.tsx
│   │   │   ├── pages/
│   │   │   │   ├── CompaniesListPage.tsx
│   │   │   │   └── CompanyDetailPage.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useAdminCompanies.ts
│   │   │   │   └── useAdminCompany.ts
│   │   │   ├── api/
│   │   │   │   └── companiesApi.ts
│   │   │   └── types/
│   │   │       └── company.types.ts
│   │   ├── tasks/              # Task Manager
│   │   │   ├── components/
│   │   │   │   ├── ScheduledTasksTab.tsx
│   │   │   │   ├── TaskQueueTab.tsx
│   │   │   │   ├── TaskHistoryTab.tsx
│   │   │   │   └── CreateTaskDialog.tsx
│   │   │   ├── pages/
│   │   │   │   └── TaskManagerPage.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useScheduledTasks.ts
│   │   │   │   ├── useTaskQueue.ts
│   │   │   │   └── useTaskHistory.ts
│   │   │   └── types/
│   │   │       └── task.types.ts
│   │   ├── calendar/
│   │   │   ├── components/
│   │   │   │   └── EventTypeForm.tsx
│   │   │   └── pages/
│   │   │       └── EventTypesPage.tsx
│   │   └── notifications/
│   │       ├── components/
│   │       └── pages/
│   │           └── NotificationTemplatesPage.tsx
│   ├── tax/                    # Tax documents & forms
│   │   ├── documents/
│   │   │   ├── components/
│   │   │   │   ├── DocumentsPreview.tsx
│   │   │   │   ├── RecentDocumentsCard.tsx
│   │   │   │   ├── DocumentFilters.tsx
│   │   │   │   └── DocumentTable.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useTaxDocuments.ts
│   │   │   │   └── useSyncDocuments.ts
│   │   │   └── types/
│   │   │       └── document.types.ts
│   │   ├── form29/
│   │   │   ├── components/
│   │   │   │   ├── F29List.tsx
│   │   │   │   ├── F29Form.tsx
│   │   │   │   └── F29Card.tsx
│   │   │   └── hooks/
│   │   │       └── useForm29.ts
│   │   ├── summary/
│   │   │   ├── components/
│   │   │   │   ├── TaxSummaryCard.tsx
│   │   │   │   ├── TaxSummaryCardSkeleton.tsx
│   │   │   │   └── TaxCalendar.tsx
│   │   │   └── hooks/
│   │   │       └── useTaxSummary.ts
│   │   └── sii/
│   │       ├── components/
│   │       │   └── SyncPanel.tsx
│   │       └── hooks/
│   │           └── useSIISync.ts
│   ├── payroll/               # Personnel & payroll
│   │   ├── people/
│   │   │   ├── components/
│   │   │   │   ├── PeopleList.tsx
│   │   │   │   ├── PersonCard.tsx
│   │   │   │   └── PersonForm.tsx
│   │   │   ├── hooks/
│   │   │   │   └── usePeople.ts
│   │   │   └── types/
│   │   │       └── person.types.ts
│   │   └── summary/
│   │       ├── components/
│   │       │   ├── PayrollSummaryCard.tsx
│   │       │   └── PayrollChart.tsx
│   │       └── hooks/
│   │           └── usePayrollSummary.ts
│   ├── calendar/              # Calendar & events
│   │   ├── components/
│   │   │   ├── CalendarConfig.tsx
│   │   │   ├── CalendarEventsSection.tsx
│   │   │   └── EventCard.tsx
│   │   ├── hooks/
│   │   │   ├── useCalendar.ts
│   │   │   └── useEvents.ts
│   │   └── types/
│   │       └── event.types.ts
│   ├── chat/                  # Chat & contacts
│   │   ├── components/
│   │   │   ├── ChatKitPanel.tsx
│   │   │   ├── ChateableWrapper.tsx
│   │   │   ├── Contacts.tsx
│   │   │   └── ContactsDrawer.tsx
│   │   ├── hooks/
│   │   │   ├── useChat.ts
│   │   │   └── useContacts.ts
│   │   └── types/
│   │       └── chat.types.ts
│   ├── dashboard/             # Main dashboard
│   │   ├── components/
│   │   │   ├── DashboardPreview.tsx
│   │   │   ├── FinancialDashboard.tsx
│   │   │   ├── FinancialDashboardDrawer.tsx
│   │   │   ├── Home.tsx
│   │   │   ├── PeriodCarousel.tsx
│   │   │   └── PeriodSelector.tsx
│   │   ├── hooks/
│   │   │   └── useDashboard.ts
│   │   └── types/
│   │       └── dashboard.types.ts
│   ├── profile/               # User profile & settings
│   │   ├── components/
│   │   │   ├── ProfileSettings.tsx
│   │   │   ├── ProfileSettingsDrawer.tsx
│   │   │   ├── ProfileSettingsSkeleton.tsx
│   │   │   └── CompanyInfoCard.tsx
│   │   ├── hooks/
│   │   │   └── useProfile.ts
│   │   └── types/
│   │       └── profile.types.ts
│   └── auth/                  # Authentication
│       ├── components/
│       │   ├── LoginOverlay.tsx
│       │   └── OnboardingModal.tsx
│       ├── hooks/
│       │   └── useAuth.ts (move from contexts)
│       └── types/
│           └── auth.types.ts
│
├── pages/                     # ⭐ Route pages (thin wrappers)
│   ├── index.tsx             # / - Landing
│   ├── admin/
│   │   ├── index.tsx         # /admin - Companies list
│   │   ├── companies/
│   │   │   └── [id].tsx      # /admin/companies/:id
│   │   ├── tasks/
│   │   │   └── index.tsx     # /admin/tasks
│   │   ├── calendar/
│   │   │   └── index.tsx     # /admin/calendar
│   │   └── notifications/
│   │       └── index.tsx     # /admin/notifications
│   ├── dashboard/
│   │   └── index.tsx         # /dashboard
│   ├── tax/
│   │   ├── documents/
│   │   │   └── index.tsx     # /tax/documents
│   │   └── form29/
│   │       └── index.tsx     # /tax/form29
│   ├── payroll/
│   │   ├── people/
│   │   │   └── index.tsx     # /payroll/people
│   │   └── summary/
│   │       └── index.tsx     # /payroll/summary
│   ├── profile/
│   │   └── index.tsx         # /profile
│   ├── legal/
│   │   ├── terms.tsx         # /legal/terms
│   │   └── privacy.tsx       # /legal/privacy
│   └── _app.tsx              # Root wrapper
│
├── shared/                    # ⭐ Shared/Common code
│   ├── components/           # Reusable components
│   │   ├── ui/              # UI primitives (shadcn/ui)
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── input.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── tabs.tsx
│   │   │   └── ...
│   │   ├── layout/          # Layout components
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── PageLayout.tsx
│   │   ├── feedback/        # Feedback components
│   │   │   ├── ErrorOverlay.tsx
│   │   │   ├── LoadingSkeleton.tsx
│   │   │   └── EmptyState.tsx
│   │   └── common/          # Other common components
│   │       ├── FizkoLogo.tsx
│   │       ├── SearchBar.tsx
│   │       └── DatePicker.tsx
│   ├── hooks/               # Shared hooks
│   │   ├── useDebounce.ts
│   │   ├── useLocalStorage.ts
│   │   └── useMediaQuery.ts
│   ├── utils/               # Utility functions
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── dates.ts
│   ├── api/                 # API client
│   │   ├── client.ts
│   │   └── endpoints.ts
│   ├── types/               # Global types
│   │   ├── api.types.ts
│   │   └── common.types.ts
│   └── constants/           # App constants
│       ├── routes.ts
│       └── config.ts
│
├── contexts/                 # React contexts (keep as is, or move to shared)
│   ├── AuthContext.tsx
│   └── DashboardCacheContext.tsx
│
├── lib/                      # External lib configs (keep as is)
│   ├── config.ts
│   └── api-client.ts
│
└── styles/                   # Global styles
    └── globals.css
```

---

## 📋 Migration Strategy

### Phase 1: Create New Structure (No Breaking Changes)

1. **Create directories:**
```bash
mkdir -p src/{features,pages,shared}/{admin,tax,payroll,calendar,chat,dashboard,profile,auth}
mkdir -p src/shared/{components/{ui,layout,feedback,common},hooks,utils,api,types,constants}
```

2. **Move shared UI components first** (safe, no dependencies):
   - Create `src/shared/components/ui/` for shadcn components
   - Move layout components to `src/shared/components/layout/`
   - Move feedback components to `src/shared/components/feedback/`

3. **Create feature modules one by one** (isolated):
   - Start with **admin/tasks** (already partially organized)
   - Then **admin/companies**
   - Then **tax/documents**
   - Then **payroll/people**
   - etc.

### Phase 2: Update Imports (Gradual)

For each feature moved:
1. Update imports in that feature
2. Update imports in pages
3. Update imports in other features (if any)
4. Test that feature works
5. Commit

### Phase 3: Update Routing (Final Step)

1. Reorganize `pages/` to match feature structure
2. Update `main.tsx` with new routes
3. Test all routes work
4. Delete old files

### Phase 4: Cleanup

1. Remove old `/components` directory
2. Remove old flat `/pages` files
3. Update documentation
4. Update import aliases in `tsconfig.json`

---

## 🎯 Benefits of New Structure

### 1. **Feature Isolation**
```typescript
// Old (hard to find related code)
import { ScheduledTasksTab } from '../../components/admin/task-manager/ScheduledTasksTab';
import { useAdminTasks } from '../../hooks/useAdminTasks'; // Where is this??
import { Task } from '../../types/admin'; // Mixed types

// New (everything in one place)
import { ScheduledTasksTab } from '@/features/admin/tasks/components/ScheduledTasksTab';
import { useScheduledTasks } from '@/features/admin/tasks/hooks/useScheduledTasks';
import type { Task } from '@/features/admin/tasks/types/task.types';
```

### 2. **Clear Responsibilities**
- **Features**: Business logic, domain-specific components
- **Shared**: Reusable, generic components/utils
- **Pages**: Route definitions only (thin wrappers)

### 3. **Easy Navigation**
```
Want to work on task manager?
→ Go to /features/admin/tasks/
→ Everything is there: components, hooks, types, api

Want to add a new button?
→ Go to /shared/components/ui/
→ Or use existing from shadcn

Want to add a new admin feature?
→ Create /features/admin/my-feature/
→ Follow the same structure
```

### 4. **Better Imports with Aliases**

Update `tsconfig.json`:
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"],
      "@/features/*": ["./src/features/*"],
      "@/shared/*": ["./src/shared/*"],
      "@/pages/*": ["./src/pages/*"],
      "@/lib/*": ["./src/lib/*"]
    }
  }
}
```

Then:
```typescript
// Instead of
import { Button } from '../../../components/ui/button';
import { useAuth } from '../../../contexts/AuthContext';

// Use
import { Button } from '@/shared/components/ui/button';
import { useAuth } from '@/features/auth/hooks/useAuth';
```

### 5. **Scalability**

Adding a new feature? Just create:
```
/features/my-new-feature/
├── components/
├── pages/
├── hooks/
├── api/
└── types/
```

No need to touch existing structure!

---

## 🚀 Quick Start (Step-by-Step)

### Step 1: Move Admin Task Manager (Example)

```bash
# Create structure
mkdir -p src/features/admin/tasks/{components,pages,hooks,types}

# Move files
mv src/components/admin/task-manager/* src/features/admin/tasks/components/
mv src/pages/AdminTaskManager.tsx src/features/admin/tasks/pages/TaskManagerPage.tsx

# Update imports in TaskManagerPage.tsx
# From: import ScheduledTasksTab from '../components/admin/task-manager/ScheduledTasksTab';
# To:   import { ScheduledTasksTab } from '../components/ScheduledTasksTab';

# Create index exports
cat > src/features/admin/tasks/index.ts << 'EOF'
export { default as TaskManagerPage } from './pages/TaskManagerPage';
export * from './components/ScheduledTasksTab';
export * from './components/TaskQueueTab';
export * from './components/TaskHistoryTab';
EOF

# Update route in main.tsx
# From: import AdminTaskManager from "./pages/AdminTaskManager";
# To:   import { TaskManagerPage } from "@/features/admin/tasks";
```

### Step 2: Create Shared UI Components

```bash
# Move shadcn components
mkdir -p src/shared/components/ui
# (Copy your existing ui components or generate with shadcn CLI)

# Move layout
mkdir -p src/shared/components/layout
mv src/components/layout/* src/shared/components/layout/

# Move feedback
mkdir -p src/shared/components/feedback
mv src/components/ErrorOverlay.tsx src/shared/components/feedback/
mv src/components/*Skeleton.tsx src/shared/components/feedback/
```

### Step 3: Repeat for Each Feature

Tax Documents:
```bash
mkdir -p src/features/tax/documents/{components,hooks,types}
mv src/components/DocumentsPreview.tsx src/features/tax/documents/components/
mv src/components/RecentDocumentsCard.tsx src/features/tax/documents/components/
# ... etc
```

---

## 📝 Example: Complete Feature Module

```
src/features/admin/tasks/
├── index.ts                          # Public API
├── components/
│   ├── ScheduledTasksTab.tsx        # Main tab component
│   ├── TaskQueueTab.tsx             # Queue monitoring
│   ├── TaskHistoryTab.tsx           # History view
│   ├── CreateTaskDialog.tsx         # Modal form
│   ├── TaskCard.tsx                 # Reusable card
│   └── index.ts                     # Component exports
├── pages/
│   ├── TaskManagerPage.tsx          # Main page wrapper
│   └── index.ts
├── hooks/
│   ├── useScheduledTasks.ts         # Query hook
│   ├── useCreateTask.ts             # Mutation hook
│   ├── useDeleteTask.ts             # Mutation hook
│   └── index.ts
├── api/
│   ├── tasksApi.ts                  # API calls
│   └── index.ts
├── types/
│   ├── task.types.ts                # TypeScript types
│   └── index.ts
└── README.md                         # Feature documentation
```

**index.ts** (Public API):
```typescript
// Pages
export { default as TaskManagerPage } from './pages/TaskManagerPage';

// Components (public only)
export { ScheduledTasksTab } from './components/ScheduledTasksTab';
export { TaskQueueTab } from './components/TaskQueueTab';
export { TaskHistoryTab } from './components/TaskHistoryTab';

// Hooks (if needed by other features)
export { useScheduledTasks } from './hooks/useScheduledTasks';

// Types
export type * from './types/task.types';
```

---

## ✅ Checklist for Implementation

- [ ] Create directory structure
- [ ] Move shared UI components
- [ ] Move layout components
- [ ] Migrate admin features
  - [ ] admin/tasks
  - [ ] admin/companies
  - [ ] admin/calendar
  - [ ] admin/notifications
- [ ] Migrate tax features
  - [ ] tax/documents
  - [ ] tax/form29
  - [ ] tax/summary
  - [ ] tax/sii
- [ ] Migrate payroll features
  - [ ] payroll/people
  - [ ] payroll/summary
- [ ] Migrate other features
  - [ ] calendar
  - [ ] chat
  - [ ] dashboard
  - [ ] profile
  - [ ] auth
- [ ] Update routing (pages/)
- [ ] Update imports (tsconfig paths)
- [ ] Test all features work
- [ ] Delete old directories
- [ ] Update documentation
- [ ] Create feature READMEs

---

## 🎓 Best Practices

1. **Keep features independent**: Avoid cross-feature imports (use shared instead)
2. **Use barrel exports**: Export public API from index.ts
3. **Co-locate related code**: Keep components, hooks, types together
4. **Small, focused files**: One component per file
5. **Consistent naming**: `useFeatureName.ts`, `FeatureCard.tsx`
6. **Document features**: Add README.md in each feature
7. **Test in isolation**: Each feature should be testable independently

---

**Next Steps**:
1. Review and approve structure
2. Start with admin/tasks migration (already partially done)
3. Gradually migrate other features
4. Update documentation as we go

¿Te parece bien esta propuesta? ¿Quieres que empiece con la migración del Task Manager como ejemplo?
