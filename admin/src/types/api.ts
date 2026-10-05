export type ModuleStatus = "DRAFT" | "PUBLISHED" | "ARCHIVED";
export type ContentReviewStatus =
  | "DRAFT"
  | "PROGRAMME_REVIEW"
  | "LOCALISATION_REVIEW"
  | "TECHNICAL_QA"
  | "PUBLISHED"
  | "REJECTED";
export type ContentType =
  | "TEXT"
  | "HEADING"
  | "IMAGE"
  | "TABLE"
  | "CALLOUT"
  | "WARNING"
  | "JOB_AID"
  | "VIDEO"
  | "AUDIO"
  | "LIST";
export type LanguageStatus = "ACTIVE" | "BETA" | "IN_REVIEW" | "NOT_STARTED";
export type ReleaseStatus = "DRAFT" | "IN_REVIEW" | "APPROVED" | "PUBLISHED" | "ROLLED_BACK";
export type RoleName =
  | "SUPER_ADMIN"
  | "CONTENT_ADMIN"
  | "PROGRAM_REVIEWER"
  | "LOCALISATION_REVIEWER"
  | "TECHNICAL_REVIEWER"
  | "SUPERVISOR"
  | "CDD"
  | "READ_ONLY";

export interface Module {
  id: string;
  module_code: string;
  module_number: number;
  title: string;
  description: string | null;
  status: ModuleStatus;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface ModuleTranslation {
  id: string;
  module_id: string;
  language_id: string;
  title: string;
  description: string | null;
  body: string | null;
  audio_text: string | null;
  status: ContentReviewStatus;
  reviewed_by: string | null;
  reviewed_at: string | null;
}

export interface ContentSection {
  id: string;
  module_id: string;
  section_number: number;
  title: string | null;
  content_type: ContentType;
  content: Record<string, unknown>;
  sort_order: number;
}

export interface Language {
  id: string;
  code: string;
  name: string;
  native_name: string;
  status: LanguageStatus;
  is_default: boolean;
  created_at: string;
}

export interface ContentRelease {
  id: string;
  release_code: string;
  campaign_id: string | null;
  version: string;
  description: string | null;
  mandatory: boolean;
  status: ReleaseStatus;
  package_size: number | null;
  checksum: string | null;
  created_by: string | null;
  approved_by: string | null;
  published_at: string | null;
  created_at: string;
}

export interface ModuleEngagement {
  module_id: string;
  module_code: string;
  title: string;
  opens: number;
  completions: number;
}

export interface LanguageUsage {
  language_code: string;
  count: number;
}

export interface Dashboard {
  active_devices_7d: number;
  published_modules: number;
  draft_modules: number;
  total_modules: number;
  ai_questions_total: number;
  ai_questions_unmatched: number;
  update_adoption_percent: number | null;
  module_engagement: ModuleEngagement[];
  language_usage: LanguageUsage[];
  download_failures_7d: number;
  sync_failures_7d: number;
}
