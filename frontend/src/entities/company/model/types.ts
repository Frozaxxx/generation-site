export type CompanyScale = "small" | "medium";
export type CompanyStatus = "draft" | "approved";
export type Gender = "female" | "male";
export type TeamRole = "ceo" | "department_head" | "specialist";
export type IssueSeverity = "error" | "warning";

export interface Brand {
  name: string;
  legal_form: string;
  legal_name: string;
  tagline: string;
  domain: string;
}

export interface Address {
  street: string;
  house_number: string;
  postal_code: string;
  city: string;
  district: string | null;
  state: string;
  country_code: string;
}

export interface Contacts {
  address: Address;
  city_key: string;
  phone: string;
  phone_display: string;
  email: string;
  office_hours: string;
}

export interface TitledText {
  title: string;
  description: string;
}

export interface Milestone extends TitledText {
  year: number;
}

export interface History {
  founded_year: number;
  employees: number;
  founding_story: string;
  specialization: string;
  milestones: Milestone[];
}

export interface Audience {
  segments: { name: string; description: string }[];
  client_problem: string;
}

export interface Product {
  name: string;
  summary: string;
  inputs: string[];
  process: TitledText[];
  outputs: string[];
  limitations: string[];
  benefits: TitledText[];
  delivery: string;
}

export interface Photo {
  file: string;
  alt: string;
}

export interface Person {
  id: string;
  first_name: string;
  last_name: string;
  gender: Gender;
  age: number;
  role: TeamRole;
  position: string;
  department: string | null;
  bio: string;
  experience: string[];
  education: string;
  photo: Photo | null;
}

export interface FaqItem {
  question: string;
  answer: string;
}

export interface CompanyProfile {
  schema_version: number;
  content_language: string;
  brand: Brand;
  contacts: Contacts;
  history: History;
  audience: Audience;
  product: Product;
  team: Person[];
  faq: FaqItem[];
}

export interface Issue {
  code: string;
  severity: IssueSeverity;
  path: string;
  message: string;
}

export interface GenerationParams {
  brand_name: string | null;
  country: string;
  direction: string;
  service_type: string;
  scale: CompanyScale;
  model: string;
  randomized: string[];
  custom_direction: string | null;
  custom_service: string | null;
}

export interface GenerationInfo {
  model: string;
  cost_usd: number;
  input_tokens: number;
  output_tokens: number;
  requests: number;
  duration_seconds: number;
  concept: Record<string, string>;
  review: { path: string; severity: IssueSeverity; message: string }[];
  review_revision: number | null;
  warnings: string[];
}

export interface Company {
  id: string;
  status: CompanyStatus;
  revision: number;
  params: GenerationParams;
  profile: CompanyProfile;
  generation: GenerationInfo | null;
  issues: Issue[];
  created_at: string;
  updated_at: string;
  approved_at: string | null;
}

export interface CompanyListItem {
  id: string;
  brand_name: string;
  legal_name: string;
  city: string;
  service_type: string;
  service_label: string;
  scale: CompanyScale;
  status: CompanyStatus;
  revision: number;
  team_size: number;
  sites_count: number;
  created_at: string;
  updated_at: string;
}

export interface GenerateCompanyInput {
  brand_name: string | null;
  country: string | null;
  direction: string | null;
  service_type: string | null;
  custom_direction: string | null;
  custom_service: string | null;
  scale: CompanyScale | null;
  model: string | null;
  with_photos: boolean;
  budget_usd: number | null;
}
