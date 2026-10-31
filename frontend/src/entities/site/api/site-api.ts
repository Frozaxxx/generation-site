import { jsonBody, requestJson } from "@/shared/api";

import type { Job } from "@/entities/job/@x/company";
import type { BuildSiteInput, SiteTheme, SiteVersion } from "../model/types";

export function fetchCompanySites(companyId: string): Promise<SiteVersion[]> {
  return requestJson(`/companies/${companyId}/sites`);
}

export function fetchSite(siteId: string): Promise<SiteVersion> {
  return requestJson(`/sites/${siteId}`);
}

export function fetchThemes(): Promise<SiteTheme[]> {
  return requestJson("/sites/themes");
}

export function buildSite(companyId: string, input: BuildSiteInput): Promise<Job> {
  return requestJson(`/companies/${companyId}/sites`, jsonBody(input));
}

export function deleteSite(siteId: string): Promise<void> {
  return requestJson(`/sites/${siteId}`, { method: "DELETE" });
}

export function siteDownloadUrl(siteId: string): string {
  return `/api/v1/sites/${siteId}/download`;
}

export function sitePreviewUrl(siteId: string, page = "index.html"): string {
  return `/preview/${siteId}/${page}`;
}
