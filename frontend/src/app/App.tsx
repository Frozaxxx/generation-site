import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { CompaniesPage } from "@/pages/companies";
import { CompanyPage } from "@/pages/company";
import { NewCompanyPage } from "@/pages/company-new";
import { SitePage } from "@/pages/site";
import { SitesPage } from "@/pages/sites";
import { AppShell } from "@/widgets/app-shell";

export function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<Navigate to="/companies" replace />} />
          <Route path="/companies" element={<CompaniesPage />} />
          <Route path="/companies/new" element={<NewCompanyPage />} />
          <Route path="/companies/:companyId" element={<CompanyPage />} />
          <Route path="/sites" element={<SitesPage />} />
          <Route path="/sites/:siteId" element={<SitePage />} />
          <Route path="*" element={<Navigate to="/companies" replace />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  );
}
