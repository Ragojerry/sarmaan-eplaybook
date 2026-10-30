# Phase 12 — Synchronisation

Two directions, one rule: **the app never needs the network to work; the network only moves data.**

## Phone → server (uploads)

| Endpoint | Key (idempotency) | Merge rule |
|---|---|---|
| `POST /sync/progress` | `(user, module)` | newer `last_opened_at` wins for percent/section; **a completed module never un-completes** |
| `POST /sync/ai-questions` | `(user, client_id)` | insert once; resend → `duplicate` |
| `POST /sync/analytics` | `(device, client_id)` | only the §50 event types; unknown type → `rejected` |

Every call takes a batch (max 200) and returns a result **per item**: `ok`, `duplicate`, `rejected`
(permanently invalid — retrying can never help) or `error` (transient). The phone drops queue rows only
for `ok`/`duplicate`/`rejected`; `error` and any network failure leave them queued. `client_id` is
`<device_id>-<queue row id>`, stable across retries, so a lost response never double-counts.

Progress is uploaded from the `local_progress` table (source of truth); its `pending_sync` rows are just
"something changed" markers. A progress row is only marked synced if it did not change during the upload.

**Order:** progress → AI questions → analytics, oldest first. A failure in one type doesn't block the others.

**Analytics are opt-in.** The consent screen has an unticked checkbox (also a switch on *Sync & updates*).
While off, analytics stay on the phone. Progress and questions are covered by the consent text
("linked to your account and uploaded when you are online").

**Shared phones.** Queued data belongs to the person who created it. If a different user signs in, the
previous user's *unsent* data is discarded rather than uploaded under the wrong account. Sign-out first tries
(8 s) to sync, so this only loses data if the phone was offline at sign-out.

## Server → phone (releases)

* **Publish** (`POST /releases/{id}/publish`, Technical Reviewer) now, in one transaction: rebuilds the Q&A
  index → builds the **package** → writes `content/releases/<code>.package.json` → stores its SHA-256 and size
  on the release → marks it PUBLISHED. If any step fails (e.g. nothing to ship) nothing is published (422).
* The package is a frozen snapshot: published modules + published translations + typed sections, a media
  manifest (id, SHA-256, size), the Q&A passages, and `counts` used for validation. Each module carries its
  own content `checksum`.
* `GET /sync/release/current?installed=<code>` → newest PUBLISHED release and `update_available`.
  `GET /sync/release/<code>/package` → the file (header `X-Package-SHA256`). Rolled-back releases are not served.
* Existing databases: run `python3 -m scripts.build_release_package` once to package the migration release
  created in Phase 6.

### Install pipeline (phone)

`download → validate → stage media → apply → verify → activate`

1. **Download** the package. 2. **Validate**: size + SHA-256 equal the published values; JSON parses;
`schema_version` is 1; package counts match its own contents. 3. **Stage media**: only images that are new or
whose checksum changed are downloaded, verified by SHA-256, written to `*.part`, renamed into place under a
*new* file name (so the old release's images stay readable). 4. **Apply + verify**: one database transaction
replaces modules/translations/sections/passages, upserts media rows, **re-counts what is stored and throws
(rolling everything back) on any mismatch**, then records the release — that row *is* activation.
5. Only after commit are superseded files deleted.

Any failure before the commit leaves the previous release untouched. First install and **mandatory** updates
install automatically; optional ones show *Update available* and wait for the button.

## States (`SyncStatus`)

`offline` · `online` · `syncing` · `syncError` · `updateAvailable` · `upToDate` — shown as a chip on Home and in
detail on **Sync & updates** (`/updates`, also reachable from About).

"Online" means `GET /health` succeeded (with a short timeout) — being on Wi-Fi is not enough (captive portals,
dead data). `connectivity_plus` only short-circuits airplane mode.

**When it runs:** after sign-in, on app resume, when connectivity returns, every 5 minutes while open, from
*Sync now*, and before sign-out. Overlapping calls share one run. After a failure, automatic attempts back
off 30 s → 60 s → 2 m … capped at 30 min; manual *Sync now* always tries immediately.

## Known limits / later

* Videos are not part of the package (they have their own resumable download manager, Phase 9).
  Required-offline videos are not yet auto-downloaded after an update.
* Only English content exists, so one language is installed; the package format already carries languages.
* The server keeps no per-device record of installed release (Phase 13 can derive it from `UPDATE_INSTALLED`).
* Low-storage pre-check before installing is Phase 15.

## Per-user data on a shared phone (local DB v3)

Progress, the upload queue and the Ask question log carry a `user_id`. The local
database is pointed at the signed-in user (`LocalDatabase.setActiveUser`) before
the signed-in state is published, so every screen only ever reads that person's
rows. Signing in as someone else no longer discards anything: the first person's
progress and unsent data stay on the phone and are uploaded only under their own
account when they next sign in.

On every sync the phone also downloads the account's saved progress
(`GET /sync/progress`) and merges it in (never over local changes that have not
uploaded yet), so a reinstall or a new phone resumes where the learner stopped.

Upgrade note: rows created before v3 are attributed to the last account recorded
by the old sync engine (`queue_owner_user_id`); if none was recorded they stay
unowned and are never shown or uploaded. After pulling this version run
`dart run build_runner build --delete-conflicting-outputs` (schema changed).
