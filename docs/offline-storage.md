# Offline Storage — Phase 8

## 1. Scope, exactly per master prompt §19-20

SQLite (via Drift), content cache, media cache, progress, local search. All 11 tables from §19,
defined exactly as named there: `CachedModules`, `CachedTranslations`, `CachedSections`,
`CachedMedia`, `CachedVideos`, `LocalProgress`, `PendingSync`, `AppSettings`, `InstalledReleases`,
`LocalAiQuestions`, `RagMetadata`.

`LocalAiQuestions` and `RagMetadata` are defined now but genuinely unused — no code writes to them
yet. That's deliberate: Phase 10/11 (offline AI/RAG) owns their logic, but defining the schema now
means that phase doesn't need its own migration just to add tables the master prompt already
specified belong here.

## 2. A mid-phase incident, disclosed plainly

Partway through this phase, the development sandbox's entire filesystem reset — not something
triggerable by anything in this project, an infrastructure-level event. Everything on disk was lost,
including PostgreSQL itself. Recovery: extracted the last verified-good delivery
(`sarmaan-eplaybook-phase7.tar.gz`, still available) as a restore point, reinstalled PostgreSQL +
pgvector from scratch, re-ran every migration and the Phase 6 content migration, and confirmed the
full 16-test backend regression suite still passed before continuing — then rebuilt the Phase 8 files
from the design already worked out earlier in the same session (preserved in conversation history,
not lost). Flagging this rather than silently continuing as if nothing happened, since it's the kind
of thing that should be visible in a build log.

One genuine mistake happened during the rebuild and was caught before delivery: `content_sync_service.dart`
was first retyped with an incorrect import path and an overly loose `dynamic` constructor parameter
instead of the properly-typed `ApiClient`. Caught on review and fixed before this delivery — mentioned
here for the same reason as everything else in this doc: real mistakes get named, not buried.

## 3. The core design decision: explicit `@DataClassName` on every table

Drift generates a Dart data class for each table automatically, inferring its name from the table
class (usually by stripping a trailing "s"). That inference cannot be verified in this environment —
there is no Dart/Flutter SDK here to actually run Drift's code generator and see what it produces.
Rather than guess and risk every method signature in `local_database.dart` being wrong in a way that
only surfaces when you run `build_runner` locally, every table gets an explicit `@DataClassName(...)`
annotation (e.g. `CachedModules` → `CachedModuleRow`). This removes an entire class of risk at zero
cost — the names are no less readable, and now they're guaranteed rather than assumed.

## 4. `ContentSyncService` — the one place that writes into the local cache from the network

Implements master prompt §18's offline-first principle for real: `syncAll()` fetches every published
module, its English translation, and its sections from the live API, replaces the corresponding local
cache rows, and downloads every referenced image — **verifying its SHA-256 checksum against what the
server recorded before trusting the file**. A checksum mismatch is treated as a failed download, not
cached. A single failed image never aborts the whole sync (partial content beats none, per the same
principle) — `mediaFailed` is tracked and reported, not silently swallowed.

Called from `HomeScreen`, once, when the local cache is empty (first login after install), and again
on manual pull-to-refresh. Nothing else in the mobile app calls it directly.

## 5. Every screen that reads content now reads from the LOCAL cache, not the network

This is the actual behavioral change Phase 8 makes real, not just structural:

| Screen | Phase 7 (network) | Phase 8 (local) |
|---|---|---|
| Home | `GET /modules` every load | `LocalDatabase.getAllModules()` — instant, works offline |
| Modules | `GET /modules` every load | Same local provider as Home, plus a real local search box (`§19`'s "local search" requirement — SQL `LIKE` over cached titles, no network call) |
| Reader | `GET /modules/{id}/sections` + `GET /modules/{id}/translations` every load | `LocalDatabase.getSectionsForModule()` / `getTranslationForModule()` — genuinely works with the device in airplane mode, provided a sync has happened once |

`Video` screens (library + detail) were deliberately **left on the network** — real video *caching* is
Phase 9's explicit job ("Offline videos: download"), and there's no video file content to cache yet
regardless (see Phase 6/7 notes: no real footage exists anywhere). Moving metadata-only video listing
to local cache now would just be redone once Phase 9 adds real download logic.

## 6. Images: `OfflineAwareImage`, not a replacement for `AuthenticatedImage`

New widget, `lib/widgets/offline_aware_image.dart`: checks the local cache for an already-downloaded
file first (near-instant, zero network), and only falls back to Phase 7's `AuthenticatedImage`
(network fetch) if no local copy exists — which should be rare after a successful sync, but a single
missed download during sync must never break the reader entirely. `AuthenticatedImage` itself is kept
as-is; `OfflineAwareImage` wraps it rather than duplicating its logic.

## 7. Progress is now real, not a placeholder

Phase 7 shipped `ReaderScreen`'s "Mark as complete" button **disabled**, with a comment explaining why
— it needed exactly this phase's local database to mean anything. It's real now: tapping it writes to
`local_progress` (`progressPercent: 100, completed: true`) and enqueues a `pending_sync` row so Phase
12's sync-to-server logic has something to drain later. Opening a module also records `lastOpenedAt`
via the same `upsertProgress` call, laying groundwrock for a future "continue reading" feature —
though that feature itself isn't built this phase (needs UI design decisions beyond just having the
data).

