import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Download, FileText, Calendar, Brain, Loader2, Calculator } from "lucide-react";
import { CeleryTaskService } from "@/services/celery/celery-task.service";

interface CompanySyncActionsProps {
  companyId: string;
}

export function CompanySyncActions({ companyId }: CompanySyncActionsProps) {
  // Task execution states
  const [syncDocsLoading, setSyncDocsLoading] = useState(false);
  const [syncF29Loading, setSyncF29Loading] = useState(false);
  const [generateDraftLoading, setGenerateDraftLoading] = useState(false);
  const [syncCalendarLoading, setSyncCalendarLoading] = useState(false);
  const [syncMemoriesLoading, setSyncMemoriesLoading] = useState(false);
  const [taskMessage, setTaskMessage] = useState<string | null>(null);

  // Task parameters
  const [docsMonths, setDocsMonths] = useState(1);
  const [docsOffset, setDocsOffset] = useState(1);
  const [f29Year, setF29Year] = useState(new Date().getFullYear().toString());
  const [draftYear, setDraftYear] = useState(new Date().getFullYear());
  const [draftMonth, setDraftMonth] = useState(new Date().getMonth() || 12);

  const handleSyncDocuments = async () => {
    try {
      setSyncDocsLoading(true);
      setTaskMessage(null);

      const response = await CeleryTaskService.syncSIIDocuments(
        companyId,
        docsMonths,
        docsOffset
      );

      setTaskMessage(
        `✓ Sincronización de documentos iniciada. Task ID: ${response.task_id}`
      );
    } catch (error) {
      console.error("Error syncing documents:", error);
      setTaskMessage(
        `✗ Error: ${error instanceof Error ? error.message : "Unknown error"}`
      );
    } finally {
      setSyncDocsLoading(false);
    }
  };

  const handleSyncF29 = async () => {
    try {
      setSyncF29Loading(true);
      setTaskMessage(null);

      const response = await CeleryTaskService.syncSIIForm29(
        companyId,
        f29Year
      );

      setTaskMessage(
        `✓ Sincronización de F29 iniciada. Task ID: ${response.task_id}`
      );
    } catch (error) {
      console.error("Error syncing F29:", error);
      setTaskMessage(
        `✗ Error: ${error instanceof Error ? error.message : "Unknown error"}`
      );
    } finally {
      setSyncF29Loading(false);
    }
  };

  const handleSyncCalendar = async () => {
    try {
      setSyncCalendarLoading(true);
      setTaskMessage(null);

      const response = await CeleryTaskService.syncCompanyCalendar(companyId);

      setTaskMessage(
        `✓ Sincronización de calendario iniciada. Task ID: ${response.task_id}`
      );
    } catch (error) {
      console.error("Error syncing calendar:", error);
      setTaskMessage(
        `✗ Error: ${error instanceof Error ? error.message : "Unknown error"}`
      );
    } finally {
      setSyncCalendarLoading(false);
    }
  };

  const handleSyncMemories = async () => {
    try {
      setSyncMemoriesLoading(true);
      setTaskMessage(null);

      const response = await CeleryTaskService.syncCompanyMemories(companyId);

      setTaskMessage(
        `✓ Sincronización de memorias iniciada. Task ID: ${response.task_id}`
      );
    } catch (error) {
      console.error("Error syncing memories:", error);
      setTaskMessage(
        `✗ Error: ${error instanceof Error ? error.message : "Unknown error"}`
      );
    } finally {
      setSyncMemoriesLoading(false);
    }
  };

  const handleGenerateDraft = async () => {
    try {
      setGenerateDraftLoading(true);
      setTaskMessage(null);

      const response = await CeleryTaskService.generateForm29Draft(
        companyId,
        draftYear,
        draftMonth,
        true // auto_calculate
      );

      setTaskMessage(
        `✓ Generación de draft F29 iniciada. Task ID: ${response.task_id}`
      );
    } catch (error) {
      console.error("Error generating F29 draft:", error);
      setTaskMessage(
        `✗ Error: ${error instanceof Error ? error.message : "Unknown error"}`
      );
    } finally {
      setGenerateDraftLoading(false);
    }
  };

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        Acciones de Sincronización
      </h2>

      <div className="space-y-6">
        {/* SII Documents Sync */}
        <div className="border-b border-gray-200 pb-6">
          <div className="flex items-start gap-4">
            <div className="p-2 bg-blue-100 rounded-lg flex-shrink-0">
              <Download className="h-5 w-5 text-blue-600" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-gray-900 mb-1">
                Sincronizar Documentos SII
              </h3>
              <p className="text-sm text-gray-600 mb-3">
                Sincroniza compras y ventas desde el SII
              </p>
              <div className="grid grid-cols-2 gap-3 max-w-md">
                <div>
                  <Label htmlFor="docsMonths" className="text-xs">Meses</Label>
                  <Input
                    id="docsMonths"
                    type="number"
                    min="1"
                    max="12"
                    value={docsMonths}
                    onChange={(e) => setDocsMonths(parseInt(e.target.value) || 1)}
                    disabled={syncDocsLoading}
                    className="h-9"
                  />
                </div>
                <div>
                  <Label htmlFor="docsOffset" className="text-xs">Offset</Label>
                  <Input
                    id="docsOffset"
                    type="number"
                    min="0"
                    max="12"
                    value={docsOffset}
                    onChange={(e) => setDocsOffset(parseInt(e.target.value) || 0)}
                    disabled={syncDocsLoading}
                    className="h-9"
                  />
                </div>
              </div>
            </div>
            <Button
              onClick={handleSyncDocuments}
              disabled={syncDocsLoading}
              className="flex-shrink-0"
            >
              {syncDocsLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Sincronizando...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  Sincronizar
                </>
              )}
            </Button>
          </div>
        </div>

        {/* F29 Sync */}
        <div className="border-b border-gray-200 pb-6">
          <div className="flex items-start gap-4">
            <div className="p-2 bg-green-100 rounded-lg flex-shrink-0">
              <FileText className="h-5 w-5 text-green-600" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-gray-900 mb-1">Sincronizar F29</h3>
              <p className="text-sm text-gray-600 mb-3">
                Sincroniza declaraciones F29 desde el SII
              </p>
              <div className="max-w-xs">
                <Label htmlFor="f29Year" className="text-xs">Año</Label>
                <Input
                  id="f29Year"
                  type="text"
                  placeholder="2025"
                  value={f29Year}
                  onChange={(e) => setF29Year(e.target.value)}
                  disabled={syncF29Loading}
                  className="h-9"
                />
              </div>
            </div>
            <Button
              onClick={handleSyncF29}
              disabled={syncF29Loading}
              className="flex-shrink-0"
            >
              {syncF29Loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Sincronizando...
                </>
              ) : (
                <>
                  <FileText className="h-4 w-4 mr-2" />
                  Sincronizar
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Calendar Sync */}
        <div className="border-b border-gray-200 pb-6">
          <div className="flex items-start gap-4">
            <div className="p-2 bg-purple-100 rounded-lg flex-shrink-0">
              <Calendar className="h-5 w-5 text-purple-600" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-gray-900 mb-1">
                Sincronizar Calendario
              </h3>
              <p className="text-sm text-gray-600">
                Genera eventos de calendario basados en configuración
              </p>
            </div>
            <Button
              onClick={handleSyncCalendar}
              disabled={syncCalendarLoading}
              className="flex-shrink-0"
            >
              {syncCalendarLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Sincronizando...
                </>
              ) : (
                <>
                  <Calendar className="h-4 w-4 mr-2" />
                  Sincronizar
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Generate F29 Draft */}
        <div className="border-b border-gray-200 pb-6">
          <div className="flex items-start gap-4">
            <div className="p-2 bg-yellow-100 rounded-lg flex-shrink-0">
              <Calculator className="h-5 w-5 text-yellow-600" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-gray-900 mb-1">Generar Draft F29</h3>
              <p className="text-sm text-gray-600 mb-3">
                Genera un borrador de F29 con valores calculados desde documentos
              </p>
              <div className="grid grid-cols-2 gap-3 max-w-md">
                <div>
                  <Label htmlFor="draftYear" className="text-xs">Año</Label>
                  <Input
                    id="draftYear"
                    type="number"
                    min="2020"
                    max="2030"
                    value={draftYear}
                    onChange={(e) => setDraftYear(parseInt(e.target.value) || new Date().getFullYear())}
                    disabled={generateDraftLoading}
                    className="h-9"
                  />
                </div>
                <div>
                  <Label htmlFor="draftMonth" className="text-xs">Mes</Label>
                  <Input
                    id="draftMonth"
                    type="number"
                    min="1"
                    max="12"
                    value={draftMonth}
                    onChange={(e) => setDraftMonth(parseInt(e.target.value) || 1)}
                    disabled={generateDraftLoading}
                    className="h-9"
                  />
                </div>
              </div>
            </div>
            <Button
              onClick={handleGenerateDraft}
              disabled={generateDraftLoading}
              className="flex-shrink-0"
            >
              {generateDraftLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Generando...
                </>
              ) : (
                <>
                  <Calculator className="h-4 w-4 mr-2" />
                  Generar
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Memory Sync */}
        <div>
          <div className="flex items-start gap-4">
            <div className="p-2 bg-orange-100 rounded-lg flex-shrink-0">
              <Brain className="h-5 w-5 text-orange-600" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-gray-900 mb-1">
                Cargar Memorias
              </h3>
              <p className="text-sm text-gray-600">
                Carga datos de la empresa en el sistema de memoria (Mem0)
              </p>
            </div>
            <Button
              onClick={handleSyncMemories}
              disabled={syncMemoriesLoading}
              className="flex-shrink-0"
            >
              {syncMemoriesLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Cargando...
                </>
              ) : (
                <>
                  <Brain className="h-4 w-4 mr-2" />
                  Cargar
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Task Message */}
        {taskMessage && (
          <div
            className={`p-3 rounded-lg text-sm ${
              taskMessage.startsWith("✓")
                ? "bg-green-50 text-green-800"
                : "bg-red-50 text-red-800"
            }`}
          >
            {taskMessage}
          </div>
        )}
      </div>
    </Card>
  );
}
