# Offline devices and app versions: test results

All tests below ran on the development machine on 2026-11-06, with no network. The phone tests use an in-memory database, the real release installer, and a fake server that serves release packages and images. The backend tests use the local development database and leave it as they found it. **Not yet tested on a real phone:** that is in the production checklist (`changeover_runbook.md`, steps 4.5 to 4.10).

## Results

| # | Scenario | Test | App version | Result | What the user sees |
|---|---|---|---|---|---|
| 1 | Phone has M1–M6 cached and syncs after the cutover | `mobile/test/changeover_test.dart`: "online phone…" | 0.1.10 | Pass | M1–M6 disappear. The list is General modules first, then the role's. The cached images of M1–M6 are deleted from storage and from the image table. The local history is wiped, and the chain starts at HFW-01. |
| 2 | Same as #1 | Same test, run against the 0.1.9 code (git worktree at the 0.1.9 release commit) | **0.1.9** | Pass | The same as #1. 0.1.9 already removes modules that leave the release, and their images. |
| 3 | Phone stays offline through the cutover | "phone offline through the changeover…" | 0.1.10 and 0.1.9 | Pass | Until it syncs, the old modules keep working offline, with images. At the first sync, its old work is refused by the server and wiped on the phone, and it switches as in #1. |
| 4 | All training history wiped at the cutover | `backend/tests/test_hfw_migration.py::test_cutover_makes_hfw_the_first_content_and_wipes_all_history` | server | Pass | Every user starts at zero: no progress, test attempts, Ask questions or analytics. M1–M6 are deleted with their content. The training restart time is set to the cutover, so uploads recorded before it, from offline phones, are refused. |
| 4b | The phone applies the wipe | `changeover_test.dart`: "online phone…" and "a phone that had restarted its training before…" | 0.1.10 and 0.1.9 | Pass | Local progress and attempts for the old modules are deleted at the sync (the server restart). Nothing old is kept on the phone. |
| 5 | **Regression:** tapping a removed module (reader) | "archived module M1 (/reader/m1)…" | 0.1.10 and 0.1.9 | Pass | A "Not available" card and a "Back to modules" button. Five fast taps open no frozen screen, there's no exception, and back works. |
| 6 | **Regression:** opening a removed module's quiz | "archived module M1 (/quiz/m1)…" | 0.1.10 and 0.1.9 | Pass | "This module is not part of your current training." Back works. |
| 7 | **Regression:** tapping a completed module (the earlier freeze bug) | `mobile/test/completed_module_test.dart` (2 cases) | 0.1.10 | Pass | Review mode; no freeze. |
| 8 | One-time notice after the changeover | `mobile/test/changeover_notice_test.dart` | 0.1.10 | Pass | It shows once, in English or in Hausa, and doesn't return after it's dismissed. |
| 9 | No notice on a first install, a re-install of the same curriculum, or a rollback | Same file | 0.1.10 | Pass | Nothing shown. |
| 10 | App updated from 0.1.9 to 0.1.10 just before the cutover | Same file | 0.1.10 | Pass | The notice shows. A phone with cached content but no curriculum record is treated as having the old curriculum. |
| 11 | Version gating | Same file | 0.1.10 | Pass | When the server's `MIN_APP_VERSION` is above the app's version, the training screens are replaced by "Training updated, please update the app" and a "Check again" button. Splash, login and other screens are not delayed. |

**Totals:** the phone suite passes 171 tests (13 new), and the backend suite passes 317 tests (7 new).

## Conclusions

- **0.1.9 does not show stale or broken content after the cutover.** It removes M1–M6 and their files at its next sync and shows the new modules. A forced update is therefore not required for the cutover. What 0.1.9 lacks:
  - the one-time notice;
  - the clearer removed-module message (0.1.9 says "not part of the training for your role").
- **Version gating** exists from 0.1.10 (`MIN_APP_VERSION`), for any later change that an old app couldn't handle. Apps 0.1.9 and older cannot read it.
- **Apps older than 0.1.8** were not tested. They have no pre-/post-tests and could not complete the new modules. The runbook checks that none are in use.

## Changes made for this (app 0.1.10)

| Change | Where |
|---|---|
| The package carries `curriculum`; the installer records it and queues the notice when it changes | `lib/sync/release_installer.dart`, `lib/learning/curriculum_notice.dart`, server `app/releases/packager.py` |
| Notice dialog, shown once from Home | `curriculum_notice.dart`, `lib/screens/home_screen.dart` |
| Server minimum version is stored at sync; the router redirects to the update screen | `lib/sync/sync_engine.dart`, `lib/navigation/app_router.dart`, `lib/screens/update_required_screen.dart`, server `MIN_APP_VERSION` in `GET /sync/learning` |
| Clearer text for a module that is no longer in the training | `lib/screens/reader_screen.dart`, `lib/screens/quiz_screen.dart` |
| App version 0.1.10+11 | `pubspec.yaml`. The APK has not been built or published. |

The Hausa texts need native-speaker review before release: the notice, "To" (OK), and "An sabunta horo, da fatan za a sabunta manhajar" for the update screen.
