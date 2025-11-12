import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { AuthProvider } from "./providers/AuthContext";
import { ProtectedRoute } from "./providers/ProtectedRoute";
import { HomePage } from "@/pages/home";
import HowItWorks from "@/pages/home/ui/HowItWorks";
import { TermsOfService, PrivacyPolicy } from "@/pages/legal";
import { SIIConnectionPage, CompanySetupPage } from "@/pages/onboarding";
import LoginPage from "@/pages/auth/ui/LoginPage";
import AdminDashboard from "@/features/admin/dashboard/pages/AdminDashboard";
import CompaniesTablePage from "@/features/admin/companies/pages/CompaniesTablePage";
import CompanyDetailPage from "@/features/admin/companies/pages/CompanyDetailPage";
import EventTemplatesPage from "@/features/admin/calendar/pages/EventTemplatesPage";
import NotificationTemplatesPage from "@/features/admin/notifications/pages/NotificationTemplatesPage";
import TaskManagerPage from "@/features/admin/tasks/pages/TaskManagerPage";
import "./styles/index.css";

// Configure React Query
// Cache Strategy: In-memory only (no persistence across page refreshes)
// - staleTime: Data considered fresh for 5 minutes
// - gcTime: Unused data garbage collected after 10 minutes
// - No localStorage persistence (data reloads on page refresh)
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
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
        <BrowserRouter>
          <Routes>
            {/* Public routes */}
            <Route path="/" element={<HomePage />} />
            <Route path="/como-funciona" element={<HowItWorks />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/terminos" element={<TermsOfService />} />
            <Route path="/privacidad" element={<PrivacyPolicy />} />

            {/* Onboarding routes - require auth but not full onboarding */}
            <Route path="/onboarding/sii" element={<ProtectedRoute><SIIConnectionPage /></ProtectedRoute>} />
            <Route path="/onboarding/setup" element={<ProtectedRoute><CompanySetupPage /></ProtectedRoute>} />

            {/* Admin routes - require auth */}
            <Route path="/admin" element={<ProtectedRoute><AdminDashboard /></ProtectedRoute>} />
            <Route path="/admin/companies" element={<ProtectedRoute><CompaniesTablePage /></ProtectedRoute>} />
            <Route path="/admin/company/:companyId" element={<ProtectedRoute><CompanyDetailPage /></ProtectedRoute>} />
            <Route path="/admin/event-templates" element={<ProtectedRoute><EventTemplatesPage /></ProtectedRoute>} />
            <Route path="/admin/notification-templates" element={<ProtectedRoute><NotificationTemplatesPage /></ProtectedRoute>} />
            <Route path="/admin/task-manager" element={<ProtectedRoute><TaskManagerPage /></ProtectedRoute>} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </StrictMode>
);
