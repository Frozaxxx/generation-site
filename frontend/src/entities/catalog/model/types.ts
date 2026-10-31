export interface CatalogOption {
  key: string;
  label: string;
  description: string | null;
}

export interface Catalog {
  countries: CatalogOption[];
  directions: CatalogOption[];
  service_types: Record<string, CatalogOption[]>;
  scales: CatalogOption[];
  models: CatalogOption[];
  default_model: string;
}

export interface ModelOption {
  id: string;
  prompt_per_mtok: number | null;
  completion_per_mtok: number | null;
}

export interface LLMStatus {
  configured: boolean;
  default_text_model: string;
  image_model: string;
  operation_budget_usd: number;
  max_retries: number;
  models: ModelOption[];
}