## 8. `app_settings` replaces `SharedPreferences` — one local storage technology, not two

Phase 7 used `SharedPreferences` for two tiny values (first-launch flag, selected language). Master
prompt §19 lists `app_settings` as one of the required local tables. Rather than run two separate
local-storage mechanisms side by side, `SettingsService` (Phase 7) was rewritten to read/write through
Drift's `app_settings` table instead, and the `shared_preferences` package dependency was removed
entirely from `pubspec.yaml`.

## 9. A robustness fix, in the same spirit as Phase 7's `AuthNotifier` fix

`SplashScreen._decideRoute()` originally called `SettingsService.isFirstLaunch()` (a local-database
read) with no surrounding try/catch. A local-database failure — corrupted file, disk full on a real
device, or a missing platform channel in a test/CI environment — would have thrown unhandled and
stranded the user on the splash spinner forever. Fixed: the entire method is now wrapped, falling back
to `/login` on any failure. That route doesn't depend on local storage at all, so it's always safe,
and re-authenticating naturally re-establishes everything else. This also means `test/widget_test.dart`
needs no special mocking for the local database (unlike the `SharedPreferences` mock Phase 7 needed) —
the fallback path handles it correctly by design, not by test-environment accommodation.

## 10. Verified — and what could not be

**Verified in this environment:**
- Full backend regression (16 tests) re-run after the sandbox reset and recovery — still passing.
- `/languages` (public) and `/videos` (Phase 7 additions) re-confirmed working after recovery.
- Content migration re-run and re-verified (7 checks, all passing) against the freshly reinstalled
  database.
- All 10 new/changed Dart files for this phase — brace/paren balance checked.
- Full relative-import graph traced by hand across every mobile `.dart` file: confirmed acyclic (no
  circular imports), which would otherwise be a compile-time error Dart's own tooling would need to
  catch.

**NOT verified here — no Flutter/Dart SDK in this sandbox** (same limitation as Phases 2 and 7):
`flutter pub get`, and **critically this phase**, `dart run build_runner build --delete-conflicting-outputs`
— Drift's code generator must run locally to produce `lib/db/local_database.g.dart` before *anything*
using `LocalDatabase` will compile. This is a new required step beyond what earlier phases needed;
see §11 below for the exact command. After that, `flutter analyze`, `flutter test`, and `flutter run`
should all be run and reported back, the same loop that caught real bugs in Phase 2 and Phase 7.

## 11. Required local setup step — new this phase

```bash
cd mobile
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter analyze
flutter test
flutter run
```

The `build_runner` step is not optional and not a one-time thing — it needs to be re-run any time
`lib/db/local_database.dart`'s table definitions change (adding a column, a table, etc.).

## 12. Known gaps / next steps

- Only English content syncs — matches Phase 6's migration scope (no other language has real content
  yet), but `ContentSyncService`'s language-code assumption (`'en'`, hardcoded) is flagged in its own
  code comment as something that needs resolving via `GET /languages` once real translations exist for
  other languages.
- `PendingSync` rows are written but nothing drains them yet — that's explicitly Phase 12's job, not
  this phase's. They'll just accumulate locally until then.
- No "continue reading" UI yet, despite `lastOpenedAt` now being tracked — the data exists, the
  feature doesn't; a deliberate scope cut, not an oversight.
- Local search (§19) is a simple `LIKE` substring match, not full-text search — sufficient for what
  this phase actually needs (module titles, section text) at current content volume; would need
  revisiting if the content library grows substantially.
