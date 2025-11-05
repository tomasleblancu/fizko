import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { AuthProvider } from "./providers/AuthContext";
import { ProtectedRoute } from "./providers/ProtectedRoute";
import { DashboardCacheProvider } from "./providers/DashboardCacheContext";
import { HomePage } from "@/pages/home";
import { TermsOfService, PrivacyPolicy } from "@/pages/legal";
import CompaniesListPage from "@/features/admin/companies/pages/CompaniesListPage";
import CompanyDetailPage from "@/features/admin/companies/pages/CompanyDetailPage";
import EventTemplatesPage from "@/features/admin/calendar/pages/EventTemplatesPage";
import NotificationTemplatesPage from "@/features/admin/notifications/pages/NotificationTemplatesPage";
import TaskManagerPage from "@/features/admin/tasks/pages/TaskManagerPage";
import "./styles/index.css";

// Configure React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes - same as custom cache
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const container = document.getElementById("root");
if (!container) {
  throw new Error("Root element with id 'root' not found");
}

createRoot(container).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <DashboardCacheProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/terminos" element={<TermsOfService />} />
              <Route path="/privacidad" element={<PrivacyPolicy />} />
              <Route path="/admin" element={<ProtectedRoute><CompaniesListPage /></ProtectedRoute>} />
              <Route path="/admin/company/:companyId" element={<ProtectedRoute><CompanyDetailPage /></ProtectedRoute>} />
              <Route path="/admin/event-templates" element={<ProtectedRoute><EventTemplatesPage /></ProtectedRoute>} />
              <Route path="/admin/notification-templates" element={<ProtectedRoute><NotificationTemplatesPage /></ProtectedRoute>} />
              <Route path="/admin/task-manager" element={<ProtectedRoute><TaskManagerPage /></ProtectedRoute>} />
            </Routes>
          </BrowserRouter>
        </DashboardCacheProvider>
      </AuthProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </StrictMode>
);
