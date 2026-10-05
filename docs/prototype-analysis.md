# Prototype Analysis — SARMAAN e-Playbook

Source inspected: `sarmaan-eplaybook-prototype_1.html` (single-file HTML/CSS/JS prototype, ~1520 lines),
cross-checked against `Mobile_App_Requirements_and_System_Architecture_E_Playbook.docx` (SRS derived from the
26 Aug 2026 meeting transcript) and `Training_Flipbook_CDDs-Updated.pdf` (source content: AZM Modules 1–6).

This document is Phase 1 of the Master Development Prompt. It inventories what the prototype actually contains
so later phases can map it to a real database, API, and offline architecture without guessing.

---

## 1. Screen inventory (mobile client)

The prototype is a single-page app driven by `go(screenName)`, which toggles `.screen[data-screen="..."]`
elements and updates the bottom nav + a right-hand "why this screen" annotation panel (dev-only, not part of
the real product). Screens, in `data-screen` order:

| Screen | Purpose | Notes |
|---|---|---|
| `splash` | Loading splash | Loads whatever content package is already on disk; no network call implied |
| `language` | First-launch step 1/2 | Radio-style list: English (full content), Hausa/Fulfulde/Kanuri (each tagged "Beta") |
| `consent` | First-launch step 2/2 | Plain-language data notice; "Agree and download" vs "Skip for now (limited offline content)" |
| `downloading` | One-time content package download | Simulated progress bar (`setInterval`, random increments) against a hardcoded "6.4 MB" target |
| `home` | Dashboard | Greeting with hardcoded "CDD TEAM 0041"; tappable search (opens Modules, not a real search box); content-update banner; "Continue reading" card (hardcoded 62%); module grid; floating "Ask" button |
| `modules` | Module list | Renders all 6 modules from the in-memory `modules` array |
| `reader` | Module content reader | Renders `module.body` (raw HTML with embedded base64 photos), a read-aloud bar (Web Speech API), "mark as complete" button |
| `videoLib` | Video list | Renders the 4-item `videos` array; explicitly "streamed online only" |
| `video` | Video player (stub) | Shows title/description; checks `online` flag and shows an inline "connection required" block instead of playing anything real; `playToast()` just alerts if offline |
| `ai` | AI assistant chat | Chat UI backed by a tiny in-memory keyword-matching "knowledge base" (`kb` array); offline state shows a canned fallback message |
| `updates` | Release/version management | Shows one pending content release, one installed content release, one installed app version, each as separate concepts |
| `about` | About/help | App version, content release, language, privacy notice, contact support, safeguarding-report contact |

Bottom nav (5 items, persistent across all main screens): Home, Modules, Videos, Ask, About.

**Not real, must become real:**
- Splash/download/update progress bars are `setInterval` animations with fabricated byte counts — no actual file transfer.
- "Search" on Home is a tap-through to Modules, not a functioning search index.
- Video screen has no video element, player, or downloadable asset — title/description only.
- AI chat is exact-substring keyword matching against 10 hardcoded Q/A pairs — not retrieval, not an LLM.
- Read-aloud uses the browser's `speechSynthesis` API directly on English text extracted from the DOM; no
  offline TTS engine, no non-English audio (the prototype explicitly says non-English "plays English for now").
- "CDD TEAM 0041", the 62% continue-reading progress, and the pending release notes are all hardcoded strings.

---

## 2. Admin Portal inventory

A second top-level stage (`#adminStage`), tab-switched via `setAdminPanel(name)`, sharing one fixed
sidebar (`ROLE · CONTENT ADMIN` — no real auth/role logic). Panels (`data-adminpanel`):

| Panel | Contents |
|---|---|
| `dash` | 4 stat cards (active devices, update adoption %, AI questions this week, published/draft module count — all static numbers); a bar chart of "sessions opened per module" (static heights) |
| `content` | Table of the 6 modules with type, languages (EN + "HA\*" beta-flagged), status (Published/Draft), last-updated date; "+ New content item" button (non-functional) |
| `releases` | Table of 4 releases: a pending content release, a live content release, a language pack, an app version — each with independent status/mandatory flags; a static "governance workflow" pill chain (Draft → Programme review → Localisation review → Data-protection review → Technical QA → Publish); "Publish new release" button (non-functional) |
| `questions` | Bar list of "most frequent unmatched questions" (static counts) + a table of a "recent question log" with module context and matched/unmatched status (static rows) |
| `languages` | Table of 4 languages with "modules translated" fraction and status (Active/In review/Not started) |
| `analytics` | Bar chart of "usage by language"; table of "update & error monitoring" events (failed downloads, resumed interrupted updates, app crashes) |

