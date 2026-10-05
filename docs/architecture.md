# Proposed Architecture — SARMAAN e-Playbook

Second Phase-1 deliverable, written after `prototype-analysis.md`. This restates the target architecture
from the master prompt in concrete terms against what the prototype actually needs to become, and calls out
the decisions that block later phases.

## 1. System overview

```
Admin Portal (React/TS) ──┐
                           ├── FastAPI (Auth, Content, Releases, Sync, AI/RAG, Analytics, Audit, Storage)
Android App (React+Capacitor) ┘        │
                                        ├── PostgreSQL (+ pgvector) — source of truth
                                        └── Object storage (S3-compatible / MinIO dev) — media + release packages
```

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy 2.x, Pydantic, Alembic migrations, PostgreSQL, JWT auth
  with Argon2/bcrypt password hashing, RBAC via the role list in the master prompt (§6).
- **Mobile**: React + TypeScript + Vite + Tailwind + React Router + TanStack Query + Zustand, wrapped by
  Capacitor for Android, with a local SQLite store, a local file cache for media/video, a local vector index
  + quantized LLM runtime for offline AI, and a sync queue.
- **Admin**: React + TypeScript + Vite + Tailwind + React Router + TanStack Query + React Hook Form + Zod +
  Recharts, talking to the same FastAPI backend.
- **AI**: hybrid — server-side RAG (FastAPI → pgvector → hosted LLM) when online; on-device RAG (local
  embeddings → local vector search → local quantized LLM) when offline. Both paths must answer only from
  approved content and must produce a "not found in approved materials" fallback plus a logged, unanswered
  question — matching the prototype's `kb` behavior but with real retrieval instead of substring matching.

## 2. Content pipeline

Flipbook PDF + prototype module bodies → `scripts/import_prototype_content.py` seeds `modules`,
`module_translations`, `content_sections`, and `media_assets` (extracting the prototype's inline base64
images to real files under `content/media/`) → reviewed through the governance workflow (Draft → Programme
review → Localisation review → Data-protection review → Technical QA → Publish, matching the prototype's
static pill chain but as real workflow state) → `scripts/build_release.py` produces a versioned package
(modules + media + videos + search index + RAG index + AI model reference) → `scripts/build_rag_index.py`
chunks and embeds approved content into `pgvector`, and separately into an offline-compatible index shipped
inside the release package.

## 3. Offline-first contract (mobile)

`CONNECT ONCE → DOWNLOAD REQUIRED CONTENT → WORK FULLY OFFLINE → SYNCHRONIZE WHEN CONNECTED`, matching the
master prompt's core principle and the SRS's "offline-first core, selective online services" conclusion.
Concretely:

- Offline, always: module navigation/reading, images, job aids, local search, downloaded videos and audio,
  read-aloud (on-device TTS engine, not just the browser's `speechSynthesis`), offline AI/RAG, progress
  tracking, language selection, settings.
- Online, as needed: initial login, initial/incremental content download, content updates, sync, cloud
  analytics, administration, optional server-side AI.
- Every "is this real" claim from the prototype (fake progress bars, non-functional video player, stubbed
  chat) must be replaced with an implementation that satisfies the master prompt's §93–95 critical rules:
  no simulated downloads, no offline AI that is just cached cloud responses, no offline video that is just a
  URL. Downloaded video must play with Wi-Fi, mobile data, and the backend all off.

## 4. Data model

Follow the master prompt's schema (§6–9: users/roles/languages/campaigns/modules/module_translations/
content_sections/media_assets/videos/user_module_progress, extended in the untruncated portion of that
document with releases, ai_question_log, analytics, and audit tables). The prototype-analysis mapping in
§9 of that document is the concrete "prototype concept → table" crosswalk; use it directly rather than
re-deriving the schema from the HTML a second time.

## 5. What must NOT be carried over from the prototype as-is

- Hardcoded numbers/strings everywhere (device counts, adoption %, team IDs, release notes) → must be
  computed from real data or stored as real config.
- The dev-only "why this screen" annotation panel and the connectivity-simulation toggle are review
  scaffolding for the prototype only; they are not product UI and should not be built into the shipped app
  (though a debug/QA build might keep a connectivity override for testing).
- The AI `kb` array's exact answers may be reused as seed content/test fixtures for the RAG index, but the
  matching mechanism (naive substring match) must not be the production implementation.

## 6. Decisions

**Resolved (confirmed by the product owner, superseding the SRS §27 ambiguity):**

- **Offline video is in MVP scope.** Videos must download to the device and play from a local file via
  `video_player` — never a bare remote URL relabeled as "offline" (master prompt §95 still applies in full).
  This overrides the SRS's "online-only to keep the app small" framing; the master prompt's Phase 9 treatment
  of offline video as mainline was correct.
- **AI/RAG assistant is in MVP scope**, both online (server RAG) and offline (on-device RAG + local
  quantized LLM), per the master prompt's hybrid AI architecture (§25–§38). Not deferred to Phase 2/scale.
- **Platform target is Android + iOS**, not Android-only. This is why the mobile app uses Flutter rather than
  a React Native/Capacitor-Android-only approach — Flutter's single codebase covers both targets, and Phase 2
  scaffolding already added the `mobile/android/` project; an `mobile/ios/` project needs to be added
  alongside it (via `flutter create --platforms=ios .` once run on a machine with Xcode, since iOS project
  generation and builds require macOS tooling this Linux dev sandbox does not have).

**Still open — do not invent answers, surface and wait for sign-off:** final product name/branding;
confirmed MVP language set beyond English (Hausa/Fulfulde/Kanuri are "Beta" in the prototype); whether users
authenticate against an existing organisational identity source or a new one; target Android OS/device range
and minimum iOS version; final video hosting/storage provider; exact AI/RAG technology choice (embedding
model, offline LLM runtime/model); who holds each governance-workflow approval role; whether content releases
can ship independently of app releases; privacy/consent/analytics/retention rules; and budget/timeline
(₦50m vs. ₦15m, no confirmed production date).

## 7. Immediate next steps (Phase 2 onward, per the master prompt's phase sequence)

1. Confirm the decisions in §6 above with the programme/product owner — several materially change scope
   (offline video in particular).
2. Stand up the repository skeleton (`backend/`, `mobile/`, `admin/`, `content/`, `scripts/`, `docker-compose.yml`).
3. Implement the PostgreSQL schema + Alembic migrations + seed data (Phase 3).
4. Implement auth/RBAC (Phase 4), then the Admin Portal shell (Phase 5), then run
   `scripts/import_prototype_content.py` to migrate the six modules, four videos, and embedded photos out of
   the prototype and into real rows/files (Phase 6).

This is a genuinely large, multi-week build (mobile + admin + backend + offline AI/video + sync +
governance). It should proceed phase-by-phase, with working, testable output at the end of each phase, per
the master prompt's §99 coding-agent behaviour rules — not as a single pass.
