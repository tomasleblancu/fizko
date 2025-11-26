# Fizko Mobile App - Expo/React Native Conversion Prompt

## Overview

Fizko is a conversational tax and accounting assistant for small businesses in Chile. The app integrates an AI chat interface (powered by OpenAI ChatKit) with financial dashboards, allowing users to interact with their tax data through natural conversation.

## Core Architecture

### 1. App Layout & Navigation

**Desktop Layout (1024px+)**:
- Split view: 30% chat panel (left) + 70% content area (right)
- Floating tab icons appear when no content view is selected
- Header with company selector, notifications, and theme toggle

**Mobile Layout (< 1024px)**:
- Full-screen chat interface as the primary view
- Fixed bottom navigation bar with 5 tabs
- Slide-up drawer (80vh height) for content views
- Drawer supports swipe-to-dismiss gesture (150px threshold)

**Bottom Navigation Tabs**:
1. **Home/Dashboard** - Tax summaries and financial overview (emerald accent when active)
2. **Contacts** - Business contact management
3. **Personnel** - Employee/contractor management
4. **Forms** - Tax form submissions
5. **Settings** - User and company settings

### 2. ChatKit Integration Architecture

**Implementation Strategy**:
- Uses OpenAI ChatKit React library (`@openai/chatkit-react`)
- All ChatKit API calls proxied through backend: `/api/chatkit?company_id={companyId}`
- Custom fetch function injects JWT auth token and metadata
- Event-driven architecture for "chateable" elements

**ChatKit Configuration**:
```typescript
Theme:
- Color scheme: Synced with system (light/dark)
- Primary accent: Emerald (#10b981 in light, #f1f5f9 in dark)
- Font: Questrial (Google Font)
- Border radius: Round (circular buttons)

Start Screen:
- Greeting: "Fizko"
- Quick prompts (4 buttons):
  1. "Quiero agregar un gasto" (Add expense) - notebook-pencil icon
  2. "Dame un resumen de ventas" (Sales summary) - notebook icon
  3. "Agrega un nuevo colaborador" (Add employee) - user icon
  4. "Quiero darte feedback" (Feedback) - circle-question icon

Composer:
- Placeholder: "Pregúntame algo..."
- Attachments enabled: Images (PNG/JPEG/GIF/WebP) and PDFs
- Max 5 files, 10MB each
- Two-phase upload strategy
```

**Chateable System** (Critical Feature):
- Any UI element can be made "chateable" (clickable to send contextual message to chat)
- Uses custom event system: `window.dispatchEvent(new CustomEvent('chatkit:sendMessage', { detail: { message, metadata } }))`
- ChatKit panel listens for events and sends messages programmatically
- Metadata includes: `ui_component`, `entity_id`, `entity_type` for context-aware queries
- Metadata injected into API URL as query params via custom fetch function
- Mobile: Drawer auto-closes when chateable element is clicked

### 3. Dashboard/Home View

**Layout Structure** (Desktop):
```
┌─────────────────────────────────────────────────────┐
│  Previous Month Card     Current Month Card (Larger)│
│  (Hidden on mobile,      (Vibrant, gradient bg,     │
│   visible on desktop)     animated badge)           │
│                                                      │
│  Quick Actions Grid (3 buttons)                     │
│  - Gasto | Resumen | Sociedad                      │
├─────────────────────────────────────────────────────┤
│  Calendar Widget        │  Movements Panel          │
│  (Upcoming events)      │  (Recent documents)       │
│  - Urgent (0-10 days)   │  - Last 10 days compact   │
│  - Later (11-60 days)   │  - Expandable to full list│
└─────────────────────────────────────────────────────┘
```

**Mobile Layout**:
- Stacked single-column layout
- Previous month card hidden
- Calendar widget hidden when movements panel is expanded
- All elements remain chateable

**Period Cards** (Tax Summary):

*Previous Month Card* (Compact, only on desktop):
- Border color: Green if paid, red if unpaid
- Background: Light green/red tinted
- Badge: "Pagado" (green) | "A Pagar" (red) | "Al día" (gray)
- Displays: Monto Pagado/Monto a Pagar (large bold number)
- "Pagar" button if unpaid (chateable: "Ayúdame a pagar mi F29 de {amount} del período {period}")
- Tax amount is chateable: "Explícame cómo se calculó el impuesto de {amount} del período {period}"

