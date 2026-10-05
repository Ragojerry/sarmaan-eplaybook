# Database — Phase 3

PostgreSQL 16 + the `pgvector` extension. Schema defined as SQLAlchemy models under `backend/app/models/`,
migrated via Alembic (`backend/alembic/`), verified against a real running instance (see §4 below).

## 1. Tables

| Table | Purpose | Key notes |
|---|---|---|
| `users` | All human accounts: CDDs, supervisors, admin/reviewer roles | `role` is an enum (`RoleName`), not a separate join table — simple single-role-per-user per master prompt §6 |
| `languages` | English + Hausa/Fulfulde/Kanuri | `status` distinguishes ACTIVE vs BETA vs IN_REVIEW vs NOT_STARTED, matching the prototype's language screen |
| `campaigns` | The AZM MDA campaign (and any future campaigns) | |
| `modules` | The 6 AZM training modules | Language-independent metadata; actual content lives in `module_translations` + `content_sections` |
| `module_translations` | Per-(module, language) title/description/body/audio_text + review status | `status` is the governance workflow (`ContentReviewStatus`): DRAFT → PROGRAMME_REVIEW → LOCALISATION_REVIEW → TECHNICAL_QA → PUBLISHED (or REJECTED) |
| `content_sections` | Structured section content within a module | `content` is JSONB — the one deliberate use of flexible JSON, since section shape varies by `content_type` (TEXT/IMAGE/TABLE/CALLOUT/etc.) |
| `media_assets` | Real files (images, docs) on disk/object storage | Never large binaries in source, unlike the prototype's inline base64 (docs/prototype-analysis.md §1) |
| `videos` | The video library | `offline_available` matters now that offline video is confirmed in MVP scope (docs/architecture.md §6) |
| `user_module_progress` | Per-user completion tracking | Mobile writes this locally first (Drift), syncs up via `POST /sync/progress` |
| `content_releases` | Versioned release packages | `release_code` format e.g. `AZM-MDA-2026.09-R03`, matches the prototype's updates screen concept but real |
| `ai_question_log` | Every AI question asked, matched or not | Server mirror of the mobile app's local AI question queue once synced — replaces the prototype's non-persisted in-memory chat log |
| `rag_chunks` | Embedded content chunks for online RAG | `embedding` is a real `pgvector` column (dimension 384, see §3 below) |
| `audit_logs` | Every governance transition + security-relevant action | `details` is JSONB for the free-form action payload |

## 2. Content governance workflow

`ContentReviewStatus` enum on `module_translations.status`, exactly per master prompt §15:

```
DRAFT → PROGRAMME_REVIEW → LOCALISATION_REVIEW → TECHNICAL_QA → PUBLISHED
                                                                → REJECTED (from any review stage)
```

`reviewed_by` / `reviewed_at` capture who last moved it and when. Multi-stage review history (who approved
*each* stage) is intentionally not modeled as separate rows yet — if the program needs a full audit trail of
every stage transition (not just the latest), that belongs in `audit_logs` with `entity_type='module_translation'`,
which is already structured for exactly that.

## 3. pgvector / RAG

`rag_chunks.embedding` is a `vector(384)` column. **384 is a placeholder** — it matches common lightweight
multilingual sentence-embedding models, but the master prompt (§29) leaves the actual embedding model choice
open (see docs/architecture.md §6, "still open" list). Changing the embedding model later requires an Alembic
migration to alter this column's dimension, since pgvector fixes dimension at column-creation time — worth
deciding before Phase 6/content-migration populates real chunks, to avoid a disruptive re-migration.

## 4. Verifying this locally

```bash
cd backend
cp .env.example .env   # then point DATABASE_URL at your Postgres instance
python3 -m alembic upgrade head
python3 -m scripts.seed
python3 -m scripts.verify_db
```

`scripts/verify_db.py` checks all 13 tables (+ `alembic_version`) exist, confirms the `rag_chunks.embedding`
column is present, and confirms the seeded languages/campaign/admin user are there. This was run against a
real PostgreSQL 16 + pgvector 0.6.0 instance during development — see the phase-3 verification output in the
project's build log for the actual run.

**Seed data is deliberately minimal**: 4 languages, 1 campaign, 1 admin user (`admin` / `ChangeMe123!` —
change this immediately in any shared environment). Migrating the prototype's actual 6 modules, images, and
videos into `content_sections`/`media_assets`/`videos` is Phase 6 ("Prototype content migration"), not this
phase — keeping that separate so Phase 6 has a clean, well-defined job rather than redoing partial work.

## 5. Migrating further

```bash
# after changing a model:
python3 -m alembic revision --autogenerate -m "describe the change"
python3 -m alembic upgrade head
```

`alembic/env.py` has a custom `render_item` hook that ensures `pgvector.sqlalchemy` gets imported correctly
in generated migrations — autogenerate doesn't add this import by default, and migrations will fail at
runtime (`NameError`) without it. Always check a freshly generated migration file's imports before running it
if it touches `rag_chunks.embedding` or any future vector column.