**Not real:** every number in every admin panel is a literal in the HTML — there is no backend, no auth, and
no data source behind any of it.

---

## 3. Content model (from the prototype's JS, sourced from the AZM Training Flipbook)

```js
modules = [
  { idx, code /* 'M1'..'M6' */, name, meta /* e.g. "6 sections · offline" */,
    progress, done, video /* currently always null */, speak /* plain-text narration string for TTS */,
    body /* raw HTML: headings, <p>, <ul>, <div class="callout">, <figure class="step-photo"> with base64 img + figcaption */ }
]
```
Six modules are seeded, matching the flipbook 1:1:
1. Introduction to Azithromycin (AZM) Drug Administration
2. Determination of Eligibility for AZM Drug Administration
3. Steps for Referral of Children to Health Facility
4. Azithromycin Drug Administration and Recording
5. Interpersonal Communication and Social & Behaviour Change (SBC)
6. Safeguarding

Photos are embedded as base64 data URIs in a top-level `photos` object keyed by name (e.g.
`module1-hero`, `module2-muac`, `module2-dose-measure`, `module3-referral`) and referenced from module
`body` strings. In a real system these become `media_assets` rows with real files in object storage, not
inline base64.

`videos` = 4 hardcoded items (title, description, source module code): AZM POS mixing/administration, MUAC
tape technique, AZM Referral Form walkthrough, interpersonal-communication role-play. No file, no URL, no
duration, no checksum — placeholders only.

`kb` (AI knowledge base) = 10 hardcoded `{keywords[], module, answer}` entries covering: age eligibility,
sick/fever referral, dosing, vomiting/re-dosing, malnutrition/MUAC thresholds, reconstitution steps, allergy
signs, safeguarding escalation, housemarking codes, 28-day antibiotic exclusion. `suggestedQs` = 4 example
chips shown above the chat input.

---

## 4. Every interaction / navigation path

- Splash → (auto, no button shown in prototype) → Language
- Language: tap a language row (radio-select only, `selectLang`) → Continue → Consent
- Consent: "Agree and download" → Downloading → (auto after fake progress) → Home; or "Skip for now" → Home directly
- Home: update banner → Updates; continue-reading card → Reader (module 4); module grid tile → Reader;
  search bar tap → Modules; "✦" FAB → Ask; bottom nav → Modules/Videos/Ask/About
- Modules: back → Home; row tap → Reader
- Reader: back → Modules; audio play/stop buttons (`toggleSpeak`/`stopSpeak`, client-side only); "mark as
  complete" → mutates in-memory module state, re-renders Home/Modules grids
- Video Library: back → Home; row tap → Video
- Video: back → Video Library; play button → `playToast()` (offline-only alert; no-op online)
- Ask: back → Home; suggestion chip or typed question + Enter/➤ → `askAI()` → keyword match or fallback,
  appended to in-memory `chatLog` (lost on reload — no persistence)
- Updates: back → Home; "Download & install" on the pending release → fake progress bar → button becomes "Installed"
- About: back → Home; other rows are inert placeholders (no destination screens exist for them)
- Global: a "simulate connectivity" toggle switch (dev annotation panel only, not part of the real product)
  flips `online`, which re-renders the video "connection required" block and the AI chat's offline fallback

Admin: sidebar links swap the active `.admin-panel`; no cross-panel navigation logic, no drill-down from a
table row to a detail view.

---

## 5. Media assets referenced

- 4 embedded photos (base64 JPEG) used as illustrative step photos inside module bodies.
- 4 video *references* (no actual media files) as listed above.
- No audio files — read-aloud is synthesized on-device from text, not a bundled asset.

---

## 6. AI interactions

