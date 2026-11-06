# Changeover plan: the HFW modules replace M1–M6

**Decision.** This is a clean changeover. The 17 HFW modules, built from the 9 flipbook modules, become the only curriculum. The old modules M1–M6 are **archived for everyone**, new learners included. Nobody gets credit for old modules, and everyone's new progress starts at zero.

**Archived does not mean deleted.** No learner, progress or test record is ever deleted, in any environment.

## 1. What learners see after the changeover

**Their module list.** Every learner sees the 7 General modules first, then the modules for their own role. `modules.csv` gives the order (`learning_order`) and roles of each module.

| Role | List (in order) |
|---|---|
| CDD | HFW-01, 02, 04, 06, 12, 14, 17, then 03, 05, 07, 08, 09, 10 |
| Health worker | General, then 05, 09, 10, 13 |
| Logistician | General, then 10, 16 |
| Monitor/supervisor | General, then 08, 09, 11, 15 |
| Other | General, then 09, 11 |

A module shared by several roles is a single module. HFW-09 (Call-in data), for example, appears for CDD, Health worker, Monitor/supervisor and Other.

**The unlock chain.** A module opens only when every earlier module in that learner's list is complete. The first General module is open for everyone. M1–M6 are no longer in anyone's list or chain.

**Progress.** Every learner starts at zero. Nothing from M1–M6 counts toward the new modules. The 90% post-test rule is unchanged: it auto-approves and completes the module, with no separate pass mark and no audit entry.

**The one-time notice.** On app 0.1.10, after the first sync that installs the new curriculum, learners see this once:
- **English:** "The training has been updated. Start the new modules."
- **Hausa (draft, needs native review):** "An sabunta horon. Fara sababbin darussa."

## 2. What happens to the old data

**Archiving.** M1–M6 are set to `status = ARCHIVED`. That takes them out of:

| Removed from | Mechanism |
|---|---|
| Learner lists and the unlock chain | `app/learning/access.py` shows PUBLISHED modules only |
| Phones | The next release package leaves them out. Phones delete their sections, quizzes and cached images at the next sync (tested, see `offline_and_app_version_tests.md`). |
| Search (Ask) | The search index is rebuilt without them |
| Picture downloads | Pictures follow module visibility |

**Records.** Every progress and test record stays in the database, unchanged. The cutover and rollback tests compare every progress and test row before and after.

**Reports.** The old records appear only in the admin portal's "**Legacy (M1-M6)**" report (`/reports/legacy` and `legacy.csv`), with every row labelled. Current reports and completion rates count PUBLISHED modules only, so old and new are never mixed.

**Late uploads.** A phone that was offline through the changeover still uploads its M1–M6 work when it reconnects. The server **keeps** it:
- quiz attempts are stored with `valid = false` and the reason "module archived (legacy curriculum)";
- progress can go up but never completes anything.

Before this change, the server would have rejected those uploads, and the learner's data would have been lost.

## 3. Content that changed between the old and new modules

This is for the programme team. Details and page references are in `change_log.md`.

| New module | Covers old | Change in doses, time windows, cut-offs or codes |
|---|---|---|
| HFW-02 Eligibility | M2 | New rule: a child who is 59 months in round 1 is not eligible in round 2. New chart that refers "mild/severe/acute malnutrition" (open clinical question). |
| HFW-03 MUAC | M2 | MAM and SAM now need "**Immediate** referral". ANC was removed. |
| HFW-04 Referral | M3 | Allergy signs changed ("continuous vomiting", no "unusual behaviour"). SAM added to the danger signs. |
| HFW-06 Giving AZM | M4 | **A partly used bottle stays viable 2 to 3 days** (was 2). At most 5 children at a time. Shake for at least 30 secs. Syringe removed. |
| HFW-07 Child Record Card | M4 | **The height-based dose table (2–25 ml) is taught for the first time** (clinician sign-off). |
| HFW-08 House marking | M4 | **Codes:** rounds 1–6, round-3 examples, house number dropped from the list, R/C example. |
| HFW-10 Accountability | M4 | **Reconciliation** now uses the Inventory Control Card and empty bottles × 4; bottles return to the LGA store within 3 days. |
| HFW-17 Safeguarding | M6 | **Contact email** printed as "concenrns@" (clinician form, item 4). |

HFW-05, 09, 12, 13, 15 and 16 have no old equivalent. HFW-01, 11 and 14 have wording changes only.

## 4. The cutover script

`backend/scripts/cutover_hfw.py`. A dry run of the cutover is in `cutover_dry_run_report.md`, and a dry run of the import alone is in `import_dry_run_report.md`.

**What a real run does,** in one transaction, so nothing is ever half done:

1. Imports the HFW content.
2. Publishes the HFW modules.
3. Archives M1–M6.
4. Rebuilds search.
5. Publishes a new mandatory content release with the curriculum marked `hfw-2026`. This is the content-version bump that makes every phone refresh.

**What it reports:**
- learner accounts affected;
- in-progress learners who lose visible progress;
- learners who completed M1–M6;
- modules archived;
- new modules published.

**Rollback** (`--rollback`): M1–M6 go back to PUBLISHED and the HFW modules back to DRAFT (hidden), and a new release is published. Nothing is deleted, and progress learners made on HFW modules stays stored. A second cutover after a rollback works; this is tested.

**Guards in production.** The script refuses to run when:
- `CUTOVER_DATE` is not set (dry runs included);
- `CUTOVER_DATE` hasn't arrived yet (real run);
- `--confirm-production` is missing (real run);
- `--backup` is missing or fails verification (real run). Verification requires a `pg_dump -Fc` file that holds the users, progress and test tables and is less than 12 hours old.

The programme sets `CUTOVER_DATE`. No default is coded.

**Not run against production.** Only against the local development database (dry run and tests).

## 5. Phones and app versions

Summary; the test results are in `offline_and_app_version_tests.md`:

| Phone | What the user sees |
|---|---|
| App 0.1.10, online | The new modules after the next sync. M1–M6 and their cached images are removed. The one-time notice appears. |
| App 0.1.9 | The same new content and removal; tested against the real 0.1.9 code. No one-time notice, and a removed module says "not part of the training for your role". It works, so no forced update is needed. |
| Offline through the changeover | Keeps showing M1–M6 until it syncs. Work done meanwhile is uploaded and kept as Legacy. Then it switches like an online phone. |
| App older than 0.1.8 (no pre/post tests) | Not tested. Those apps can't do the pre/post tests the new modules need. Check that no field phone runs one (runbook step 4.6). |

**Version gating.** From 0.1.10, the server can set `MIN_APP_VERSION`. Older apps then show "Training updated, please update the app" instead of the training. Apps older than 0.1.10 cannot read this setting.

## 6. Afterwards

M1–M6 stay archived and are never deleted. Their records stay available in the Legacy report and export.
