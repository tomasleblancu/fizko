"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createBrowserClient } from "@supabase/ssr";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Building2, Search, Users, Activity, LogOut, Calendar } from "lucide-react";
import type { CompanyWithStats } from "@/services/admin/companies.service";

export default function AdminPage() {
  const router = useRouter();
  const [companies, setCompanies] = useState<CompanyWithStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const supabase = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
  );

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/admin/companies");

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to fetch companies");
      }

      const { data } = await response.json();
      setCompanies(data);
    } catch (err) {
      console.error("Error fetching companies:", err);
      setError(err instanceof Error ? err.message : "Unknown error");
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

  const filteredCompanies = companies.filter((company) => {
    const query = searchQuery.toLowerCase();
    return (
      company.rut.toLowerCase().includes(query) ||
      company.business_name?.toLowerCase().includes(query) ||
      company.trade_name?.toLowerCase().includes(query) ||
      company.email?.toLowerCase().includes(query)
    );
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("es-CL", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando empresas...</p>
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
            <p className="text-gray-600">{error}</p>
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
              <div className="p-2 bg-blue-100 rounded-lg">
                <Building2 className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Panel de Administración
                </h1>
                <p className="text-sm text-gray-500">
                  Gestión de empresas en Fizko
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="outline" className="text-sm">
                {companies.length} {companies.length === 1 ? "empresa" : "empresas"}
              </Badge>
              <button
                onClick={() => router.push("/admin/event-templates")}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                aria-label="Templates de Eventos"
              >
                <Calendar className="h-4 w-4" />
                <span className="hidden sm:inline">Templates</span>
              </button>
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
        {/* Search */}
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <Input
              type="text"
              placeholder="Buscar por RUT, razón social, nombre de fantasía o email..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 w-full"
            />
          </div>
        </div>

        {/* Companies List */}
        <div className="grid gap-4">
          {filteredCompanies.length === 0 ? (
            <Card className="p-8">
              <div className="text-center text-gray-500">
                <Building2 className="h-12 w-12 mx-auto mb-3 text-gray-400" />
                <p>No se encontraron empresas</p>
              </div>
            </Card>
          ) : (
            filteredCompanies.map((company) => (
              <Card
                key={company.id}
                className="p-6 hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => router.push(`/admin/companies/${company.id}`)}
              >
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  {/* Company Info */}
                  <div className="md:col-span-2">
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-gray-100 rounded-lg">
                        <Building2 className="h-5 w-5 text-gray-600" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900">
                          {company.business_name || company.trade_name || "Sin nombre"}
                        </h3>
                        {company.trade_name && company.business_name !== company.trade_name && (
                          <p className="text-sm text-gray-600">
                            {company.trade_name}
                          </p>
                        )}
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="outline" className="text-xs">
                            {company.rut}
                          </Badge>
                        </div>
                        {company.email && (
                          <p className="text-sm text-gray-500 mt-1">
                            {company.email}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2 text-sm">
                      <Users className="h-4 w-4 text-gray-400" />
                      <span className="text-gray-600">
                        {company.users_count || 0} {company.users_count === 1 ? "usuario" : "usuarios"}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <Activity className="h-4 w-4 text-gray-400" />
                      <span className="text-gray-600">
                        {company.sessions_count || 0} {company.sessions_count === 1 ? "sesión" : "sesiones"}
                      </span>
                    </div>
                  </div>

                  {/* Dates */}
                  <div className="flex flex-col gap-1 text-sm text-gray-500">
                    <div>
                      <span className="font-medium">Creada:</span>{" "}
                      {formatDate(company.created_at)}
                    </div>
                    <div>
                      <span className="font-medium">Actualizada:</span>{" "}
                      {formatDate(company.updated_at)}
                    </div>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
