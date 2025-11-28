import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { X } from "lucide-react";
import type { EventTemplate, EventCategory, CreateEventTemplateDto, RecurrenceFrequency } from "@/types/event-template";

interface EventTemplateFormProps {
  template?: EventTemplate | null;
  onSubmit: (data: CreateEventTemplateDto) => Promise<void>;
  onCancel: () => void;
}

const CATEGORIES: { value: EventCategory; label: string }[] = [
  { value: "impuesto_mensual", label: "Impuesto Mensual" },
  { value: "impuesto_anual", label: "Impuesto Anual" },
  { value: "prevision", label: "Previsión" },
  { value: "aduanas", label: "Aduanas" },
  { value: "laboral", label: "Laboral" },
  { value: "otros", label: "Otros" },
];

const FREQUENCIES: { value: RecurrenceFrequency; label: string }[] = [
  { value: "monthly", label: "Mensual" },
  { value: "annual", label: "Anual" },
  { value: "one_time", label: "Única vez" },
];

export function EventTemplateForm({ template, onSubmit, onCancel }: EventTemplateFormProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<EventCategory>("impuesto_mensual");
  const [authority, setAuthority] = useState("");
  const [isMandatory, setIsMandatory] = useState(false);
  const [regimes, setRegimes] = useState("");
  const [frequency, setFrequency] = useState<RecurrenceFrequency>("monthly");
  const [dayOfMonth, setDayOfMonth] = useState(1);
  const [monthOfYear, setMonthOfYear] = useState(1);
  const [businessDaysAdjustment, setBusinessDaysAdjustment] = useState<"before" | "after" | "none">("none");
  const [displayDaysBefore, setDisplayDaysBefore] = useState(30);

  // Load template data if editing
  useEffect(() => {
    if (template) {
      setCode(template.code);
      setName(template.name);
      setDescription(template.description || "");
      setCategory(template.category);
      setAuthority(template.authority || "");
      setIsMandatory(template.is_mandatory);
      setRegimes(template.applies_to_regimes?.join(", ") || "");
      setFrequency(template.default_recurrence.frequency);
      setDayOfMonth(template.default_recurrence.day_of_month || 1);
      setMonthOfYear(template.default_recurrence.month_of_year || 1);
      setBusinessDaysAdjustment(template.default_recurrence.business_days_adjustment || "none");
      setDisplayDaysBefore(template.display_days_before);
    }
  }, [template]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const data: CreateEventTemplateDto = {
        code,
        name,
        description: description || undefined,
        category,
        authority: authority || undefined,
        is_mandatory: isMandatory,
        applies_to_regimes: regimes
          ? regimes.split(",").map((r) => r.trim()).filter(Boolean)
          : undefined,
        default_recurrence: {
          frequency,
          day_of_month: frequency !== "one_time" ? dayOfMonth : undefined,
          month_of_year: frequency === "annual" ? monthOfYear : undefined,
          business_days_adjustment: businessDaysAdjustment !== "none" ? businessDaysAdjustment : undefined,
        },
        display_days_before: displayDaysBefore,
      };

      await onSubmit(data);
    } catch (err) {
      console.error("Error submitting form:", err);
      setError(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            {template ? "Editar Template" : "Nuevo Template"}
          </h2>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Error Message */}
          {error && (
            <div className="p-3 rounded-lg bg-red-50 text-red-800 text-sm">
              {error}
            </div>
          )}

          {/* Code and Name */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="code" className="text-sm font-medium">
                Código <span className="text-red-500">*</span>
              </Label>
              <Input
                id="code"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="f29"
                required
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="name" className="text-sm font-medium">
                Nombre <span className="text-red-500">*</span>
              </Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Declaración Mensual F29"
                required
                className="mt-1"
              />
            </div>
          </div>

          {/* Description */}
          <div>
            <Label htmlFor="description" className="text-sm font-medium">
              Descripción
            </Label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Descripción del template..."
              rows={3}
              className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Category and Authority */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="category" className="text-sm font-medium">
                Categoría <span className="text-red-500">*</span>
              </Label>
              <select
                id="category"
                value={category}
                onChange={(e) => setCategory(e.target.value as EventCategory)}
                required
                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {CATEGORIES.map((cat) => (
                  <option key={cat.value} value={cat.value}>
                    {cat.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label htmlFor="authority" className="text-sm font-medium">
                Autoridad
              </Label>
              <Input
                id="authority"
                value={authority}
                onChange={(e) => setAuthority(e.target.value)}
                placeholder="SII"
                className="mt-1"
              />
            </div>
          </div>

          {/* Is Mandatory and Display Days */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="isMandatory"
                checked={isMandatory}
                onChange={(e) => setIsMandatory(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <Label htmlFor="isMandatory" className="text-sm font-medium cursor-pointer">
                Obligatorio
              </Label>
            </div>
            <div>
              <Label htmlFor="displayDaysBefore" className="text-sm font-medium">
                Días de anticipación
              </Label>
              <Input
                id="displayDaysBefore"
                type="number"
                min="1"
                max="365"
                value={displayDaysBefore}
                onChange={(e) => setDisplayDaysBefore(parseInt(e.target.value) || 30)}
                className="mt-1"
              />
            </div>
          </div>

          {/* Regimes */}
          <div>
            <Label htmlFor="regimes" className="text-sm font-medium">
              Regímenes aplicables
            </Label>
            <Input
              id="regimes"
              value={regimes}
              onChange={(e) => setRegimes(e.target.value)}
              placeholder="pro_pyme, general, 14ter (separados por coma)"
              className="mt-1"
            />
            <p className="text-xs text-gray-500 mt-1">
              Separar con comas. Ej: pro_pyme, general, 14ter
            </p>
          </div>

          {/* Recurrence Section */}
          <div className="border-t border-gray-200 pt-4">
            <h3 className="font-semibold text-gray-900 mb-3">Recurrencia</h3>

            <div className="space-y-4">
              {/* Frequency */}
              <div>
                <Label htmlFor="frequency" className="text-sm font-medium">
                  Frecuencia <span className="text-red-500">*</span>
                </Label>
                <select
                  id="frequency"
                  value={frequency}
                  onChange={(e) => setFrequency(e.target.value as RecurrenceFrequency)}
                  required
                  className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {FREQUENCIES.map((freq) => (
                    <option key={freq.value} value={freq.value}>
                      {freq.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Day and Month (conditional) */}
              {frequency !== "one_time" && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="dayOfMonth" className="text-sm font-medium">
                      Día del mes
                    </Label>
                    <Input
                      id="dayOfMonth"
                      type="number"
                      min="1"
                      max="31"
                      value={dayOfMonth}
                      onChange={(e) => setDayOfMonth(parseInt(e.target.value) || 1)}
                      className="mt-1"
                    />
                  </div>
                  {frequency === "annual" && (
                    <div>
                      <Label htmlFor="monthOfYear" className="text-sm font-medium">
                        Mes del año
                      </Label>
                      <Input
                        id="monthOfYear"
                        type="number"
                        min="1"
                        max="12"
                        value={monthOfYear}
                        onChange={(e) => setMonthOfYear(parseInt(e.target.value) || 1)}
                        className="mt-1"
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Business Days Adjustment */}
              <div>
                <Label htmlFor="businessDaysAdjustment" className="text-sm font-medium">
                  Ajuste por días hábiles
                </Label>
                <select
                  id="businessDaysAdjustment"
                  value={businessDaysAdjustment}
                  onChange={(e) =>
                    setBusinessDaysAdjustment(e.target.value as "before" | "after" | "none")
                  }
                  className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="none">Sin ajuste</option>
                  <option value="before">Día hábil anterior</option>
                  <option value="after">Día hábil siguiente</option>
                </select>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
            <Button type="button" variant="outline" onClick={onCancel} disabled={loading}>
              Cancelar
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Guardando..." : template ? "Actualizar" : "Crear"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
