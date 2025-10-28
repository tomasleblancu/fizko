# Fizko Frontend

Tax and accounting platform frontend built with React, TypeScript, Vite, TailwindCSS, ChatKit, and Supabase.

## Overview

Fizko is a modern tax and accounting platform for Chilean companies. This frontend provides:
- AI-powered conversational interface via ChatKit
- Financial dashboard with tax summaries, payroll data, and document tracking
- Real-time data synchronization with backend
- Supabase authentication (Google OAuth)
- Responsive design for desktop and mobile

## Project Structure

```
frontend/
├── src/
│   ├── components/           # React components
│   │   ├── ChatKitPanel.tsx          # ChatKit integration (company_id context)
│   │   ├── FinancialDashboard.tsx    # Main dashboard layout
│   │   ├── CompanyInfoCard.tsx       # Company information display
│   │   ├── TaxSummaryCard.tsx        # Tax revenue/IVA summary
│   │   ├── PayrollSummaryCard.tsx    # Payroll summary
│   │   ├── RecentDocumentsCard.tsx   # Recent tax documents list
│   │   ├── Home.tsx                  # Main layout (Chat + Dashboard)
│   │   ├── Header.tsx                # App header with auth menu
│   │   └── LoginOverlay.tsx          # Google OAuth login overlay
│   ├── contexts/
│   │   └── AuthContext.tsx           # Supabase authentication context
│   ├── hooks/
│   │   ├── useColorScheme.ts         # Dark/light theme management
│   │   ├── useCompany.ts             # Fetch company data
│   │   ├── useTaxSummary.ts          # Fetch tax summaries
│   │   ├── usePayroll.ts             # Fetch payroll data
│   │   └── useTaxDocuments.ts        # Fetch recent tax documents
│   ├── lib/
│   │   ├── supabase.ts               # Supabase client setup
│   │   └── config.ts                 # App configuration (API URLs, prompts)
│   ├── types/
│   │   ├── fizko.d.ts                # Fizko type definitions
│   │   ├── chatkit-tools.d.ts        # ChatKit tool types
│   │   └── vite-env.d.ts             # Vite environment types
│   ├── App.tsx                       # Root component with AuthProvider
│   ├── main.tsx                      # Entry point
│   └── index.css                     # Global styles + Tailwind
├── public/                           # Static assets
├── .env                              # Environment variables (copy from .env.example)
├── .env.example                      # Environment variables template
├── package.json                      # Dependencies
├── vite.config.ts                    # Vite configuration (port 5171)
├── tailwind.config.ts                # Tailwind CSS configuration
├── tsconfig.json                     # TypeScript configuration
└── index.html                        # HTML entry point
```

## Key Features

### 1. ChatKit Integration
- **File**: `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/components/ChatKitPanel.tsx`
- Passes `company_id` in API URL query parameters
- Supports two-phase file uploads
- Auth via JWT bearer token
- Theme switching via client tools

### 2. Financial Dashboard
- **File**: `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/components/FinancialDashboard.tsx`
- 2-column card layout:
  - Company Info (full width)
  - Tax Summary (left column)
  - Payroll Summary (right column)
  - Recent Documents (full width)
- Auto-refresh on data updates
- Error handling with user-friendly messages

### 3. Type Definitions
**File**: `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/types/fizko.d.ts`

```typescript
interface Company {
  id: string;
  user_id: string;
  rut: string;
  business_name: string;
  tax_regime: string;
  activity_code: string;
  // ...
}

interface TaxSummary {
  id: string;
  company_id: string;
  period_start: string;
  period_end: string;
  total_revenue: number;
  total_expenses: number;
  iva_collected: number;
  iva_paid: number;
  net_iva: number;
  income_tax: number;
}

interface PayrollSummary {
  period: string;
  total_employees: number;
  total_gross_salary: number;
  total_deductions: number;
  total_net_salary: number;
  total_employer_contributions: number;
}

interface TaxDocument {
  id: string;
  company_id: string;
  document_type: string;
  document_number: string;
  issue_date: string;
  amount: number;
  status: string;
  // ...
}
```

### 4. Custom Hooks

#### useCompany
**File**: `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/hooks/useCompany.ts`
```typescript
const { company, loading, error, refresh } = useCompany();
// Fetches company data for authenticated user
// API: GET /api/company
```

#### useTaxSummary
**File**: `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/hooks/useTaxSummary.ts`
```typescript
const { taxSummary, loading, error, refresh } = useTaxSummary(companyId, period);
// Fetches tax summary for specific period
// API: GET /api/tax-summary/{companyId}?period={period}
```

#### usePayroll
**File**: `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/hooks/usePayroll.ts`
```typescript
const { payrollSummary, loading, error, refresh } = usePayroll(companyId, period);
// Fetches payroll summary for specific period
// API: GET /api/payroll-summary/{companyId}?period={period}
```

