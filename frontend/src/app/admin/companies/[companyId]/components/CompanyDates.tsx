import { Calendar } from "lucide-react";
import { Card } from "@/components/ui/card";
import type { CompanyDetail } from "@/services/admin/companies.service";

interface CompanyDatesProps {
  company: CompanyDetail;
}

export function CompanyDates({ company }: CompanyDatesProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("es-CL", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        Fechas Importantes
      </h2>
      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <Calendar className="h-5 w-5 text-gray-400" />
          <div>
            <p className="text-sm text-gray-600">Fecha de Creación</p>
            <p className="text-gray-900">{formatDate(company.created_at)}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Calendar className="h-5 w-5 text-gray-400" />
          <div>
            <p className="text-sm text-gray-600">Última Actualización</p>
            <p className="text-gray-900">{formatDate(company.updated_at)}</p>
          </div>
        </div>
      </div>
    </Card>
  );
}
