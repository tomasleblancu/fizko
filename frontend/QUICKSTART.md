# Fizko Frontend - Quick Start Guide

## Installation

```bash
# Navigate to frontend directory
cd /Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will run at: **http://localhost:5171**

## Environment Setup

The `.env` file has been created from `.env.example`. Update these values:

```bash
# Required - Get from Supabase dashboard
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key

# ChatKit - Use default for local development
VITE_CHATKIT_API_DOMAIN_KEY=domain_pk_localhost_dev
```

## Project Overview

This is a tax/accounting platform (Fizko) built by adapting the impor-ai frontend structure:

### Key Changes from Impor-AI:
1. **Context**: `quotation_id` → `company_id`
2. **Dashboard**: QuotationPanel → FinancialDashboard
3. **Data**: Import products → Tax summaries, payroll, documents
4. **Port**: 5170 → 5171

### Main Components:

```
Home.tsx (Main Layout)
├── ChatKitPanel (Left 35%)
│   └── AI assistant with company_id context
└── FinancialDashboard (Right 65%)
    ├── CompanyInfoCard (company details)
    ├── TaxSummaryCard (revenue, IVA, income tax)
    ├── PayrollSummaryCard (salaries, deductions)
    └── RecentDocumentsCard (DTEs, invoices)
```

## Backend Requirements

The frontend expects these API endpoints:

| Endpoint | Purpose |
|----------|---------|
| `POST /chatkit` | ChatKit conversation API |
| `POST /chatkit/upload/{id}` | File uploads |
| `GET /api/company` | Company data |
| `GET /api/tax-summary/{id}` | Tax summaries |
| `GET /api/payroll-summary/{id}` | Payroll data |
| `GET /api/tax-documents/{id}` | Recent documents |

All requests include `Authorization: Bearer {token}` with Supabase JWT.

## File Structure

```
frontend/
├── src/
│   ├── components/          # React components (9 files)
│   ├── contexts/            # AuthContext
│   ├── hooks/               # Custom hooks (5 files)
│   ├── lib/                 # Supabase, config
│   ├── types/               # TypeScript definitions
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── package.json
├── vite.config.ts
├── tailwind.config.ts
└── .env
```

## Development Workflow

1. **Start dev server**: `npm run dev`
2. **Edit components** in `src/components/`
3. **Add API hooks** in `src/hooks/`
4. **Update types** in `src/types/fizko.d.ts`
5. **Build for production**: `npm run build`

## Troubleshooting

### Port already in use
```bash
# Change port in vite.config.ts
server: {
  port: 5172,  // Change this
  // ...
}
```

### Environment variables not loading
- Ensure `.env` file exists in `/frontend/` directory
- Restart dev server after changing `.env`
- All frontend env vars must start with `VITE_`

### API errors
- Check browser console for 401/403 errors
- Verify Supabase credentials in `.env`
- Ensure backend is running on port 8089
- Check `Authorization` header is being sent

## Next Steps

1. **Configure Supabase**:
   - Create project at supabase.com
   - Enable Google OAuth
   - Update `.env` with project credentials

2. **Set up backend**:
   - Ensure backend runs on port 8089
   - Implement API endpoints listed above
   - Configure CORS for `http://localhost:5171`

3. **Test authentication**:
   - Visit http://localhost:5171
   - Click "Sign in with Google"
   - Verify auth flow works

4. **Test dashboard**:
   - Create test data in backend
   - Verify dashboard cards display data
   - Test chat interactions

## Resources

- **Full Documentation**: See `README.md`
- **ChatKit**: https://platform.openai.com/docs/chatkit
- **Supabase**: https://supabase.com/docs
- **TailwindCSS**: https://tailwindcss.com/docs
