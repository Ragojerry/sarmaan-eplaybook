# SARMAAN e-Playbook

Offline-first training app for Community Drug Distributors (CDDs) delivering the AZM (Azithromycin) Mass
Drug Administration training curriculum, built to replace the `sarmaan-eplaybook-prototype_1.html`
click-through prototype with a real system: FastAPI backend, React admin portal, and a Flutter mobile app.

This is built in phases — see `docs/architecture.md` §7 and the master development prompt for the full
sequence. **Do not assume every phase is finished**; check the phase status below.

## Phase status

- [x] Phase 1 — Prototype analysis (`docs/prototype-analysis.md`, `docs/architecture.md`)
- [x] Phase 2 — Repository foundation: backend/admin/mobile scaffolds, Docker, env config
- [x] Phase 3 — PostgreSQL schema, migrations, seed data — see `docs/database.md`
- [x] Phase 4 — Authentication & RBAC — see `docs/security.md`
- [x] Phase 5 — Admin Portal (this commit) — see `docs/admin-portal.md`
- [x] Phase 6 — Prototype content migration — see `docs/content-migration.md`
- [x] Phase 7 — Mobile application — see `docs/mobile-app.md`
- [x] Phase 8 — Offline storage — see `docs/offline-storage.md`
- [x] Phase 9 — Offline video (this commit) — see `docs/offline-video.md`
- [ ] Phase 10 onward — RAG, offline AI, sync, analytics/audit, packaging, production hardening

**Resolved:** offline video is in MVP scope; AI/RAG assistant is in MVP scope; platform target is
Android + iOS (mobile app is Flutter for this reason).

**Still open** (do not assume answers — see `docs/architecture.md` §6): final product branding, confirmed
MVP language set beyond English, auth identity source, video hosting/storage provider, exact AI/RAG
technology (embedding model, offline LLM runtime), governance-workflow role owners, budget/timeline.

## Repository layout

```
backend/   FastAPI + SQLAlchemy + PostgreSQL + pgvector
admin/     React + TypeScript + Vite admin portal
mobile/    Flutter mobile app (Android first)
content/   Source content, processed content, built releases, media
scripts/   Import/release/validation scripts
docs/      Architecture, database, offline, sync, release, RAG, security, deployment, testing docs
```

## Local development

### Backend + Admin (via Docker Compose)

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

- Backend: http://localhost:8000 (docs at `/docs`, health at `/health`)
- Admin: http://localhost:5173

### Backend (without Docker)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then point DATABASE_URL at a local Postgres if not using Compose
uvicorn app.main:app --reload
```

### Admin (without Docker)

```bash
cd admin
npm install
npm run dev
```

### Mobile (Flutter)

Requires the Flutter SDK (not available in this dev sandbox — the mobile code here has been reviewed for
correctness but not compiler-verified; run `flutter analyze` and `flutter pub get` locally before trusting it
fully).

```bash
cd mobile
flutter pub get
flutter run   # with an Android emulator or device attached
```

The mobile app talks to the backend at `http://10.0.2.2:8000` by default when run on the Android emulator
(the emulator's alias for the host machine's `localhost`).

## Verification performed so far

- `backend`: dependencies installed, app imported successfully, ran under `uvicorn`, `/health` and `/`
  responded correctly.
- `admin`: `npm install`, `tsc -b` (strict type-check), and `vite build` all pass cleanly.
- `mobile`: confirmed running on-device (Android) by the project owner — real Gradle build, real app launch,
  screen navigation working end-to-end.
- `database` (Phase 3): a real PostgreSQL 16 + pgvector instance was stood up, `alembic upgrade head` applied
  cleanly (all 13 tables + `alembic_version`), `scripts/seed.py` ran twice back-to-back with no duplicate
  rows (proving idempotency), and `scripts/verify_db.py` confirms table presence, the `rag_chunks.embedding`
  pgvector column, and the seeded languages/campaign/admin user. The backend's `/health/db` endpoint also
  confirmed the FastAPI app itself (not just raw SQL) can reach the schema. See `docs/database.md` for full
  details and the exact commands to reproduce this locally.
- `auth` (Phase 4): `backend/tests/test_auth.py` — 6 automated tests against a real database, run twice in a
  row to check for state leakage: wrong password rejected, correct login issues both tokens, `/auth/me`
  requires and correctly returns the current user, RBAC actually blocks a non-admin role (403) on a real
  protected endpoint, and logout genuinely revokes the refresh token server-side (a reused token after
  logout is rejected, not just ignored client-side). See `docs/security.md`.
- `admin portal` (Phase 5): `backend/tests/test_content.py` — 10 more automated tests (16 total combined with
  Phase 4's), covering module CRUD, the full 4-stage content governance workflow with per-stage RBAC (every
  wrong-role attempt rejected before the correct role succeeds), rejection, language management, and
  release publishing — all against a real database, stable across repeated runs. The admin frontend was
  type-checked (`tsc -b`), built (`vite build`), and run together with the backend in the same session,
  confirmed logging in and successfully calling every real endpoint (`/modules`, `/languages`, `/releases`,
  `/analytics/dashboard`) with real (not fabricated) data. See `docs/admin-portal.md`.
- `content migration` (Phase 6): the 6 real AZM modules (61 content sections, 11 real images with
  verified checksums, 4 video metadata records) migrated out of the prototype and into the schema —
  run twice to confirm idempotency, verified via `scripts/verify_content_migration.py` (7 checks) and
  by fetching the content through the real API (`/modules`, `/modules/{id}/sections`,
  `/media/{id}/file`) rather than just querying the database directly. Video files themselves are
  honestly absent — no real footage exists in the source materials. See `docs/content-migration.md`.
- `mobile` (Phase 7): backend additions verified live — `GET /videos`/`GET /videos/{id}` (real data,
  401 without a token) and `GET /languages` made public (full 16-test backend regression still passes
  after the change). All 18 new/changed Dart files brace/paren-balance checked. **Not** run through
  `flutter pub get`/`analyze`/`test`/`run` — no Flutter SDK in this sandbox, same limitation as Phase 2
  — please run those locally and report back. See `docs/mobile-app.md`.
- `offline storage` (Phase 8): full local Drift database (11 tables per master prompt §19), a real
  content sync service (downloads + checksum-verifies media before trusting it), and every
  module/reader screen rewired to read from the local cache instead of the network — genuinely works
  offline after one successful sync. "Mark as complete" is real now (writes to `local_progress`,
  queues a `pending_sync` entry). Backend regression (16 tests) and content-migration verification (7
  checks) re-confirmed after a mid-phase sandbox reset and recovery — see `docs/offline-storage.md` for
  the full incident note and what was re-verified. **New required local step this phase**:
  `dart run build_runner build --delete-conflicting-outputs` must run before the mobile app compiles.
- `offline video` (Phase 9): real upload/download/resume/checksum pipeline, verified end-to-end with
  a genuine small MP4 (not mocked bytes) — 7 new automated tests including a full resumed-download
  reassembly confirmed byte-identical and checksum-matching to the source file. 23/23 backend tests
  passing, stable across repeated runs. Video screens now have three real states (not available /
  available-to-download with live progress / downloaded-and-playing from a real local file via
  `video_player`). Storage-usage display computes actual on-disk bytes for videos and training
  images; honestly omits AI/Available-space figures rather than fabricate them. See
  `docs/offline-video.md`.
