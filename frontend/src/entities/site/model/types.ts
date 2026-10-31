export type SiteLanguage = "ru" | "de";
export type SiteStatus = "ready" | "failed_checks";

export interface SiteIssue {
  code: string;
  severity: "error" | "warning";
  path: string;
  message: string;
}

export interface SiteVersion {
  id: string;
  company_id: string;
  company_revision: number;
  number: number;
  language: SiteLanguage;
  theme: string;
  accent: string | null;
  status: SiteStatus;
  pages: string[];
  issues: SiteIssue[];
  cost_usd: number;
  requests: number;
  reused_from: string | null;
  brand_name: string;
  domain: string;
  stale: boolean;
  created_at: string;
}

export interface SiteTheme {
  key: string;
  name: string;
  description: string;
  accent: string;
  background: string;
  ink: string;
}

export interface BuildSiteInput {
  language: SiteLanguage;
  theme: string;
  accent: string | null;
  reuse_texts: boolean;
  model: string | null;
}

export const LANGUAGE_LABELS: Record<SiteLanguage, string> = { ru: "Русский", de: "Немецкий" };

export const PAGE_LABELS: Record<string, string> = {
  "index.html": "Главная",
  "product.html": "Продукт",
  "company.html": "Компания и контакты",
};