*Current Month Card* (Vibrant, larger):
- Gradient background: emerald-50 → emerald-100 → teal-50
- Border: 2px emerald-300 with emerald shadow glow
- Animated badge: "En Curso" with pulse animation, gradient emerald→teal
- Three chateable sections:
  1. **Impuesto Proyectado** (Projected Tax) - Large 4xl font, trending-up icon
     - Click: "Explícame cómo se calculó el impuesto proyectado de {amount} del período {period}"
  2. **Ventas** (Sales) - Dollar-sign icon, emerald gradient card
     - Click: "Dame detalles de mis ingresos de {amount} en {period}"
  3. **Compras** (Purchases) - Shopping-cart icon, teal gradient card
     - Click: "Analiza mis compras de {amount} en {period}"
- All amounts formatted as Chilean Peso (CLP) with no decimals: "$1.234.567"

**Quick Actions Grid**:
- 3-column responsive grid
- Light gray cards with rounded corners and icons
- Each button is chateable:
  1. **Gasto** (Plus icon) → "Ayúdame a agregar un nuevo gasto o compra"
  2. **Resumen** (Bar chart icon) → "Dame un resumen detallado de mi situación tributaria actual"
  3. **Sociedad** (Help circle icon) → "Muéstrame la información completa de mi sociedad y empresa"

**Calendar Widget**:
- Shows upcoming tax events (60 days ahead)
- Split into two sections:
  - **Urgent** (0-10 days): Red border, alarm icon, "Hoy"/"Mañana"/"X días"
  - **Later** (11-60 days): Gray border, compact style
- Each event is chateable (wrapped in ChateableWrapper):
  - Message: "Dame información sobre mi obligación tributaria: {eventName} que vence el {dueDate}"
  - Metadata: `ui_component: "tax_calendar_event"`, `entity_id: {eventId}`, `entity_type: "calendar_event"`

**Movements Panel**:
- Compact view: Last 10 days of activity
- Expandable view: Full infinite scroll list (50 items per page)
- Toggle button to expand/collapse
- Filters:
  - Document type: All | Sales | Purchases (buttons)
  - Search by: Counterparty, folio, type, amount
  - Hide zero-amount documents (checkbox)
- CSV download button (opens modal)
- Groups documents by date (most recent first)
- Each document row displays:
  - Type badge (e.g., "Factura Electrónica", "Boleta")
  - Counterparty/issuer name
  - Folio number
  - Net amount, IVA amount, total amount
  - All amounts in CLP format
- Entire row is chateable (fragment mode to preserve HTML structure)

**CSV Download Modal**:
- Select year (dropdown)
- Multi-select months (checkboxes with "Select All" button)
- Multi-select document types (checkboxes with "Select All" button)
- Clear all buttons for each section
- Download button triggers CSV generation

### 4. Data Fetching & State Management

**React Query Configuration**:
- Stale time: 60 seconds (refetch after 1 minute)
- Cache time: 5 minutes (garbage collection)
- Retry count: 1
- Refetch on window focus: disabled

**Key Hooks** (Custom React Query hooks):
1. `useUserSessions()` - Fetch user's company sessions with company data
2. `useTaxSummary({ companyId, period })` - Tax calculations (revenue, expenses, IVA, PPM, projected tax)
3. `useInfiniteCompanyDocuments({ companyId, pageSize: 50 })` - Paginated documents with infinite scroll
4. `useUpcomingEvents({ companyId, daysAhead: 60 })` - Calendar events
5. `useF29Forms({ companyId, year, month })` - Tax form submission status
6. `useChateableClick({ message, contextData, uiComponent, entityId, entityType })` - Hook for individual chateable elements

**Query Key Pattern**:
- Centralized in `/lib/query-keys.ts`
- Format: `['entity', companyId, ...params]`
- Example: `['tax-summary', companyId, period]`

### 5. Design System

