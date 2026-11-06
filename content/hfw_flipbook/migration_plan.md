# Migration plan: current 6 modules → 17 HFW role modules

The 17 new modules (HFW-01 to HFW-17) are **added alongside** the current modules M1–M6. Nothing is replaced or deleted. Existing progress, pre-tests and post-tests stay exactly as they are.

## 1. What covers what

The current modules follow the CDD flipbook order: M1 Intro, M2 Eligibility (with MUAC), M3 Referral, M4 Administration and recording, M5 IPC/SBC, M6 Safeguarding.

| Current module | New module(s) covering the same content | Credit given |
|---|---|---|
| M1 Introduction to AZM | HFW-01 Introduction to AZM | yes |
| M2 Determination of Eligibility | HFW-02 Eligibility for AZM; HFW-03 MUAC Nutrition Assessment | yes, both |
| M3 Steps for Referral | HFW-04 Referral of Children to the Health Facility | yes |
| M4 Administration and Recording | HFW-06 Giving AZM Safely; HFW-07 Child Record Card; HFW-08 House Marking; HFW-10 Drug Accountability and Reconciliation; HFW-11 Cohort Tracking | yes, all five |
| M5 Interpersonal Communication and SBC | HFW-14 Interpersonal Communication and SBC | yes |
| M6 Safeguarding | HFW-17 Safeguarding | yes |

New in the 17-module set. There is no old equivalent, so no credit is given:

| New module | Roles | Why it is new |
|---|---|---|
| HFW-05 The AZM Referral Form | CDD, Health worker | M3 only had one step: "complete the top portion of the referral form". The whole form, including the health-facility part, is new. |
| HFW-09 Call-in Data Reporting | CDD, Health worker, Monitor/supervisor, Other | Not in M1–M6. |
| HFW-12 Drug Safety and Side Effects | All (GENERAL) | Side effects, adverse events and SAE definitions were not taught. M3 only listed allergy signs. |
| HFW-13 NAFDAC Reporting and the Role of DSNOs | Health worker | Not in M1–M6. |
| HFW-15 Monitoring and Supervision | Monitor/supervisor | Not in M1–M6. |
| HFW-16 Supply Chain Management | Logistician | Not in M1–M6. |

The full list of new modules, with roles, duration and source pages, is in `modules.csv`.

## 2. Credit rule

**When credit is given.** A new module is credited from an old module only when the old module taught the new module's topic in a section of its own: a heading, or a titled callout or warning. One sentence inside another topic does not count. That is why HFW-05 (referral form) and HFW-12 (drug safety) get no credit.

**What a credit is.** For each learner who completed the old module, the credit script:

- creates a credit record for the new module, marked "credited from <old module>";
- copies the old completion date and the score of the post-test that completed it. The score is left empty when the old module was completed without a post-test, for example before tests existed;
- marks the learner's progress for the new module as completed, with the old date, so phones and the "complete to unlock the next module" order treat it as done.

**Records that are never touched.** The old module's progress and test records are never edited or deleted. The credit is stored alongside them in a new table, `module_completion_credits`.

**Telling credits apart.**

| Where | What shows |
|---|---|
| Data | A credit row exists for (learner, module), with `source_module_code`, `source_completed_at`, `source_score_percent` and `run_id`. |
| Pre/post-test report and CSV | `completion_source` = `credited` or `earned`, plus `credited_from` and `credited_score`. The admin page has a "Completed how" column, for example "credited from M4 (100%)". |
| Activity reports and CSVs | `modules_completed_credited` per learner, area and session, and `completed_credited` per module, next to the existing totals. The admin pages show them as "Credited" or "Of which credited". |

**Who gets a credit.** Learner accounts only, and only for new modules their learner role can see. A logistician who completed M4 is credited HFW-06 and HFW-10, but not HFW-07 (CDD only).

**Skipped.**

- learners already credited by an earlier run (so the script is safe to re-run);
- learners who already completed the new module themselves (their completion stays "earned");
- modules outside the learner's role.

A learner whose role changes later can be credited by running the script again.

**Training restart.** Restarting a learner's training now also removes their credits, together with their progress and attempts.

### One old module → several new modules

- **M2 → HFW-02, HFW-03:** the same completion date and score are copied to each.
- **M4 → HFW-06, HFW-07, HFW-08, HFW-10, HFW-11:** the same completion date and score are copied to each.

### Several old modules → one new module

