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
  | "LIST"
  | "TRUE_FALSE";
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

export type LearnerRole = "CDD" | "HEALTH_WORKER" | "LOGISTICIAN" | "MONITOR_SUPERVISOR" | "OTHER";
export type ModuleAudience = "GENERAL" | "ROLE_SPECIFIC";
export type QuestionUsage = "BOTH" | "PRE" | "POST";

export interface Module {
  id: string;
  module_code: string;
  module_number: number;
  title: string;
  description: string | null;
  status: ModuleStatus;
  sort_order: number;
  audience: ModuleAudience;
  learner_roles: LearnerRole[];
  audience_needs_review: boolean;
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
  learner_role: LearnerRole | null;
  learner_role_needs_review: boolean;
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
  deactivated_at?: string | null;
  deactivation_reason?: string | null;
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
  usage: QuestionUsage;
}

export interface QuizSummaryRow {
  module_id: string;
  questions: number;
  pass_mark: number;
  attempts: number;
  learners_passed: number;
  pre_test_questions: number;
  post_test_questions: number;
  pre_test_attempts: number;
  post_test_attempts: number;
  warning: string | null;
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

// ---------- Learner roles, audiences and pre/post tests ----------

export interface LearnerPerson {
  user_id: string;
  username: string;
  full_name: string;
  learner_role: LearnerRole | null;
  team_code: string | null;
  state: string | null;
  lga: string | null;
  session: string | null;
}

export interface LearningReview {
  /** A 100% pre-test is auto-approved by a post-test at or above this percentage. */
  auto_approve_percent: number;
  learner_roles: { value: LearnerRole; label: string }[];
  modules: {
    id: string;
    module_code: string;
    title: string;
    status: ModuleStatus;
    audience: ModuleAudience;
    learner_roles: LearnerRole[];
    needs_review: boolean;
  }[];
  users_needing_review: (LearnerPerson & { role: string; email: string; reason: string })[];
}

export interface TestReportRow extends LearnerPerson {
  module_code: string;
  module_title: string;
  status: string;
  pre_test_score: number | null;
  pre_test_correct: string | null;
  pre_test_taken_at: string | null;
  post_test_attempts: number;
  post_test_best_score: number | null;
  post_test_latest_score: number | null;
  post_test_latest_at: string | null;
  pass_mark: number;
  met_both_rules: boolean;
  auto_approved: boolean;
  attempts_not_counted: number;
  completed_at: string | null;
  // since 2026-11: the inline module quiz and the active time
  learner_group: string;
  curriculum: string;
  quiz_statements: number;
  quiz_attempts: number;
  quiz_passed: boolean;
  quiz_passed_at: string | null;
  quiz_latest_score: number | null;
  seconds_spent: number;
  min_seconds: number;
}

/** One learner's General pre/post test (GET /learning/general-report). */
export interface GeneralReportRow extends LearnerPerson {
  learner_group: string;
  modules_total: number;
  modules_completed: number;
  seconds_spent_total: number;
  pre_test_points: number | null;
  pre_test_total: number | null;
  pre_test_percent: number | null;
  pre_test_taken_at: string | null;
  post_test_points: number | null;
  post_test_total: number | null;
  post_test_percent: number | null;
  post_test_taken_at: string | null;
  change_points: number | null;
  change_percent: number | null;
  attempts_not_counted: number;
}

/** One mobile-app interface string and its translation in the chosen language (GET /app-strings). */
export interface AppStringItem {
  key: string;
  note: string;
  placeholders: string[];
  english: string;
  english_one: string | null;
  plural: boolean;
  translation_id: string | null;
  text: string | null;
  text_one: string | null;
  status: ContentReviewStatus | null;
  needs_update: boolean;
  published_text: string | null;
  published_text_one: string | null;
  published_at: string | null;
  edited_by: string | null;
  edited_by_id: string | null;
  edited_at: string | null;
}

export interface AppStringList {
  language: string;
  total: number;
  items: AppStringItem[];
}

export interface AppStringLanguageStats {
  language: string;
  name: string;
  total: number;
  translated: number;
  published: number;
  in_review: number;
  needs_update: number;
  translated_percent: number;
  published_percent: number;
}

export interface AppStringProblem {
  row?: number;
  id?: string;
  key: string | null;
  problem: string;
}

export type SupportContactType = "PHONE" | "SMS" | "EMAIL" | "WHATSAPP" | "LINK";

/** A Support deck row (GET /support-contacts). Empty `audience` = every learner. */
export interface SupportContact {
  id: string;
  type: SupportContactType;
  label: string;
  value: string;
  whatsapp_message: string | null;
  email_subject: string | null;
  include_app_version: boolean;
  availability: string | null;
  languages: string | null;
  audience: LearnerRole[];
  is_active: boolean;
  display_order: number;
  created_by: string | null;
  updated_by: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export type ToolItemType = "DOCUMENT" | "SPREADSHEET" | "PRESENTATION" | "PDF" | "IMAGE" | "VIDEO_LINK" | "WEBSITE" | "FORM" | "OTHER";

/** A Tools repository module (GET /tools/modules): links only, separate from training. */
export interface ToolModule {
  id: string;
  title: string;
  description: string | null;
  audience: ModuleAudience;
  learner_roles: LearnerRole[];
  is_active: boolean;
  display_order: number;
  item_count: number;
  updated_by: string | null;
  updated_at: string | null;
}

/** A link in a Tools module (GET /tools/items). Empty `audience` = everyone the module is for. */
export interface ToolItem {
  id: string;
  tool_module_id: string;
  title: string;
  description: string | null;
  type: ToolItemType;
  url: string;
  host: string | null;
  category: string | null;
  languages: string | null;
  audience: LearnerRole[];
  is_active: boolean;
  last_reviewed: string | null;
  display_order: number;
  duplicates: { id: string; title: string }[];
  created_by: string | null;
  updated_by: string | null;
  updated_at: string | null;
}