**Color Palette**:
```typescript
Primary: Emerald (green)
- emerald-50, emerald-100, emerald-500, emerald-600
- Active states: bg-emerald-500 with shadow-emerald-500/50
- Hover: bg-emerald-600

Secondary: Slate (gray)
- slate-200, slate-400, slate-600, slate-700, slate-900
- Borders: border-slate-200 (light) / slate-700 (dark)

Status Colors:
- Success: green-600, green-50 (bg)
- Warning: yellow-600, yellow-50 (bg)
- Error: red-600, red-50 (bg)
- Info: blue-500

Gradients:
- Background: from-emerald-50 via-white to-teal-50
- Current month card: from-emerald-50 via-emerald-100/50 to-teal-50
```

**Typography**:
- Font family: Questrial (loaded from Google Fonts)
- Base size: 16px
- Tax amounts: 4xl (36px) bold
- Card headers: sm (14px) medium/semibold
- Period labels: xs (12px) semibold

**Spacing & Layout**:
- Standard gap: 4 (1rem = 16px)
- Card padding: 4 (mobile), 6 (desktop)
- Border radius: xl (12px) for cards, lg (8px) for buttons
- Split view: 30% chat, 70% content (desktop)

**Animations**:
- Pulse badge: 2s infinite pulse on "En Curso" badge
- Hover transforms: `translateY(-1px)` + soft shadow
- Transitions: 0.2s cubic-bezier for chateable elements
- Drawer: 0.3s ease-out for slide-up/dismiss
- Loading spinners: 1s spin animation

**Dark Mode**:
- All colors have dark variants (e.g., `dark:bg-slate-900`)
- Synced with system theme via `next-themes`
- ChatKit theme updates dynamically

### 6. Mobile Interactions

**Drawer Behavior**:
- Trigger: Click any bottom navigation tab
- Height: 80vh
- Rounded top corners: 2xl (16px)
- Box shadow: Multi-layer shadow for depth
- Handle bar: 1.5px high × 20px wide, slate-400 color
- Swipe to dismiss:
  - Touch start: Capture Y position
  - Touch move: Transform drawer down if dragging > 0
  - Touch end: Close if dragged > 150px, otherwise snap back
  - Supports both touch and mouse events
- Backdrop: Transparent overlay, click to close
- Close button: Absolute positioned top-right, X icon
- Pull-to-refresh disabled when drawer is open (`overscrollBehavior: 'none'`)

**Auto-close on Chateable Click**:
- Listen for `chatkit:sendMessage` event
- If mobile and drawer is open, close drawer after message sent
- Smooth transition back to chat view

**Bottom Navigation**:
- Fixed at bottom with border-top
- 5 tabs with icons (Lucide React)
- Active state: Emerald bg, white text, shadow glow
- Inactive state: Slate text, transparent bg
- Always visible on mobile

**Responsive Breakpoints**:
- Mobile: < 1024px (lg)
- Desktop: ≥ 1024px
- Utilities: `hidden lg:flex`, `flex lg:hidden`

### 7. Component Structure

**Main Components**:
```
/app/dashboard/page.tsx (512 lines)
├── Header (company selector, tabs, notifications)
├── ChatKitPanel (always visible, 30% on desktop)
└── Content Area (70% on desktop)
    ├── DashboardView
    │   ├── PeriodCard (previous)
    │   ├── PeriodCard (current)
    │   ├── QuickActions
    │   ├── CalendarWidget
    │   └── MovementsPanel
    ├── ContactsView
    ├── PersonnelView
    ├── FormsView
    └── SettingsView

/components/chat/chatkit-panel.tsx (256 lines)
- ChatKit React integration
- Custom fetch with auth + metadata injection
- Event listener for chateable messages
- Theme configuration
- Start screen prompts

/components/features/dashboard/DashboardView.tsx (449 lines)
- Container for all dashboard sub-components
- Data fetching orchestration
- Filter/search state management
- CSV download modal

/components/ui/ChateableWrapper.tsx (169 lines)
- Generic wrapper for chateable elements
- Supports fragment mode for <tr> elements
- Keyboard accessibility (Enter/Space)
- Metadata injection
- Event dispatching
```

**ChateableWrapper Usage**:
```typescript
// Wrap entire components
<ChateableWrapper
  message="Analyze my tax summary"
  contextData={{ period: "2024-01" }}
  uiComponent="tax_summary_iva"
  entityId="2024-01"
  entityType="tax_period"
>
  <TaxCard />
</ChateableWrapper>

// Fragment mode for table rows
<ChateableWrapper
  as="fragment"
  message={(data) => `Show details for ${data.name}`}
  contextData={{ contactId: "123", name: "John" }}
>
  <tr>...</tr>
</ChateableWrapper>

// Hook for individual elements
const clickProps = useChateableClick({
  message: "Explain this amount",
  contextData: { amount: 1000 },
  uiComponent: "amount_detail"
});

return <p {...clickProps}>{amount}</p>;
```

