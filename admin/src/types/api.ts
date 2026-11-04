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

// ---------- Phase 13: audit + usage ----------

export interface AuditEntry {
  id: string;
  created_at: string;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  details: Record<string, unknown>;
  ip_address: string | null;
  user_id: string | null;
  username: string | null;
  user_role: string | null;
}

export interface AuditPage {
  total: number;
  limit: number;
  offset: number;
  items: AuditEntry[];
}

export interface UsageReport {
  days: number;
  since: string;
  devices: { active_1d: number; active_7d: number; active_30d: number };
  daily: { date: string; events: number; devices: number }[];
  events_by_type: { event_type: string; count: number }[];
  modules: {
    module_id: string;
    module_code: string;
    title: string;
    opens: number;
    completions: number;
    cdds_started: number;
    cdds_completed: number;
  }[];
  videos: { video_id: string; title: string; opens: number; completions: number; playback_failures: number }[];
  technical: {
    download_failures: number;
    sync_failures: number;
    app_errors: number;
    storage_errors: number;
    playback_failures: number;
  };
  current_release_code: string | null;
  current_release_devices: number;
  release_adoption_percent: number | null;
  release_adoption: { release_code: string; devices: number }[];
  languages: { language_code: string; count: number }[];
  note: string;
}

export interface QuestionCount {
  question: string;
  count: number;
  last_asked: string;
}

export interface QuestionsReport {
  days: number;
  total: number;
  matched: number;
  unmatched: number;
  answer_rate_percent: number | null;
  top_unanswered: QuestionCount[];
  top_answered: QuestionCount[];
}

// ---------- Videos (admin management) ----------

export type VideoStatus = "DRAFT" | "PUBLISHED" | "ARCHIVED";

export interface TrainingVideo {
  id: string;
  title: string;
  description: string | null;
  module_id: string | null;
  duration_seconds: number | null;
  file_size: number | null;
  checksum: string | null;
  language: string;
  offline_available: boolean;
  required_offline: boolean;
  status: VideoStatus;
  has_file: boolean;
}

// ---------- Users (SUPER_ADMIN) ----------

export interface ManagedUser {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  team_code: string | null;
  role: string;
  status: string;
  country_id: string | null;
  state_id: string | null;
  lga_id: string | null;
  ward_id: string | null;
  facility_id: string | null;
  country_name: string | null;
  state_name: string | null;
  lga_name: string | null;
  ward_name: string | null;
  facility_name: string | null;
  training_session_id: string | null;
  session_name: string | null;
  session_start_date: string | null;
  session_end_date: string | null;
  session_status: string | null;
  training_attempt: number;
  training_restarted_at: string | null;
  last_login_at: string | null;
  created_at: string;
}

export type BoundaryLevel = "COUNTRY" | "STATE" | "LGA" | "WARD" | "FACILITY";

export interface Boundary {
  id: string;
  level: BoundaryLevel;
  name: string;
  code: string | null;
  parent_id: string | null;
}

export type ReportRow = Record<string, string | number | null>;

// ---------- Quiz ----------

export type QuestionType =
  | "MULTIPLE_CHOICE"
  | "TRUE_FALSE"
  | "MULTIPLE_SELECT"
  | "MATCHING"
  | "ORDERING"
  | "IMAGE_CHOICE"
  | "NUMERIC";

export interface QuizQuestionRow {
  id: string;
  module_id: string;
  question_type: QuestionType;
  prompt: string;
  content: Record<string, unknown>;
  explanation: string | null;
  sort_order: number;
  is_active: boolean;
}

export interface QuizSummaryRow {
  module_id: string;
  questions: number;
  pass_mark: number;
  attempts: number;
  learners_passed: number;
}

export interface MediaItem {
  id: string;
  asset_type: string;
  filename: string;
  mime_type: string;
  alt: string | null;
}

export interface TrainingSession {
  id: string;
  name: string;
  description: string | null;
  start_date: string;
  end_date: string;
  status: "UPCOMING" | "ONGOING" | "ENDED";
  user_count: number;
  created_at: string;
}

export interface ConsentText {
  language: string;
  title: string;
  body: string;
  usage_label: string;
  button_label: string;
  version: number;
  updated_at: string | null;
  outdated: boolean;
}

export type ReferenceStatus = "DRAFT" | "APPROVED" | "ARCHIVED";

export interface ReferenceDocument {
  id: string;
  title: string;
  description: string | null;
  filename: string;
  mime_type: string;
  file_size: number;
  language: string;
  status: ReferenceStatus;
  passage_count: number;
  uploaded_by: string | null;
  approved_by: string | null;
  approved_at: string | null;
  created_at: string | null;
}

export interface ReferencePassage {
  position: number;
  heading: string | null;
  text: string;
}

export type FaqStatus = "DRAFT" | "APPROVED" | "ARCHIVED";

export interface FaqEntry {
  id: string;
  question: string;
  alternates: string | null;
  answer: string;
  module_id: string;
  module_code: string | null;
  module_title: string | null;
  language: string;
  status: FaqStatus;
  source_question: string | null;
  created_by: string | null;
  approved_by: string | null;
  approved_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}
