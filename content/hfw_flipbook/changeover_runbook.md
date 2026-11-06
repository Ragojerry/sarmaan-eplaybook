# Changeover runbook

The HFW modules become the first and only content, M1–M6 are deleted, and all training history is wiped.

Each step has a Pass and a Fail box. **Stop at the first Fail.** Nothing runs against production before the go/no-go (section 3) is signed.

There is no staging server. Dry runs happen locally, and the real run happens on production with a verified backup. **Rollback = restore that backup.**

## Production run record (2026-11-06)

The programme decided to run the changeover the same day, without waiting for the clinician review (`clinician_signoff.md`).

| Step | Result |
|---|---|
| 4.1 | Done. `CUTOVER_DATE=2026-11-06`; backend deployed with `main`; database already at the latest migration; content copied to the server. |
| 2.5 | Done. Production dry run: 3 accounts (2 learners) wiped; 6 old modules, 62 sections and 63 questions deleted; 17 modules published. |
| 4.2 | Done. `pre-hfw-cutover-final.dump` (SHA-256 `f9944af082dd70e429ecd369bc3036a72cd9731cdc50bf769aae008027c82884`) was taken just before the run. It is in `/opt/sarmaan/content/hfw_backups/` on the server and in `s3://sarmaan-deploy-568898409880/backups/`. A copy from 13:08 (before the dry run) is next to it. |
| 4.3 | Done at 13:31 UTC; the backup was verified by the script. Report: `cutover_production_report.md`. Release `HFW-CUTOVER-20261106133103`. |
| 4.4 | Checked in the database, not yet in the admin portal. The only modules are HFW-01 to HFW-17, all PUBLISHED and in learning order. Progress, attempts, Ask logs and analytics are all 0; every user is on attempt 1. 254 sections, 170 questions, 39 images on disk. Health is 200 directly and through CloudFront. |
| 4.5–4.10 | **Still to do** on real phones with app 0.1.10 (published the same day) and 0.1.9. |

Production differs from the steps below in one way: the server's IAM role can't write to S3. The off-server copy of the backup was therefore pulled through Systems Manager, checked by SHA-256, and uploaded with a team member's credentials.

## People

| Role | Responsible for | Name | Contact |
|---|---|---|---|
| Technical owner (app and backend) | Scripts, deploy, backup, restore | | |
| Programme owner (changeover) | `CUTOVER_DATE`, telling learners | | |
| Clinician (content) | `clinician_signoff.md` (open review, not a gate) | | |

## 1. Local checks (development machine)

| # | Step | Pass | Fail |
|---|---|---|---|
| 1.1 | Run `pytest tests/test_hfw_migration.py` (backend) and `flutter test` (mobile). All tests pass. | ☐ | ☐ |
| 1.2 | Run `python -m scripts.cutover_hfw --dry-run`. Expect: 17 modules live in learning order, 6 old modules to delete, release `hfw-2026`, no "REFUSED". | ☐ | ☐ |
| 1.3 | Build the 0.1.10 APK and install it on a test phone. It must point at a test or local backend, never at production before 4.4. | ☐ | ☐ |

## 2. Before go/no-go

| # | Step | Pass | Fail |
|---|---|---|---|
| 2.1 | Clinician review is **not** a gate (programme decision, 2026-11-06). The content is published as the PDF prints it; `clinician_signoff.md` stays open, and changes come later in a new release. | ☐ | ☐ |
| 2.3 | The image rights and consent items (`open_questions.md`, section D) are resolved, or accepted in writing by the programme owner. | ☐ | ☐ |
| 2.4 | The programme owner has set `CUTOVER_DATE` and told testers that all training history will be wiped. | ☐ | ☐ |
| 2.5 | Production dry run (after deploying the branch): `python -m scripts.cutover_hfw --dry-run --content-dir /content/hfw_flipbook`. Review the counts of users and rows to be deleted. | ☐ | ☐ |

## 3. Go / no-go

| Question | Yes | No |
|---|---|---|
| Sections 1 and 2 all passed? | ☐ | ☐ |
| Everyone agrees that all progress, test submissions, Ask questions and analytics will be deleted? | ☐ | ☐ |
| A backup will be taken and verified just before the run, and restoring it has been tried once? | ☐ | ☐ |

Decision: ☐ **GO** on `CUTOVER_DATE` = __________  ☐ **NO-GO**. Reason: ______________________

| Role | Name | Signature | Date |
|---|---|---|---|
| Technical owner (app and backend) | | | |
| Programme owner (changeover) | | | |

## 4. Production run (only after GO)

| # | Step | Pass | Fail |
|---|---|---|---|
| 4.1 | `CUTOVER_DATE` is set in production `.env`. Deploy the branch the usual way; `alembic upgrade head` runs. Copy `content/hfw_flipbook/` to `/opt/sarmaan/content/hfw_flipbook/`. | ☐ | ☐ |
| 4.2 | Take a backup: `pg_dump -Fc` in the database container, giving `pre-hfw-cutover.dump`. Copy it where the backend can read it, and keep a second copy off the server (for example in the project's S3 deploy bucket). | ☐ | ☐ |
| 4.3 | Run `python -m scripts.cutover_hfw --backup <file> --confirm-production --content-dir /content/hfw_flipbook --report cutover_production.md`. The report says "backup … verified". | ☐ | ☐ |
| 4.4 | In the admin portal: only HFW-01 to HFW-17 exist, all PUBLISHED. Reports show no old modules and no old activity. | ☐ | ☐ |
| 4.5 | **Phone with old content and old progress** (0.1.10): after syncing, the old modules and their progress are gone, the list is General first, only HFW-01 is open, and the notice shows once. | ☐ | ☐ |
| 4.6 | **One account per role** signs in: CDD, Health worker, Logistician, Monitor/supervisor, Other. Each list matches `migration_plan.md` §1. **HFW-09** appears for CDD, Health worker, Monitor/supervisor and Other, and not for the Logistician. | ☐ | ☐ |
| 4.7 | Open one module end to end: pre-test, reading with pictures, then post-test. A score of 90% or more completes it and opens the next. | ☐ | ☐ |
| 4.8 | **App 0.1.9 phone:** after syncing it shows the new modules, M1–M6 are gone, and there is no freeze. | ☐ | ☐ |
| 4.9 | **Offline phone:** airplane mode during the run, then reconnect. The old content is replaced and nothing old is kept. | ☐ | ☐ |
| 4.10 | **Regression:** tap a completed module, and try to open a module that was removed. No freeze, and back works. TalkBack reads one picture's alt text. | ☐ | ☐ |

**If anything fails after 4.3:** stop the backend and restore with `pg_restore --clean -d <database> pre-hfw-cutover-final.dump` (the backup from 4.2, taken just before the 2026-11-06 run). Restart and check the admin portal. The newest release is then the pre-cutover one again, so phones go back to it at their next sync and restore their progress from the server. Image files were never deleted.
