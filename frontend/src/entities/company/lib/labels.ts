import type { CompanyScale, CompanyStatus, TeamRole } from "../model/types";

export const SCALE_LABELS: Record<CompanyScale, string> = {
  small: "Небольшая",
  medium: "Средняя",
};

export const STATUS_LABELS: Record<CompanyStatus, string> = {
  draft: "Черновик",
  approved: "Утверждена",
};

export const ROLE_LABELS: Record<TeamRole, string> = {
  ceo: "Руководитель",
  department_head: "Руководитель отдела",
  specialist: "Специалист",
};

/** Названия разделов карточки для путей из проверок (`product.limitations[1]`). */
const SECTION_LABELS: Record<string, string> = {
  brand: "Бренд",
  contacts: "Контакты",
  history: "История",
  audience: "Аудитория",
  product: "Продукт",
  team: "Команда",
  faq: "FAQ",
  params: "Параметры",
};

export function sectionOf(path: string): string {
  return path.split(/[.[]/)[0] ?? "";
}

export function sectionLabel(path: string): string {
  return SECTION_LABELS[sectionOf(path)] ?? path;
}
