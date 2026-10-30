# Admin Portal — Phase 5

## 1. What's real now

| Area | Backend | Frontend |
|---|---|---|
| **Auth** | Already existed (Phase 4) | Login page, `AuthProvider` (localStorage-backed tokens), automatic 401→refresh→retry via an axios interceptor, protected routes redirect to `/login` |
| **Dashboard** | `GET /analytics/dashboard` — real SQL aggregates (module counts, AI question counts, module engagement, language usage, download/sync failures) | Stat cards + two Recharts bar charts, all reading from that one endpoint |
| **Modules** | Full CRUD (`GET/POST /modules`, `PATCH /modules/{id}`, `POST /modules/reorder`) | List page with create form; click through to detail |
| **Content (per module)** | Translations (`.../translations`) + structured sections (`.../sections`), typed by `ContentType` enum — never raw HTML | Module detail page: governance workflow bar + actions, section list with a typed create form |
| **Governance workflow** | `app/content/governance.py` — `advance()`/`reject()`, RBAC-checked per stage, every transition audit-logged | Workflow bar shows current stage; buttons for submit/approve/reject appear only where the API would actually allow them (though the backend is the real enforcement — the frontend hiding a button is just UX, not security) |
| **Languages** | Full CRUD + status transitions (`LANGUAGE_APPROVE` audit-logged on reaching ACTIVE) | List + create form; status dropdown for reviewer roles |
| **Releases** | Create, publish (TECHNICAL_REVIEWER-only), rollback | List + create form; publish/rollback buttons gated by role |

## 2. Governance workflow — who can do what

Exactly per master prompt §15, enforced in `app/content/governance.py` (one shared module so every content type uses the same rules, not per-endpoint copies):

```
DRAFT --(CONTENT_ADMIN submits)--> PROGRAMME_REVIEW
PROGRAMME_REVIEW --(PROGRAM_REVIEWER approves)--> LOCALISATION_REVIEW
LOCALISATION_REVIEW --(LOCALISATION_REVIEWER approves)--> TECHNICAL_QA
TECHNICAL_QA --(TECHNICAL_REVIEWER approves)--> PUBLISHED

Any review stage --(that stage's reviewer rejects)--> REJECTED
```

`SUPER_ADMIN` can perform any transition regardless of stage — the one role every governance action must permit. Every transition writes an `audit_logs` row with `entity_type='module_translation'` and the from/to status in `details` — satisfying §15's "record every transition in audit logs" requirement.

**Reject destination**: the master prompt doesn't specify where rejected content goes. I chose `REJECTED` as a terminal status (not silently back to `DRAFT`) so the rejection and its reason are visible/auditable, rather than disappearing back into the normal draft flow. This is a reasonable interpretation, not a specified requirement — flag if the program wants rejected content to auto-return to `DRAFT` for immediate rework instead.

## 3. The "no raw HTML" requirement (§16)

Content sections are typed blocks (`ContentType`: TEXT, HEADING, IMAGE, TABLE, CALLOUT, WARNING, JOB_AID, VIDEO, AUDIO, LIST) with a JSONB `content` field whose shape depends on the type. The admin UI's section editor in Phase 5 is intentionally minimal — a type picker + title + plain text field — proving the structured-content mechanism works end-to-end without raw HTML. Building out richer per-type editors (a real table builder, image upload with cropping, etc.) is expected to grow in Phase 6 as actual prototype content gets migrated through this pipeline and its real editing needs become concrete.

## 4. The `analytics_events` table (new in this phase)

