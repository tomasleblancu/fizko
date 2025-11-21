import { Users, Activity, Calendar } from "lucide-react";
import { Card } from "@/components/ui/card";
import type { CompanyDetail } from "@/services/admin/companies.service";

interface CompanyStatsProps {
  company: CompanyDetail;
}

export function CompanyStats({ company }: CompanyStatsProps) {
  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Nunca";
    return new Date(dateString).toLocaleDateString("es-CL", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Card className="p-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Users className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <p className="text-sm text-gray-600">Usuarios</p>
            <p className="text-2xl font-bold text-gray-900">
              {company.users_count || 0}
            </p>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-100 rounded-lg">
            <Activity className="h-5 w-5 text-green-600" />
          </div>
          <div>
            <p className="text-sm text-gray-600">Sesiones Activas</p>
            <p className="text-2xl font-bold text-gray-900">
              {company.sessions?.filter((s) => s.is_active).length || 0}
            </p>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Calendar className="h-5 w-5 text-purple-600" />
          </div>
          <div>
            <p className="text-sm text-gray-600">Última Actividad</p>
            <p className="text-sm font-semibold text-gray-900">
              {formatDate(company.last_activity)}
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