#### useTaxDocuments
**File**: `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/hooks/useTaxDocuments.ts`
```typescript
const { documents, loading, error, refresh } = useTaxDocuments(companyId, limit);
// Fetches recent tax documents
// API: GET /api/tax-documents/{companyId}?limit={limit}
```

## Setup

### Prerequisites
- Node.js >= 18.18
- npm >= 9

### Installation

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Configure environment variables:
```bash
# Copy template
cp .env.example .env

# Edit .env with your credentials
# - VITE_SUPABASE_URL
# - VITE_SUPABASE_ANON_KEY
# - VITE_CHATKIT_API_DOMAIN_KEY
```

3. Start development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5171`

## Environment Variables

```bash
# Backend URL
VITE_BACKEND_URL=http://localhost:8089               # For local dev

# ChatKit Configuration
VITE_CHATKIT_API_DOMAIN_KEY=domain_pk_localhost_dev  # For local dev

# Supabase Configuration
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

## API Endpoints Expected

The frontend expects the following backend endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chatkit` | POST | ChatKit conversational API |
| `/chatkit/upload/{attachment_id}` | POST | Two-phase file upload |
| `/api/company` | GET | Get user's company data |
| `/api/tax-summary/{companyId}` | GET | Get tax summary for period |
| `/api/payroll-summary/{companyId}` | GET | Get payroll summary for period |
| `/api/tax-documents/{companyId}` | GET | Get recent tax documents |

All API requests include `Authorization: Bearer {token}` header with Supabase JWT.

## Component Architecture

### Data Flow

```
User Authentication
      ↓
AuthContext (Supabase)
      ↓
Home Component
      ├─→ ChatKitPanel (left, 35% width)
      │   ├─ Passes company_id to backend
      │   ├─ Handles chat interactions
      │   └─ Triggers data refresh on response
      │
      └─→ FinancialDashboard (right, 65% width)
          ├─ CompanyInfoCard (useCompany)
          ├─ TaxSummaryCard (useTaxSummary)
          ├─ PayrollSummaryCard (usePayroll)
          └─ RecentDocumentsCard (useTaxDocuments)
```

### Responsive Design

- **Desktop (lg+)**: Side-by-side layout (Chat 35% | Dashboard 65%)
- **Mobile (<lg)**: Stacked layout with drawer for dashboard

## Styling

- **Framework**: TailwindCSS v3.4
- **Theme**: Light/Dark mode support
- **Colors**: Professional blues/grays for financial data
- **Effects**: Glass-morphism cards, smooth transitions
- **Animations**: Fade-in, slide-up, pulse effects

## Development Scripts

```bash
npm run dev      # Start dev server (port 5171)
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Run ESLint
```

## Key Differences from Impor-AI

| Aspect | Impor-AI | Fizko |
|--------|----------|-------|
| Context | `quotation_id` | `company_id` |
| Dashboard | QuotationPanel | FinancialDashboard |
| Data | Products, shipping, costs | Tax summaries, payroll, documents |
| Domain | Import management | Tax/accounting |
| Port | 5170 | 5171 |

## File Summary

### Core Files Created (22 total)

**Configuration (6 files)**:
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/package.json`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/vite.config.ts`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/tailwind.config.ts`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/.env.example`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/.env`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/index.html`

**Main App Files (3 files)**:
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/main.tsx`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/App.tsx`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/index.css`

**Components (8 files)**:
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/components/Home.tsx`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/components/ChatKitPanel.tsx`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/components/FinancialDashboard.tsx`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/components/CompanyInfoCard.tsx`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/components/TaxSummaryCard.tsx`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/components/PayrollSummaryCard.tsx`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/components/RecentDocumentsCard.tsx`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/components/LoginOverlay.tsx`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/components/Header.tsx`

**Context & Hooks (6 files)**:
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/contexts/AuthContext.tsx`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/hooks/useColorScheme.ts`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/hooks/useCompany.ts`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/hooks/useTaxSummary.ts`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/hooks/usePayroll.ts`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/hooks/useTaxDocuments.ts`

**Lib & Types (5 files)**:
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/lib/supabase.ts`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/lib/config.ts`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/types/fizko.d.ts`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/types/chatkit-tools.d.ts`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/vite-env.d.ts`

## Next Steps

1. **Backend Integration**: Ensure backend endpoints match expected API
2. **Database Schema**: Set up Supabase tables for companies, tax_summaries, payroll_records, tax_documents
3. **Authentication**: Configure Google OAuth in Supabase
4. **Testing**: Test chat interactions and dashboard data flow
5. **Styling**: Customize color scheme and branding as needed

## Support

For issues or questions, refer to:
- ChatKit docs: https://platform.openai.com/docs/chatkit
- Supabase docs: https://supabase.com/docs
- Vite docs: https://vitejs.dev