Single-turn request/response, no conversation memory beyond the visible `chatLog` array, no session
persistence, no real retrieval (substring match on a 10-entry array), no citation mechanism beyond a
hardcoded `mod` label, no online/offline distinction in matching logic — offline simply blocks the whole
interaction rather than falling back to a local index. Unmatched question handling is described as "logged
for the content team" but nothing is actually persisted anywhere.

---

## 7. Online/offline states represented

- Global `online` boolean (prototype-only toggle switch), read by: `renderConnBlock()` (video screen),
  `renderChatState()`/`askAI()` (AI screen).
- Reader, Modules, Home, About, Updates all ignore the flag entirely in the prototype — implying (per the
  requirements doc) they are meant to work identically online or offline once content is downloaded.
- No offline queue, no sync-on-reconnect logic, no conflict resolution exists in the prototype.

---

## 8. Hardcoded values that must become database/config-driven

- CDD team identity ("CDD TEAM 0041"), greeting text, continue-reading percentage and module reference
- Content package size ("6.4 MB"), download/update progress simulation
- App version ("1.2.0"), content release id ("2026.03-R02" installed, "2026.09-R03" pending) and release notes text
- All admin dashboard/analytics numbers (device counts, adoption %, question counts, bar-chart heights)
- Language list and per-language translation-completion fractions
- The `kb` AI answer set and `suggestedQs`
- Safeguarding contact email (`concerns@malariaconsortium.org`) — sourced from flipbook Module 6, should
  become a configurable org setting rather than a literal string
- The governance workflow stage list (Draft → Programme review → Localisation review → Data-protection
  review → Technical QA → Publish) — matches flipbook language on release approval and should become
  actual workflow state, not a static pill row

---

## 9. Recommended database mapping (summary — detailed schema already drafted in the master prompt, §6–9)

| Prototype concept | Target table(s) |
|---|---|
| `modules[]` entries | `modules`, `module_translations`, `content_sections` |
| `photos{}` base64 blobs | `media_assets` (type IMAGE), referenced by `content_sections` |
| `videos[]` | `videos` + `media_assets` (type VIDEO) |
| Language list + beta flags | `languages` |
| `kb[]` | Source documents for the RAG pipeline (chunked + embedded into `pgvector`), not a literal table |
| Chat log | `ai_question_log` (question, matched module/content ref, answered boolean, timestamp, device/user ref) |
| Release rows (content/app/language-pack) | `releases` (+ `campaigns` for the AZM intervention itself) |
| Admin stat-card numbers | Derived views/queries over `user_module_progress`, `ai_question_log`, `releases` — not stored directly |
| "Mark as complete" / continue-reading % | `user_module_progress` |
| Governance pill chain | Release approval workflow state machine (status enum + `reviewed_by`/`reviewed_at` per review type) |

## 10. Recommended API mapping (indicative — not final)

- `GET /content/releases/current`, `GET /content/releases/{id}/package` — for the connect-once download
- `GET /modules`, `GET /modules/{id}` (localized) — served from the downloaded package offline, from the API online
- `POST /sync/progress`, `POST /sync/ai-questions`, `POST /sync/analytics` — batched sync on reconnect
- `POST /ai/ask` (online RAG) vs. on-device RAG (offline) — same request/response shape, different execution path
- `GET /videos`, `GET /videos/{id}/stream-url` (or signed download URL if offline video is enabled)
- Admin: `POST /admin/releases`, `PATCH /admin/releases/{id}/approve` (per workflow stage), `GET /admin/analytics/*`

## 11. Recommended offline storage mapping

- SQLite tables mirroring `modules`, `module_translations`, `content_sections`, `media_assets` (local cache),
  `user_module_progress`, a local `sync_queue` for AI questions/progress/analytics generated while offline,
  and a local vector index + quantized model files for offline AI once Phase 10/11 is reached.

---

## 12. Open items this analysis cannot resolve (carried from the SRS, §27)

Per the requirements document, the following are explicitly undecided and must be confirmed by stakeholders
before they're hardened into schema/config: final product name/branding, exact MVP languages, whether videos
are ever downloadable for offline playback, exact AI scope for MVP, content-approval role names, budget
(₦50m vs. ₦15m figures both appear in the source transcript and are not reconciled), and final pilot/production
timeline. Nothing in this analysis invents answers to these.

---

*Next: `docs/architecture.md` (Phase 1, second deliverable) before any implementation phase begins.*
