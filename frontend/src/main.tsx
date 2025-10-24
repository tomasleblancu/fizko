import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { DashboardCacheProvider } from "./contexts/DashboardCacheContext";
import Root from "./pages/Root";
import AdminCompaniesView from "./pages/AdminCompaniesView";
import AdminCompanyView from "./pages/AdminCompanyView";
import "./index.css";

const container = document.getElementById("root");
if (!container) {
  throw new Error("Root element with id 'root' not found");
}

createRoot(container).render(
  // Note: StrictMode removed to avoid double-fetching in development
  // This is NOT recommended for production apps as it helps catch bugs
  // Only remove if you understand the trade-offs
  <AuthProvider>
    <DashboardCacheProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Root />} />
          <Route path="/admin" element={<AdminCompaniesView />} />
          <Route path="/admin/company/:companyId" element={<AdminCompanyView />} />
        </Routes>
      </BrowserRouter>
    </DashboardCacheProvider>
  </AuthProvider>
);
