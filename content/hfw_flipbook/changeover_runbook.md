# Changeover runbook

The HFW modules become the first and only content, M1–M6 are deleted, and all training history is wiped.

Each step has a Pass and a Fail box. **Stop at the first Fail.** Nothing runs against production before the go/no-go (section 3) is signed.

There is no staging server. Dry runs happen locally, and the real run happens on production with a verified backup. **Rollback = restore that backup.**

## People

| Role | Responsible for | Name | Contact |
|---|---|---|---|
| Technical owner (app and backend) | Scripts, deploy, backup, restore | | |
| Programme owner (changeover) | `CUTOVER_DATE`, telling learners | | |
| Clinician (content) | `clinician_signoff.md` | | |

## 1. Local checks (development machine)

| # | Step | Pass | Fail |
|---|---|---|---|
| 1.1 | Run `pytest tests/test_hfw_migration.py` (backend) and `flutter test` (mobile). All tests pass. | ☐ | ☐ |
| 1.2 | Run `python -m scripts.cutover_hfw --dry-run`. Expect: 17 modules live in learning order, 6 old modules to delete, release `hfw-2026`, no "REFUSED". | ☐ | ☐ |
| 1.3 | Build the 0.1.10 APK and install it on a test phone. It must point at a test or local backend, never at production before 4.4. | ☐ | ☐ |

## 2. Before go/no-go

| # | Step | Pass | Fail |
|---|---|---|---|
| 2.1 | `clinician_signoff.md` is complete and signed, including the confirmed safeguarding address. | ☐ | ☐ |
| 2.2 | Any change from 2.1 was applied through `_build/`, the CSVs were regenerated, and `_build/hfw_verify.py` shows 0 mismatches. | ☐ | ☐ |
| 2.3 | The image rights and consent items (`open_questions.md`, section D) are resolved, or accepted in writing by the programme owner. | ☐ | ☐ |
| 2.4 | The programme owner has set `CUTOVER_DATE` and told testers that all training history will be wiped. | ☐ | ☐ |
| 2.5 | Production dry run (after deploying the branch): `python -m scripts.cutover_hfw --dry-run --content-dir /content/hfw_flipbook`. Review the counts of users and rows to be deleted. | ☐ | ☐ |

## 3. Go / no-go

| Question | Yes | No |
|---|---|---|
| Sections 1 and 2 all passed? | ☐ | ☐ |
| The clinician has signed `clinician_signoff.md`? | ☐ | ☐ |
| Everyone agrees that all progress, test submissions, Ask questions and analytics will be deleted? | ☐ | ☐ |
| A backup will be taken and verified just before the run, and restoring it has been tried once? | ☐ | ☐ |

Decision: ☐ **GO** on `CUTOVER_DATE` = __________  ☐ **NO-GO**. Reason: ______________________

| Role | Name | Signature | Date |
|---|---|---|---|
| Technical owner (app and backend) | | | |
| Programme owner (changeover) | | | |
| Clinician (content) | | | |

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

**If anything fails after 4.3:** stop the backend and restore with `pg_restore --clean -d <database> pre-hfw-cutover.dump`. Restart and check the admin portal. The newest release is then the pre-cutover one again, so phones go back to it at their next sync and restore their progress from the server. Image files were never deleted.
