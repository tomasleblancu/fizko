import { Building2 } from 'lucide-react';
import type { Company } from "@/shared/types/fizko";
import type { ColorScheme } from "@/shared/hooks/useColorScheme";
import { CompanyInfoCardSkeleton } from './CompanyInfoCardSkeleton';
import { ChateableWrapper } from '@/shared/ui/ChateableWrapper';
import { FizkoLogo } from '@/shared/ui/branding/FizkoLogo';
import '@/app/styles/chateable.css';

interface CompanyInfoCardProps {
  company: Company | null;
  loading: boolean;
  scheme: ColorScheme;
  isInDrawer?: boolean;
}

export function CompanyInfoCard({ company, loading, scheme, isInDrawer = false }: CompanyInfoCardProps) {
  if (loading) {
    return <CompanyInfoCardSkeleton />;
  }

  if (!company) {
    return (
      <div className="rounded-2xl border border-amber-200/70 bg-amber-50/80 p-6 dark:border-amber-900/40 dark:bg-amber-900/20">
        <div className="flex items-center gap-3 text-amber-700 dark:text-amber-400">
          <Building2 className="h-6 w-6" />
          <p className="text-sm font-medium">No se encontró información de la empresa</p>
        </div>
      </div>
    );
  }

  return (
    <ChateableWrapper
      message={`Cuéntame sobre mi empresa ${company.business_name}`}
      contextData={{
        companyId: company.id,
        businessName: company.business_name,
        rut: company.rut,
      }}
      uiComponent="CompanyInfoCard"
    >
      <div className={isInDrawer ? "p-0" : "rounded-2xl border border-slate-200/70 bg-gradient-to-br from-emerald-50 to-teal-50 p-3 dark:border-slate-800/70 dark:from-emerald-950/30 dark:to-teal-950/30"}>
        {/* Company Info */}
        <div className="flex items-center gap-3">
          {/* Fizko Logo */}
          <FizkoLogo className="h-8 w-8 flex-shrink-0" />

          {/* Company content */}
          <div className="flex-1">
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
              {company.business_name}
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              RUT: {company.rut}
            </p>
          </div>
        </div>
      </div>
    </ChateableWrapper>
  );
}
