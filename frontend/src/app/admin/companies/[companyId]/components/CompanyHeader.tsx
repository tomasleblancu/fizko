import { ArrowLeft, Building2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { CompanyDetail } from "@/services/admin/companies.service";

interface CompanyHeaderProps {
  company: CompanyDetail;
  onBack: () => void;
}

export function CompanyHeader({ company, onBack }: CompanyHeaderProps) {
  return (
    <div className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Button
          variant="ghost"
          onClick={onBack}
          className="mb-4 -ml-2"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver al listado
        </Button>

        <div className="flex items-start gap-4">
          <div className="p-3 bg-blue-100 rounded-lg">
            <Building2 className="h-8 w-8 text-blue-600" />
          </div>
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-900">
              {company.business_name || company.trade_name || "Sin nombre"}
            </h1>
            {company.trade_name &&
              company.business_name !== company.trade_name && (
                <p className="text-lg text-gray-600 mt-1">
                  {company.trade_name}
                </p>
              )}
            <div className="flex items-center gap-2 mt-2">
              <Badge variant="outline">{company.rut}</Badge>
              {company.sii_password && (
                <Badge variant="secondary" className="bg-green-100 text-green-800">
                  SII Configurado
                </Badge>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
