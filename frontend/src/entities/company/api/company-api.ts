import { jsonBody, requestJson, type Page } from "@/shared/api";

import type { Job } from "@/entities/job/@x/company";
import type {
  Company,
  CompanyListItem,
  CompanyProfile,
  CompanyStatus,
  GenerateCompanyInput,
} from "../model/types";

export interface CompanyFilters {
  search?: string;
  status?: CompanyStatus;
  page?: number;
}

export function fetchCompanies(filters: CompanyFilters = {}): Promise<Page<CompanyListItem>> {
  const params = new URLSearchParams({ size: "50" });
  if (filters.search) params.set("search", filters.search);
  if (filters.status) params.set("status", filters.status);
  if (filters.page) params.set("page", String(filters.page));
  return requestJson(`/companies?${params}`);
}

export function fetchCompany(id: string): Promise<Company> {
  return requestJson(`/companies/${id}`);
}

export function saveProfile(id: string, profile: CompanyProfile, revision: number): Promise<Company> {
  return requestJson(`/companies/${id}/profile`, {
    method: "PUT",
    body: JSON.stringify({ profile, revision }),
  });
}

export function approveCompany(id: string): Promise<Company> {
  return requestJson(`/companies/${id}/approve`, { method: "POST" });
}

export function reviewCompany(id: string): Promise<Company> {
  return requestJson(`/companies/${id}/review`, jsonBody({}));
}

export function regeneratePhoto(id: string, personId: string): Promise<Company> {
  return requestJson(`/companies/${id}/team/${personId}/photo`, jsonBody({}));
}

export function deleteCompany(id: string): Promise<void> {
  return requestJson(`/companies/${id}`, { method: "DELETE" });
}

export function generateCompany(input: GenerateCompanyInput): Promise<Job> {
  return requestJson("/companies/generate", jsonBody(input));
}

export function companyExportUrl(id: string): string {
  return `/api/v1/companies/${id}/export`;
}

export function photoUrl(companyId: string, file: string, version?: string): string {
  const suffix = version ? `?v=${encodeURIComponent(version)}` : "";
  return `/media/companies/${companyId}/${file}${suffix}`;
}
