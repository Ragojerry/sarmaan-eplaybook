# Content Migration — Phase 6

## 1. What was migrated

The 6 AZM training modules, their full content, and supporting media — out of the click-through
prototype (`sarmaan-eplaybook-prototype_1.html`) and into the real schema built in Phases 3–5.

| Source (prototype) | Destination (real schema) | Count |
|---|---|---|
| `modules[]` array (raw HTML `body` strings) | `modules` + `module_translations` (English) + `content_sections` (typed, structured) | 6 modules, 61 sections |
| `photos{}` (base64 data URIs embedded in source) | Real `.jpg` files on disk (`content/media/images/`) + `media_assets` rows | 11 images |
| `videos[]` (title/description only, no files) | `videos` rows | 4 metadata records |
| — | `content_releases` (baseline migration marker) | 1 release |

## 2. How the HTML→structured conversion was done

The prototype's module bodies are one-off JS template literals with inline HTML — not a consistent,
machine-parseable format, and there are only 6 of them, ever, to convert. Rather than write a
general-purpose HTML parser for a one-time job, the content was **hand-transcribed** into typed
Python data structures (`backend/scripts/prototype_content_data.py`), checked line-by-line against
the original source. Every section maps to a real `ContentType` enum value — **no raw HTML is
stored anywhere**, per master prompt §16.

Mapping used:

| Prototype HTML | `ContentType` |
|---|---|
| `<figure class="step-photo"><img>...</figure>` | `IMAGE` (references a real `media_asset_id`) |
| `<h3>` | `HEADING` |
| `<p>` | `TEXT` |
| `<ul><li>` | `LIST` |
| `<div class="callout good">` | `CALLOUT` (positive framing) |
| `<div class="callout">` (plain) | `WARNING` (constraints/cautions) |
| `<div class="callout">` specifically titled "Job aid tools" | `JOB_AID` |
| `<table class="dose-table">` | `TABLE` |
| `<div class="video-inline" onclick="openVideoFromReader(N)">` | `VIDEO` (references a real `video_id`) |

**Judgment call, not a spec requirement**: the CALLOUT-vs-WARNING split above is a reasonable
interpretation of unstructured legacy content — the prototype only had two visual callout styles,
not four semantic categories. A content reviewer may want to recategorize individual sections
during governance review; nothing prevents that, since these are now ordinary structured rows.

## 3. Media: real files, real checksums

All 11 images were base64-decoded out of the prototype's inline `photos{}` object into real JPEG
files, then uploaded as `media_assets` rows with **actual** SHA-256 checksums and file sizes — not
placeholders. Verified: every file on disk still matches its recorded checksum
(`scripts/verify_content_migration.py`, check 4), and a live download through
`GET /media/{id}/file` was byte-for-byte identical to the source file.

## 4. Videos: honestly incomplete

**No real video files exist anywhere in the source materials** — not in the prototype, not
elsewhere. The prototype's video screen was always a non-functional placeholder (title +
description only; see `docs/prototype-analysis.md` §1). The migration reflects this honestly rather
than pretending otherwise: `videos` rows exist with real titles/descriptions/module links, but
`status=DRAFT`, `offline_available=False`, and `filename`/`storage_path` set to the literal string
`"NOT_YET_UPLOADED"`. These records are correctly linked from their `VIDEO`-type content sections
(verified), but **cannot be published or played until real footage is provided and uploaded** — that
upload step doesn't exist yet either (a natural companion to the `/api/media` upload endpoint, not
built in this phase since there's nothing to upload).

## 5. Governance status of migrated content

Every module's English translation is marked `PUBLISHED` directly, **not** routed through the live
`DRAFT → PROGRAMME_REVIEW → LOCALISATION_REVIEW → TECHNICAL_QA → PUBLISHED` workflow built in Phase
5. This is a deliberate, documented choice: this content already existed (it's the AZM Training
Flipbook, presumably already vetted by the health program) — it wasn't authored fresh through the
admin portal, so forcing it through the review workflow would be theater, not a real review. Every
migrated translation's audit log entry says so explicitly (`details.note` on the `CONTENT_CREATE`
audit row), so this is traceable, not silently smuggled past governance.

## 6. New backend capability: serving media files

Phase 5 built `media_assets` as a table but nothing could actually retrieve the bytes. Since Phase 6
populated real files, this gap would have blocked any actual use of the migrated content — so Phase
6 also added `GET /media/{id}` (metadata) and `GET /media/{id}/file` (the actual file, auth-required),
closing the `/api/media` group from master prompt §53. The admin portal's Module Detail page now
renders real images via a new `AuthenticatedImage` component — a plain `<img src="...">` can't attach
the Bearer token this endpoint requires, so it fetches the file through the authenticated axios
client and renders it as a local object URL instead.

## 7. Verified (not just written)

- `scripts/import_prototype_content.py` run against a real database — **twice**, back-to-back —
  confirming idempotency (identical row counts both times: 6 modules, 61 sections, 11 media assets,
  4 videos, 1 release).
- `scripts/verify_content_migration.py` — 7 checks, all passing: module presence/status, translation
  presence/status/narration text, section counts, on-disk file existence + checksum match for every
  image, every `IMAGE` section's `media_asset_id` resolving to a real row, every `VIDEO` section's
  `video_id` resolving to a real row, and the migration release record.
- Content confirmed reachable through the real API — `GET /modules`, `GET /modules/{id}/sections`,
  `GET /media/{id}/file` — not just present in the database.
- `GET /media/{id}/file` tested for a real download: byte-identical to the source file, and correctly
  rejects unauthenticated requests (401).
- Section counts cross-checked module-by-module via the API (9+11+8+19+6+8 = 61), matching the
  verification script's total exactly.
- Full regression: both existing test suites (Phase 4 auth, Phase 5 content/governance — 16 tests)
  still pass after all Phase 6 changes.
- Admin frontend: `tsc -b` and `vite build` both pass clean with the new `AuthenticatedImage`
  component and media-rendering changes.

## 8. Known gaps / next steps

- Video files: see §4 — real footage + an upload mechanism are both still needed before any video
  can be published.
- Only English content was migrated. Hausa/Fulfulde/Kanuri translations don't exist yet for any
  module — the prototype never had them either (it explicitly labeled those languages "Beta" with no
  real content behind them).
- The `AuthenticatedImage` component works but isn't optimized (no caching across navigations,
  re-fetches the blob every time the component mounts) — fine for Phase 6's verification purposes,
  worth revisiting if the admin portal's image-heavy pages feel slow in practice.
- Section content is faithful to the prototype but minimal in richness (e.g. `TABLE` sections store
  a `headers`/`rows` array, not per-cell formatting) — matches what the source actually had, but
  future content authored fresh through the admin portal could go further than what this migration
  needed to replicate.
