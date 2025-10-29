import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { AuthProvider } from "./contexts/AuthContext";
import { DashboardCacheProvider } from "./contexts/DashboardCacheContext";
import Root from "./pages/Root";
import AdminCompaniesView from "./pages/AdminCompaniesView";
import AdminCompanyView from "./pages/AdminCompanyView";
import AdminEventTypes from "./pages/AdminEventTypes";
import AdminNotificationTemplates from "./pages/AdminNotificationTemplates";
import TermsOfService from "./pages/TermsOfService";
import PrivacyPolicy from "./pages/PrivacyPolicy";
import "./index.css";

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
  // Note: StrictMode removed to avoid double-fetching in development
  // This is NOT recommended for production apps as it helps catch bugs
  // Only remove if you understand the trade-offs
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <DashboardCacheProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Root />} />
            <Route path="/terminos" element={<TermsOfService />} />
            <Route path="/privacidad" element={<PrivacyPolicy />} />
            <Route path="/admin" element={<AdminCompaniesView />} />
            <Route path="/admin/company/:companyId" element={<AdminCompanyView />} />
            <Route path="/admin/event-templates" element={<AdminEventTypes />} />
            <Route path="/admin/notification-templates" element={<AdminNotificationTemplates />} />
          </Routes>
        </BrowserRouter>
      </DashboardCacheProvider>
    </AuthProvider>
    <ReactQueryDevtools initialIsOpen={false} />
  </QueryClientProvider>
);
