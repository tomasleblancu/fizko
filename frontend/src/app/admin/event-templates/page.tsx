"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createBrowserClient } from "@supabase/ssr";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Calendar, Search, Plus, ArrowLeft, LogOut } from "lucide-react";
import { EventTemplatesService } from "@/services/admin/event-templates.service";
import { EventTemplateCard } from "./components/EventTemplateCard";
import { EventTemplateForm } from "./components/EventTemplateForm";
import type { EventTemplate, EventCategory, CreateEventTemplateDto } from "@/types/event-template";

export default function EventTemplatesPage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<EventTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<EventCategory | "all">("all");

  // Form state
  const [showForm, setShowForm] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<EventTemplate | null>(null);

  const supabase = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
  );

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await EventTemplatesService.listAll();
      setTemplates(data);
    } catch (err) {
      console.error("Error fetching templates:", err);
      setError(err instanceof Error ? err.message : "Error al cargar templates");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await supabase.auth.signOut();
      router.push("/auth/login");
    } catch (err) {
      console.error("Error al cerrar sesión:", err);
    }
  };

  const handleCreate = () => {
    setEditingTemplate(null);
    setShowForm(true);
  };

  const handleEdit = (template: EventTemplate) => {
    setEditingTemplate(template);
    setShowForm(true);
  };

  const handleDelete = async (template: EventTemplate) => {
    if (!confirm(`¿Estás seguro de que quieres eliminar "${template.name}"?`)) {
      return;
    }

    try {
      await EventTemplatesService.delete(template.id);
      await fetchTemplates();
    } catch (err) {
      console.error("Error deleting template:", err);
      alert(err instanceof Error ? err.message : "Error al eliminar");
    }
  };

  const handleSubmit = async (data: CreateEventTemplateDto) => {
    try {
      if (editingTemplate) {
        await EventTemplatesService.update(editingTemplate.id, data);
      } else {
        await EventTemplatesService.create(data);
      }
      await fetchTemplates();
      setShowForm(false);
      setEditingTemplate(null);
    } catch (err) {
      console.error("Error saving template:", err);
      throw err;
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingTemplate(null);
  };

  const filteredTemplates = templates.filter((template) => {
    const matchesSearch =
      searchQuery === "" ||
      template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.description?.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesCategory =
      categoryFilter === "all" || template.category === categoryFilter;

    return matchesSearch && matchesCategory;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando templates...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="p-6 max-w-md">
          <div className="text-center">
            <div className="text-red-500 text-5xl mb-4">⚠️</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Error</h2>
            <p className="text-gray-600 mb-4">{error}</p>
            <Button onClick={fetchTemplates} variant="outline">
              Reintentar
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => router.push("/admin")}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                aria-label="Volver"
              >
                <ArrowLeft className="h-5 w-5 text-gray-600" />
              </button>
              <div className="p-2 bg-blue-100 rounded-lg">
                <Calendar className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Templates de Eventos
                </h1>
                <p className="text-sm text-gray-500">
                  Gestión de plantillas para eventos del calendario
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="outline" className="text-sm">
                {templates.length} {templates.length === 1 ? "template" : "templates"}
              </Badge>
              <Button onClick={handleCreate} className="flex items-center gap-2">
                <Plus className="h-4 w-4" />
                Nuevo Template
              </Button>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                aria-label="Cerrar sesión"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Cerrar sesión</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filters */}
        <div className="mb-6 space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <Input
              type="text"
              placeholder="Buscar por nombre, código o descripción..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 w-full"
            />
          </div>

          {/* Category Filter */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-gray-700">Categoría:</span>
            <button
              onClick={() => setCategoryFilter("all")}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                categoryFilter === "all"
                  ? "bg-blue-100 text-blue-800"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              Todas
            </button>
            <button
              onClick={() => setCategoryFilter("impuesto_mensual")}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                categoryFilter === "impuesto_mensual"
                  ? "bg-blue-100 text-blue-800"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              Impuesto Mensual
            </button>
            <button
              onClick={() => setCategoryFilter("impuesto_anual")}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                categoryFilter === "impuesto_anual"
                  ? "bg-purple-100 text-purple-800"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              Impuesto Anual
            </button>
            <button
              onClick={() => setCategoryFilter("prevision")}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                categoryFilter === "prevision"
                  ? "bg-green-100 text-green-800"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              Previsión
            </button>
            <button
              onClick={() => setCategoryFilter("laboral")}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                categoryFilter === "laboral"
                  ? "bg-orange-100 text-orange-800"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              Laboral
            </button>
            <button
              onClick={() => setCategoryFilter("otros")}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                categoryFilter === "otros"
                  ? "bg-gray-100 text-gray-800"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              Otros
            </button>
          </div>
        </div>

        {/* Templates List */}
        <div className="space-y-4">
          {filteredTemplates.length === 0 ? (
            <Card className="p-8">
              <div className="text-center text-gray-500">
                <Calendar className="h-12 w-12 mx-auto mb-3 text-gray-400" />
                <p>
                  {searchQuery || categoryFilter !== "all"
                    ? "No se encontraron templates con los filtros aplicados"
                    : "No hay templates creados"}
                </p>
              </div>
            </Card>
          ) : (
            filteredTemplates.map((template) => (
              <EventTemplateCard
                key={template.id}
                template={template}
                onEdit={handleEdit}
                onDelete={handleDelete}
              />
            ))
          )}
        </div>
      </div>

      {/* Form Modal */}
      {showForm && (
        <EventTemplateForm
          template={editingTemplate}
          onSubmit={handleSubmit}
          onCancel={handleCancel}
        />
      )}
    </div>
  );
}