The dashboard (§49) and analytics (§50) requirements need event-level data — active devices, video plays, download/sync failures — that didn't exist in the Phase 3 schema. Rather than fake these numbers (explicitly forbidden: "Do not use permanent prototype numbers"), I added `analytics_events`: a generic event log (`event_type` enum + JSONB `payload` + FK references to user/module/video/device) that the dashboard queries directly. **Every dashboard number currently reads 0 or `null`** because the mobile app doesn't emit these events yet (that's Phase 7+ work) — that's the honest, correct state, not a bug. Once mobile starts syncing via `POST /sync/analytics`, these numbers populate for real.

## 5. Verified (not just written)

`backend/tests/test_content.py` — 10 automated tests, run twice in a row against a real database:

1. `CDD` role blocked from creating a module (403)
2. `CONTENT_ADMIN` can create a module
3. Any authenticated role can list modules
4. Listing modules requires auth
5. **Full 4-stage governance workflow**: DRAFT → PROGRAMME_REVIEW → LOCALISATION_REVIEW → TECHNICAL_QA → PUBLISHED, with the wrong role rejected (403) at every single stage before the correct role succeeds — plus confirms the audit trail actually recorded ≥4 entries
6. Rejection at a review stage sets status to REJECTED
7. Non-`CONTENT_ADMIN` blocked from creating a language (403)
8. Listing languages includes the 4 seeded defaults
9. Only `TECHNICAL_REVIEWER` can publish a release (`CONTENT_ADMIN` gets 403)
10. Dashboard reflects real database state (not hardcoded)

Combined with Phase 4's 6 tests, **16/16 pass**, stable across repeated runs.

Two real bugs were found and fixed during this verification (not left for later discovery):
- **JWT collision**: two logins for the same user within the same second produced byte-identical tokens (JWT `iat` truncates to whole seconds) and violated the `refresh_tokens.token` unique constraint. Fixed by adding a `jti` (random UUID) claim to every token.
- **Test cleanup FK gap**: `content_releases.created_by`/`approved_by` have no cascade-delete (correct — a release's provenance should survive even if the creating/approving user's account is later removed), so test teardown needed to null those fields explicitly before deleting the test user.

Run it yourself:
```bash
cd backend
python3 -m pytest tests/ -v
```

## 6. Frontend build verification

```bash
cd admin
npm install
npx tsc -b        # strict type-check — passes clean
npx vite build    # production build — passes clean (657 KB main bundle; a
                   # code-splitting warning appears, not an error — Recharts
                   # is the main contributor, worth revisiting if bundle size
                   # becomes a real concern later)
```

Also verified: backend + admin dev server running together, login flow, and every admin page's underlying API call (`/modules`, `/languages`, `/releases`, `/analytics/dashboard`) all returning correct real data in the same session.

## 7. Known gaps / next steps

- Section editor is minimal (type + title + plain text) — richer per-type editors are expected to grow in Phase 6, per §3 above.
- No image/video upload UI yet (`media_assets`/`videos` tables exist from Phase 3, but Phase 5 didn't build admin screens for them — not in the master prompt's explicit Phase 5 list, which is dashboard/modules/content/languages/releases).
- `AnalyticsPage` (nav item) is still a Phase 2 stub — a dedicated deep-dive analytics screen beyond the dashboard's charts wasn't in Phase 5's explicit scope either.
- Release "package" fields (`package_size`, `checksum`) exist in the schema but nothing populates them yet — actual release-package building is master prompt §11-14, a later phase.

## Videos page

Admin > Videos (CONTENT_ADMIN, SUPER_ADMIN can edit; other roles see the list).
1. **New video** creates a DRAFT record (title, description, module, required-offline).
2. **Upload footage** (MP4 H.264 or WebM, up to 500 MB, `MAX_VIDEO_UPLOAD_MB`). The
   browser reads the duration itself and shows upload progress.
3. **Publish** (needs footage). **Archive** hides it from learners.
Replacing the footage of a published video returns it to DRAFT for re-approval.
Phones that already downloaded a video keep their copy. Learners only ever see
PUBLISHED videos. Index-on-publish: publishing a release rebuilds the Q&A index
(all languages) and the package in one transaction.

## Users page and team code

Admin > Users (SUPER_ADMIN only). Create accounts, set or clear a **team code**
(letters, digits, dashes, up to 20, e.g. `0041`), activate/deactivate, filter by
team. The phone's Home header shows it as "CDD TEAM 0041"; accounts without one
show the first name. Passwords are never shown or editable here. API: `GET/POST
/users`, `PATCH /users/{id}`; every change is audited (USER_CREATE, USER_UPDATE,
ROLE_CHANGE). You cannot change your own role or status.

## Module quiz

Open a module in Content and choose **Manage the module quiz**. Add, edit, reorder-by-sort-order or delete questions of all seven types; image questions use the picture library or a new upload (JPEG/PNG/WebP, 5 MB). A warning shows when a module has fewer than 10 questions. Changes reach phones in the next published release. See `quiz.md`.

## Editing English content

On a module page (CONTENT_ADMIN, SUPER_ADMIN): **Edit title, description and audio text (English)** updates the module and its English translation together. Each section has an **Edit** button: text, headings, callouts/warnings/job aids, list items (one per line), table headers and cells, and image caption/alt text. Structure and pictures are not changed here. Edits are written to the audit log and reach phones on their next sync. Translations in other languages are not updated automatically: after changing English wording, re-export the CSV for that language and re-translate the changed lines.
