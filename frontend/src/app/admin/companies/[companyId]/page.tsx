"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import type { CompanyDetail } from "@/services/admin/companies.service";
import { CompanyHeader } from "./components/CompanyHeader";
import { CompanyStats } from "./components/CompanyStats";
import { CompanySyncActions } from "./components/CompanySyncActions";
import { CompanyContactInfo } from "./components/CompanyContactInfo";
import { CompanyDates } from "./components/CompanyDates";
import { CompanyUsersList } from "./components/CompanyUsersList";

export default function CompanyDetailPage() {
  const router = useRouter();
  const params = useParams();
  const companyId = params?.companyId as string;

  const [company, setCompany] = useState<CompanyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Tab state
  const [activeTab, setActiveTab] = useState<"overview" | "users" | "sync">("overview");

  useEffect(() => {
    if (companyId) {
      fetchCompanyDetail();
    }
  }, [companyId]);

  const fetchCompanyDetail = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/admin/companies/${companyId}`);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to fetch company");
      }

      const { data } = await response.json();
      setCompany(data);
    } catch (err) {
      console.error("Error fetching company:", err);
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando detalles...</p>
        </div>
      </div>
    );
  }

  if (error || !company) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="p-6 max-w-md">
          <div className="text-center">
            <div className="text-red-500 text-5xl mb-4">⚠️</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Error</h2>
            <p className="text-gray-600 mb-4">{error || "Empresa no encontrada"}</p>
            <Button onClick={() => router.push("/admin")} variant="outline">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Volver al listado
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <CompanyHeader
        company={company}
        onBack={() => router.push("/admin")}
      />

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex gap-6">
            <button
              onClick={() => setActiveTab("overview")}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === "overview"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              Vista General
            </button>
            <button
              onClick={() => setActiveTab("sync")}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === "sync"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              Sincronización
            </button>
            <button
              onClick={() => setActiveTab("users")}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === "users"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              <div className="flex items-center gap-2">
                <span>Usuarios y Sesiones</span>
                <Badge variant="outline" className="text-xs">
                  {company.users_count || 0}
                </Badge>
              </div>
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === "overview" ? (
          <div className="space-y-6">
            {/* Stats */}
            <CompanyStats company={company} />

            {/* Grid for Contact and Dates */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Contact Information */}
              <CompanyContactInfo company={company} />

              {/* Dates */}
              <CompanyDates company={company} />
            </div>
          </div>
        ) : activeTab === "sync" ? (
          /* Sync Tab */
          <div className="space-y-6">
            <CompanySyncActions companyId={companyId} />
          </div>
        ) : (
          /* Users Tab */
          <CompanyUsersList company={company} />
        )}
      </div>
    </div>
  );
}