### 8. Authentication & Session Management

**Supabase Auth**:
- JWT tokens from Supabase Auth
- Session stored in browser
- Auto-refresh on expiry
- Middleware redirects unauthenticated users to `/` (landing page)

**Company Sessions**:
- User can have multiple company sessions (multi-tenancy)
- Session includes: `{ id, company: { id, rut, business_name, trade_name, ... } }`
- Company selector in header if user has multiple sessions
- Selected company ID passed to all hooks and ChatKit
- Auto-redirect to `/onboarding/sii` if user has no sessions

**Session Flow**:
1. User logs in via Supabase Auth
2. Fetch user sessions via `useUserSessions()` hook
3. Default to first session, or use selected session
4. Pass `companyId` to all child components
5. ChatKit API URL includes `?company_id={companyId}` for context

### 9. Chilean Localization

**Date Formatting**:
```typescript
// Full date: "lunes, 15 de enero de 2024"
formatDate(dateString) → Intl.DateTimeFormat('es-CL', {
  weekday: 'long', day: 'numeric', month: 'long'
})

// Month-Year: "enero de 2024"
formatMonthYear(year, month) → Intl.DateTimeFormat('es-CL', {
  month: 'long', year: 'numeric'
})

// Due date: "15 ene. 2024"
formatDueDate(dateString) → Intl.DateTimeFormat('es-CL', {
  day: 'numeric', month: 'short', year: 'numeric'
})
```

**Currency Formatting**:
```typescript
// Chilean Peso (CLP) with no decimals
formatCurrency(amount) → Intl.NumberFormat('es-CL', {
  style: 'currency',
  currency: 'CLP',
  minimumFractionDigits: 0
})
// Result: "$1.234.567"
```

**Days Left Formatting**:
```typescript
formatDaysLeft(days) →
  days === 0 ? "Hoy" :
  days === 1 ? "Mañana" :
  `${days} días`
```

**Locale Settings**:
- ChatKit locale: `es-ES`
- All text in Spanish
- Period format: "YYYY-MM" (e.g., "2024-01")

### 10. Backend API Integration

**ChatKit Proxy Endpoint**:
```
POST /api/chatkit?company_id={companyId}&ui_component={component}&entity_id={id}&entity_type={type}
Headers: Authorization: Bearer {jwt_token}
Body: ChatKit message/thread operations

Response: ChatKit standard responses
```

**Tax Summary Endpoint**:
```
GET /api/tax/summary?company_id={companyId}&period=2024-01
Response: {
  revenue: number,
  expenses: number,
  iva_credit: number,
  iva_debit: number,
  ppm: number,  // 0.125% of net revenue
  monthly_tax: number,  // IVA debit - IVA credit + PPM
}
```

**Documents Endpoint** (Infinite Scroll):
```
GET /api/tax/documents?company_id={companyId}&page=1&page_size=50
Response: {
  documents: DocumentWithType[],
  next_page: number | null,
  has_more: boolean,
}
```

**Calendar Events Endpoint**:
```
GET /api/calendar/events?company_id={companyId}&days_ahead=60
Response: {
  events: CalendarEvent[],
}
```

**F29 Forms Endpoint**:
```
GET /api/tax/f29-forms?company_id={companyId}&year=2024&month=1
Response: {
  data: F29Form[],
}
```

### 11. Error Handling & Loading States

**Loading States**:
- Skeleton loaders: Spinning emerald circle (4px border, transparent top)
- Displayed during: Auth check, session load, data fetching
- Position: Center of container with gradient background

**Error States**:
- Red text with error message
- Retry button if applicable
- Fallback UI if critical error

**Empty States**:
- No sessions → Auto-redirect to onboarding
- No documents → "Sin movimientos recientes"
- No events → Calendar widget hidden

**Optimistic UI**:
- Chateable clicks dispatch event immediately
- No waiting for backend response
- Background drawer closes instantly on mobile

### 12. Key Technical Requirements

