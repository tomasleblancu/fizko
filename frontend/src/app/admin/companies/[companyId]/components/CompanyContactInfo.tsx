import { Mail, MapPin, Phone } from "lucide-react";
import { Card } from "@/components/ui/card";
import type { CompanyDetail } from "@/services/admin/companies.service";

interface CompanyContactInfoProps {
  company: CompanyDetail;
}

export function CompanyContactInfo({ company }: CompanyContactInfoProps) {
  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        Información de Contacto
      </h2>
      <div className="space-y-3">
        {company.email && (
          <div className="flex items-center gap-3">
            <Mail className="h-5 w-5 text-gray-400" />
            <div>
              <p className="text-sm text-gray-600">Email</p>
              <p className="text-gray-900">{company.email}</p>
            </div>
          </div>
        )}
        {company.phone && (
          <div className="flex items-center gap-3">
            <Phone className="h-5 w-5 text-gray-400" />
            <div>
              <p className="text-sm text-gray-600">Teléfono</p>
              <p className="text-gray-900">{company.phone}</p>
            </div>
          </div>
        )}
        {company.address && (
          <div className="flex items-center gap-3">
            <MapPin className="h-5 w-5 text-gray-400" />
            <div>
              <p className="text-sm text-gray-600">Dirección</p>
              <p className="text-gray-900">{company.address}</p>
            </div>
          </div>
        )}
        {!company.email && !company.phone && !company.address && (
          <p className="text-sm text-gray-500 italic">
            No hay información de contacto disponible
          </p>
        )}
      </div>
    </Card>
  );
}