There are no such cases in this mapping. The script supports them: all listed old modules must be completed, and the latest completion date and the lowest score are copied.

## 3. Content that changed between the old and new versions

This is for the programme team. Credit still applies; this is information, not a block. The details and page references are in `change_log.md`.

| New module | Credited from | What changed |
|---|---|---|
| HFW-02 Eligibility | M2 | New rule: a child who is 59 months in round one gets AZM but is not eligible in the next round (p11). New eligibility chart that refers children with "mild/severe/acute malnutrition" (p16; open clinical question B3). "Green card" wording removed (p11). |
| HFW-03 MUAC | M2 | MUAC actions changed: MAM is now "**Immediate** referral to health facility for counselling", and SAM "Immediate referral to health facility" (p18). The ANC assessment was removed. |
| HFW-04 Referral | M3 | Allergy signs changed: "continuous vomiting" replaces "vomiting for more than 2 hours", and "unusual behaviour" was removed (p24). Danger signs now include SAM (p23). The step "confirm the caregiver understands by asking them to repeat" was removed (p25). |
| HFW-06 Giving AZM | M4 | **Time window:** a partly used bottle stays viable "up to 2 to 3 days" instead of "up to 2 days" (p32). New: give to at most 5 children at a time (p31) and shake for at least 30 secs (p33). The infant feeding syringe was removed, leaving the dispensing cup only (p33). The daily target is now "a total of 100 children each day" instead of "a minimum of 100 children" (p32). |
| HFW-07 Child Record Card | M4 | **Doses:** the card's height-based dosing table (2–25 ml) is taught for the first time (p34; open clinical question B1). A second card version adds date of birth (p49). |
| HFW-08 House Marking | M4 | **Codes:** the round can now be 1–6 instead of 1 or 2. Examples changed from round 1 to round 3. "House number" was dropped from the list, although the examples still include `021`. An R/C example was added (p36; open question C2). |
| HFW-10 Accountability | M4 | **Procedure:** reconciliation moves from "in DIGIT HCM at day's end" to the Inventory Control Card, empty bottles × 4 checked against DIGIT HCM, separate cartons, and return to the LGA store within 3 days (p44–45). |
| HFW-17 Safeguarding | M6 | **Contact:** the safeguarding email in the new flipbook reads concenrns@malariaconsortium.org; the old module had concerns@ (p87; open question C1). |

HFW-01, HFW-11 and HFW-14 have wording changes only: who supervises CDDs, a longer cohort section, and longer IPC examples.

## 4. How the credit step runs

- Script: `backend/scripts/credit_hfw_modules.py`. It is separate from the import, and safe to re-run.
- Run `--dry-run` first: it changes nothing and reports, per new module, how many learners and records it would credit, and why others were skipped.
- `--undo <run_id>` removes one run's credits and puts the new-module progress back as it was. It keeps any progress a learner earned afterwards with a post-test.
- When `ENVIRONMENT=production`, the script refuses to run without `--allow-production`. Run it on staging first (see `import_runbook.md`). It has **not** been run against production.
- Mapping source: the `credit_from` field in `content_sections.json`, generated from `_build/hfw_modules.py`.

The local dry run (`credit_dry_run_report.md`) shows 0 records, because the local database has no completions and no imported modules. The automated test `tests/test_hfw_migration.py::test_credit_from_old_modules` runs the whole path with sample learners: dry-run counts, credit, re-run, reports and undo. It checks that the old progress and test rows are unchanged afterwards.

## 5. Hiding the old modules after the migration window

Archive, never delete:

1. Before archiving, export the activity and pre/post-test reports (CSV) as a record of the old modules.
2. In the admin portal, or with `PATCH /modules/{id}` and `{"status": "ARCHIVED"}`, set M1–M6 to ARCHIVED.

What archiving does:

- Learners stop seeing the module. Only PUBLISHED modules are shown (`app/learning/access.py`).
- The next content release leaves it out (`app/releases/packager.py`), so phones drop it at their next sync.
- Reports stop counting it toward completion rates, because they measure PUBLISHED modules only. That's why step 1 exports them first.
- Every progress, attempt and credit row stays in the database.

To undo, set the status back to PUBLISHED.

**Decision needed before go-live:** the learning order during the window (open question A1). The new modules are imported with a sort order after M1–M6. A learner must complete every earlier visible module before a later one unlocks, so a learner who has not finished M1–M6 cannot start the new modules. Credited learners skip the matching new modules.
