import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Calendar, Pencil, Trash2, Building2 } from "lucide-react";
import type { EventTemplate } from "@/types/event-template";

interface EventTemplateCardProps {
  template: EventTemplate;
  onEdit: (template: EventTemplate) => void;
  onDelete: (template: EventTemplate) => void;
}

const CATEGORY_LABELS: Record<string, string> = {
  impuesto_mensual: "Impuesto Mensual",
  impuesto_anual: "Impuesto Anual",
  prevision: "Previsión",
  aduanas: "Aduanas",
  laboral: "Laboral",
  otros: "Otros",
};

const CATEGORY_COLORS: Record<string, string> = {
  impuesto_mensual: "bg-blue-100 text-blue-800",
  impuesto_anual: "bg-purple-100 text-purple-800",
  prevision: "bg-green-100 text-green-800",
  aduanas: "bg-yellow-100 text-yellow-800",
  laboral: "bg-orange-100 text-orange-800",
  otros: "bg-gray-100 text-gray-800",
};

const FREQUENCY_LABELS: Record<string, string> = {
  monthly: "Mensual",
  annual: "Anual",
  one_time: "Única vez",
};

export function EventTemplateCard({ template, onEdit, onDelete }: EventTemplateCardProps) {
  const categoryLabel = CATEGORY_LABELS[template.category] || template.category;
  const categoryColor = CATEGORY_COLORS[template.category] || "bg-gray-100 text-gray-800";
  const frequencyLabel = FREQUENCY_LABELS[template.default_recurrence.frequency] || template.default_recurrence.frequency;

  return (
    <Card className="p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className={`p-2 ${categoryColor.split(' ')[0]} rounded-lg flex-shrink-0`}>
          <Calendar className={`h-5 w-5 ${categoryColor.split(' ')[1]}`} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-start justify-between mb-2">
            <div>
              <h3 className="font-semibold text-gray-900 text-lg">
                {template.name}
              </h3>
              <p className="text-sm text-gray-500">
                Código: <span className="font-mono">{template.code}</span>
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onEdit(template)}
                className="flex items-center gap-1"
              >
                <Pencil className="h-3 w-3" />
                Editar
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onDelete(template)}
                className="flex items-center gap-1 text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                <Trash2 className="h-3 w-3" />
                Eliminar
              </Button>
            </div>
          </div>

          {/* Description */}
          {template.description && (
            <p className="text-sm text-gray-600 mb-3">
              {template.description}
            </p>
          )}

          {/* Badges and Info */}
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <Badge className={categoryColor}>
              {categoryLabel}
            </Badge>
            {template.authority && (
              <Badge variant="outline" className="flex items-center gap-1">
                <Building2 className="h-3 w-3" />
                {template.authority}
              </Badge>
            )}
            {template.is_mandatory && (
              <Badge className="bg-red-100 text-red-800">
                Obligatorio
              </Badge>
            )}
            <Badge variant="outline">
              {frequencyLabel}
            </Badge>
          </div>

          {/* Recurrence Details */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-gray-600">Recurrencia:</span>
              <span className="font-medium text-gray-900">
                {template.default_recurrence.frequency === 'monthly' &&
                  `Día ${template.default_recurrence.day_of_month} de cada mes`}
                {template.default_recurrence.frequency === 'annual' &&
                  `${template.default_recurrence.day_of_month} del mes ${template.default_recurrence.month_of_year}`}
                {template.default_recurrence.frequency === 'one_time' && 'Única vez'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-600">Mostrar con:</span>
              <span className="font-medium text-gray-900">
                {template.display_days_before} días de anticipación
              </span>
            </div>
          </div>

          {/* Regimes */}
          {template.applies_to_regimes && template.applies_to_regimes.length > 0 && (
            <div className="mt-3">
              <span className="text-sm text-gray-600">Aplica a regímenes: </span>
              <div className="flex flex-wrap gap-1 mt-1">
                {template.applies_to_regimes.map((regime) => (
                  <Badge key={regime} variant="outline" className="text-xs">
                    {regime}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
