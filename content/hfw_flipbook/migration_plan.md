# Changeover plan: the HFW modules become the first and only content

## Decision (programme, 2026-11-06)

The app is still being built, and every progress record and test submission in it is test data. So:

- The 17 HFW modules, built from the 9 flipbook modules, are treated as the **first content** the app ever had.
- The old modules M1–M6 are **deleted completely**.
- **Every user starts from nothing.** No training history is kept.
- No staging server: dry run locally, then run on production with a verified backup.

## 1. What learners see afterwards

| Role | Module list, in order |
|---|---|
| CDD | HFW-01, 02, 04, 06, 12, 14, 17 (General), then 03, 05, 07, 08, 09, 10 |
| Health worker | General, then 05, 09, 10, 13 |
| Logistician | General, then 10, 16 |
| Monitor/supervisor | General, then 08, 09, 11, 15 |
| Other | General, then 09, 11 |

- A module opens only when every earlier module in the learner's list is complete; HFW-01 is open for everyone.
- A module shared by several roles, such as HFW-09, is one module.
- Everyone starts at zero.
- The 90% post-test rule is unchanged: it auto-approves and completes the module, with no separate pass mark and no audit entry.

**On app 0.1.10,** learners who had the old content see a one-time notice:
- **English:** "The training has been updated. Start the new modules."
- **Hausa (draft, needs native review):** "An sabunta horon. Fara sababbin darussa."

## 2. What the changeover deletes and keeps

Everything happens in one transaction (`backend/scripts/cutover_hfw.py`).

| Deleted, for all users | Deleted, the old modules | Kept |
|---|---|---|
| Module progress | M1–M6 module rows | User accounts, roles, areas, teams |
| Pre-/post-test attempts | Their sections and section translations | The audit log |
| Ask (AI) question logs | Their quiz questions, module texts, FAQ entries and search passages | Image files on disk, so a backup restore still works |
| Analytics events | Their 4 placeholder video records | |
| | Media rows that only they used | |

**Restart.** Every user's training attempt goes back to 1, and their training restart time is set to the moment of the cutover. This has two effects:

- **Phones** (0.1.9 and 0.1.10) wipe their own local progress and test attempts at the next sync, then install the new release.
- **The server** refuses any upload recorded before the cutover, for example from a phone that was offline through it.

**Content version.** A new mandatory release, marked `hfw-2026`, makes every phone refresh at its next sync. M1–M6 and their cached images are removed from phones.

**Reports.** Reports show only HFW modules and new activity.

## 3. Content that changed from the old M1–M6

This is for the programme team. Details are in `change_log.md`.

| New module | Change in doses, time windows, cut-offs or codes |
|---|---|
| HFW-02 Eligibility | New rule: a child who is 59 months in round 1 is not eligible in round 2. The chart refers "mild/severe/acute malnutrition" (clinician item 3). |
| HFW-03 MUAC | MAM and SAM now need "Immediate referral". ANC was removed. |
| HFW-04 Referral | Allergy signs changed. SAM added to the danger signs. |
| HFW-06 Giving AZM | A partly used bottle stays viable 2 to 3 days (was 2). At most 5 children at a time. Shake for at least 30 secs. |
| HFW-07 Child Record Card | The height-based dose table (2–25 ml) is taught for the first time (clinician item 1). |
| HFW-08 House marking | Rounds 1–6, round-3 examples, house number dropped from the list. |
| HFW-10 Accountability | Inventory Control Card and empty bottles × 4; return to the LGA store within 3 days. |
| HFW-17 Safeguarding | Email printed as "concenrns@" (clinician item 4). |

## 4. The script

**Dry run** (`--dry-run`): changes nothing and reports:
- users and learners affected;
- learners with unfinished and with completed modules;
- every count of rows to be deleted;
- the 17 modules that will be live, in learning order.

The local result is in `cutover_dry_run_report.md`.

**Guards in production.** The script refuses to run when:
- `CUTOVER_DATE` is not set (dry runs included);
- `CUTOVER_DATE` hasn't arrived yet (real run);
- `--confirm-production` is missing (real run);
- `--backup` is missing or fails verification (real run). Verification requires a `pg_dump -Fc` file that holds the users, progress and test tables and is less than 12 hours old.

The programme sets `CUTOVER_DATE`. No default is coded.

**Rollback.** Restore the backup taken just before the run (`pg_restore`). Deleted data cannot come back any other way, which is why the script won't run on production without a verified backup.

**Re-running** after a cutover finds nothing more to do.

**Not run against production.** Only the local dry run, plus tests that run the real cutover inside a transaction that is rolled back.

## 5. Phones and app versions

Details in `offline_and_app_version_tests.md`.

| Phone | What the user sees |
|---|---|
| 0.1.10, online | The new modules after the next sync. Local history and M1–M6 (with cached images) are removed. The one-time notice appears. |
| 0.1.9 | The same removal and new modules; tested against the real 0.1.9 code. No notice. |
| Offline through the changeover | Keeps the old content until it syncs. Work done meanwhile is refused by the server and wiped on the phone at the sync. |
| Older than 0.1.8 | Not tested. Can't do the pre/post tests. Check that none are in use. |

From 0.1.10, the server can set `MIN_APP_VERSION`. Older apps then show "Training updated, please update the app".