**Must-Have Features for Expo/React Native**:
1. **Chat Panel Integration**: Embed OpenAI ChatKit (or equivalent) with custom event system
2. **Chateable System**: Any component can dispatch chat messages with metadata
3. **Bottom Sheet/Drawer**: Native slide-up modal with gesture handling
4. **Infinite Scroll**: FlatList with pagination for documents
5. **Bottom Navigation**: Tab navigator with 5 tabs
6. **Split View (Tablet)**: 30-70 split for iPad/large screens
7. **Dark Mode**: System-synced theme switching
8. **Pull-to-Refresh**: Native refresh control
9. **File Upload**: Image picker + document picker for chat attachments
10. **Haptic Feedback**: Subtle haptics on chateable clicks
11. **Authentication**: Supabase React Native SDK
12. **HTTP Client**: Axios/Fetch with JWT interceptor
13. **State Management**: React Query (@tanstack/react-query)
14. **Navigation**: React Navigation (Tab + Stack navigators)

**Libraries/Packages** (Expo equivalents):
- `@openai/chatkit-react` → Custom WebView or native implementation
- `@supabase/ssr` → `@supabase/supabase-js` (React Native)
- `@tanstack/react-query` → Same package
- `lucide-react` → `lucide-react-native`
- `next-themes` → Custom theme context with AsyncStorage
- React Navigation v6 for navigation
- React Native Reanimated for animations
- React Native Gesture Handler for drawer
- Expo Image Picker for attachments

**Performance Considerations**:
- Virtualized lists for documents (FlatList)
- Memoized calculations (useMemo)
- Debounced search input (300ms)
- Image optimization (Expo Image)
- Lazy loading for heavy components
- Cache invalidation on company switch

### 13. Accessibility

**Keyboard Navigation**:
- All chateable elements support Enter/Space
- Tab index management (0 for enabled, -1 for disabled)
- Focus visible styles (2px blue outline)

**Screen Readers**:
- ARIA roles: role="button" for chateable elements
- aria-label for icon-only buttons
- aria-disabled for disabled elements

**Touch Targets**:
- Minimum 48px × 48px for all interactive elements
- Adequate spacing between adjacent buttons (8px minimum)

**Color Contrast**:
- WCAG AA compliant
- Dark mode meets contrast requirements
- Status colors distinguishable (green/red/yellow)

### 14. Screenshots Reference

**Screenshot 1** (Bottom Sheet with Tax Summary):
- Shows current month ("noviembre de 2025")
- 3 tabs at top: Gasto, Resumen (active), Sociedad
- "En Curso" badge (animated)
- Large projected tax: "$5.755"
- Sales: "$5.479.018", Purchases: "$1.621.467"
- Emerald gradient background on card
- Bottom navigation: 5 icons, left icon (home) highlighted

**Screenshot 2** (Chat Start Screen):
- "Fizko" greeting header
- 4 prompt suggestion buttons:
  1. "Quiero agregar un gasto"
  2. "Dame un resumen de ventas"
  3. "Agrega un nuevo colaborador"
  4. "Quiero darte feedback"
- Text input at bottom: "Pregúntame algo..."
- Bottom navigation: Same 5 icons
- Clean white background

### 15. Implementation Priority

**Phase 1** (MVP):
1. Authentication & session management
2. Bottom navigation + tab views
3. ChatKit integration (WebView or custom)
4. Dashboard with period cards (current month only)
5. Chateable wrapper component
6. Basic theme support (light mode)

**Phase 2** (Enhanced):
1. Bottom sheet drawer with gestures
2. Previous month card
3. Movements panel (compact view)
4. Calendar widget
5. Quick actions grid
6. Dark mode
7. Infinite scroll for documents

**Phase 3** (Complete):
1. CSV download modal
2. Advanced filters (search, type, hide zero)
3. Tablet split view
4. Full animations
5. Haptic feedback
6. Accessibility enhancements
7. Error handling & loading states

---

## Summary

This is a **conversational AI tax assistant** where the chat interface is the primary interaction model. The key innovation is the **chateable system**: any UI element can be clicked to send a contextual message to the AI agent. The mobile UX prioritizes chat-first interactions with a slide-up drawer for data views. The design is clean, modern, and optimized for Chilean small business owners who need quick, conversational access to their tax information.
