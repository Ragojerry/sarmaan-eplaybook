# Phase 13 — Audit trail and usage analytics

## Audit log (master prompt §61)

Entries are written next to the action itself. Now recorded: sign-in, sign-out, **failed sign-in**
(unknown user, wrong password, suspended account — with the attempted username and the client IP, never
the password), content create/edit/review/approve/reject, language approval, release create/publish/rollback,
**video upload** (filename, size, SHA-256) and **video required-offline changes**.

* `GET /audit` — filters `action`, `user_id`, `entity_type`, `date_from`, `date_to`; `limit` ≤ 200 + `offset`;
  newest first. `GET /audit/actions` lists the action names. `GET /audit/export.csv` exports the same filters
  (max 10,000 rows); cells starting with `= + - @` are prefixed with `'` so a spreadsheet never runs them.
* **Who can read it:** Super Admin, Content Admin, Technical Reviewer. Everyone else gets 403.
* Append-only: there is no endpoint that edits or deletes entries.
* Admin portal: **Audit log** page (filters, paging, Export CSV). Failed sign-ins are highlighted.

## Usage analytics (§49-50)

* `GET /analytics/usage?days=` — active devices (24 h/7 d/30 d), activity per day (UTC, zero-filled), module
  opens/completions, **CDDs started/completed** (from synced progress), per-video opens/completions/failures,
  technical failure counts, **release adoption** (distinct devices per release — not raw event counts) and
  language usage.
* `GET /analytics/questions?days=` — answer rate, **questions the materials could not answer** (content gaps,
  grouped case-insensitively) and the most-asked answered questions (§42-43).
* **Who can read it:** every role except CDD. Aggregates only; no per-person data.
* The Dashboard's "Update adoption" is now "% of devices active in 30 days that installed the current release"
  (it previously divided raw install events by active devices, which could exceed 100%).
* Migration `c8e4a1f06d52`: three new audit actions + indexes on the audit/analytics/question tables.
  (Postgres cannot drop enum values; downgrade removes only the indexes.)

## What the phone records

Only if the person opted in (consent screen checkbox, or the switch on Sync & updates):

| Event | When |
|---|---|
| `MODULE_OPEN` / `MODULE_COMPLETE` | opening / marking complete a module |
| `VIDEO_OPEN` / `VIDEO_COMPLETE` / `VIDEO_PLAYBACK_FAILURE` | video screen, end of playback, player error |
| `DOWNLOAD_STARTED` / `DOWNLOAD_FAILED` | video download |
| `SYNC_FAILED` | first failure of a sync streak, or a failed update install |
| `STORAGE_ERROR` | file-system error while downloading a video or update images |
| `APPLICATION_ERROR` | uncaught error — **type name only**, max 1 per type per 10 min |
| `UPDATE_INSTALLED` | a release was installed |
| `DEVICE_HEARTBEAT` | once per UTC day, at the first successful sync |

Events never contain question text, answers, names, e-mail or file paths. They are capped at 2,000 queued
events, are uploaded through the Phase 12 idempotent `/sync/analytics`, and nothing is queued while consent is off.
Questions asked in the Ask screen are *not* analytics events: they are uploaded as account data (see consent text)
and feed the "Questions learners ask" report.

## Known limits

* Event-based figures only cover opted-in devices; the admin page says so. Progress-based CDD columns do not
  depend on opt-in.
* No per-user drill-down yet (supervisor views of their own CDDs) — would need a supervisor↔CDD assignment model.
* Days are UTC, not Nigerian local time.
