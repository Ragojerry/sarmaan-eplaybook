# Changeover runbook: staging first, then production

Each step has a Pass and a Fail box. **Stop at the first Fail.** Fix the problem and repeat the step.

Nothing runs against production before the go/no-go page (section 7) is signed. The scripts enforce this:
- they refuse production without `CUTOVER_DATE`;
- a real production run also needs `--confirm-production` and a verified backup.

**Never delete** a learner, progress or test row, in any environment.

## People

| Role | Responsible for | Name | Contact |
|---|---|---|---|
| Technical owner (app and backend) | Staging build, scripts, deploy, rollback | | |
| Programme owner (changeover) | Staging plan, `CUTOVER_DATE`, learner communication | | |
| Clinician (content) | `clinician_signoff.md` | | |
| Staging owner (to be confirmed by the programme owner) | Runs and looks after the staging server | | |

## 1. Build staging

Default plan, to be confirmed by the programme owner: a second server in **eu-north-1**, restored from the latest production backup and anonymised.

A local run is acceptable **for dry runs only**. It cannot test phones, offline sync or file delivery.

| # | Step | Pass | Fail |
|---|---|---|---|
| 1.1 | Programme owner confirms the staging plan, the staging owner, and the extra server cost. Check the project's spend limit in AWS Settings › Billing first. | ☐ | ☐ |
| 1.2 | Launch a second EC2 instance in eu-north-1, sized like production, managed through SSM. Give it its own security group, its own database, and its own HTTPS address (for example a second CloudFront distribution). | ☐ | ☐ |
| 1.3 | Set `.env` on staging: `ENVIRONMENT=staging`, a **new** `JWT_SECRET_KEY` (never the production one), and **no** `CUTOVER_DATE`. | ☐ | ☐ |
| 1.4 | Take the latest production backup (`pg_dump -Fc`, read-only) and copy it to staging. Restore it into the staging database, with the API **stopped**. | ☐ | ☐ |
| 1.5 | **Anonymise before anyone signs in:** `STAGING_PASSWORD='…' python -m scripts.anonymise_staging`. This replaces names, usernames, emails, phones and passwords, the free text of Ask questions, and usernames in audit details. It deletes no rows. | ☐ | ☐ |
| 1.6 | Spot-check 5 users in the admin portal: no real names, phones or emails. | ☐ | ☐ |
| 1.7 | Deploy the branch to staging. Run `alembic upgrade head`. Copy `content/hfw_flipbook/` to the server's content folder. | ☐ | ☐ |
| 1.8 | Build two test APKs that point at the staging address:<br>• 0.1.10, from this branch;<br>• **0.1.9**, from the 0.1.9 release commit (`a90f381`), for the old-version check.<br>Both use `--dart-define=API_BASE_URL=<staging>`. They must never point at production. | ☐ | ☐ |

## 2. Dry run on staging

| # | Step | Pass | Fail |
|---|---|---|---|
| 2.1 | Run `python -m scripts.cutover_hfw --dry-run --report cutover_staging_dry_run.md`. Expect: no "REFUSED", 17 new modules published, 6 archived, release curriculum `hfw-2026` with 17 modules. | ☐ | ☐ |
| 2.2 | Programme owner reviews the learner counts in the report: learners affected, in-progress learners who lose visible progress, and learners who completed M1–M6. | ☐ | ☐ |
| 2.3 | Confirm the dry run changed nothing: M1–M6 still PUBLISHED, no HFW module, no new release. | ☐ | ☐ |

## 3. Real cutover on staging

| # | Step | Pass | Fail |
|---|---|---|---|
| 3.1 | Back up staging: `pg_dump -Fc`, giving `pre-cutover-staging.dump`. | ☐ | ☐ |
| 3.2 | Run `python -m scripts.cutover_hfw --backup pre-cutover-staging.dump --report cutover_staging.md`. The report must say "backup … verified". | ☐ | ☐ |
| 3.3 | In the admin portal: M1–M6 show ARCHIVED, and HFW-01 to HFW-17 show PUBLISHED. | ☐ | ☐ |
| 3.4 | The "Legacy (M1-M6)" report tab and its CSV list old progress, labelled. The other tabs show HFW modules only. | ☐ | ☐ |
| 3.5 | Database row counts of `user_module_progress` and `quiz_attempts` are the same as before 3.2. | ☐ | ☐ |

## 4. Phones on staging

Create one test learner per role. Use real phones.

| # | Step | Pass | Fail |
|---|---|---|---|
| 4.1 | **CDD** (0.1.10): the list is HFW-01, 02, 04, 06, 12, 14, 17, then 03, 05, 07, 08, 09, 10. Only HFW-01 is open. Open it end to end: pre-test, reading with pictures, then post-test. A score of 90% or more completes it and opens HFW-02. | ☐ | ☐ |
| 4.2 | **Health worker:** General modules, then HFW-05, 09, 10, 13. **Logistician:** General, then 10, 16. **Monitor/supervisor:** General, then 08, 09, 11, 15. **Other:** General, then 09, 11. Open one role module per role. | ☐ | ☐ |
| 4.3 | **Shared module HFW-09** appears for CDD, Health worker, Monitor/supervisor and Other, and not for the Logistician. It is the same module for all of them (same content). | ☐ | ☐ |
| 4.4 | **Phone with M1–M6 cached:** before 3.2, install the app and download content; after 3.2, sync. M1–M6 disappear. Storage use drops (Settings › Storage). The notice shows once, in English, then in Hausa on a Hausa-language phone. | ☐ | ☐ |
| 4.5 | **Offline phone:** airplane mode before 3.2. Work in M2 while offline (the old content still opens). Reconnect and sync. M1–M6 disappear, and the M2 work shows in the Legacy report as not counted. | ☐ | ☐ |
| 4.6 | **App 0.1.9 phone:** after syncing it shows the new modules, M1–M6 are gone, and there is no freeze. Also ask the programme owner to confirm that no field phone runs an app older than 0.1.8. | ☐ | ☐ |
| 4.7 | **Regression:** tap a completed module, and try to open an archived module (for example from a "continue" card that was showing before the sync). No freeze, and back works. | ☐ | ☐ |
| 4.8 | **TalkBack** reads the alt text of one picture. | ☐ | ☐ |

## 5. Rollback on staging, then cutover again

| # | Step | Pass | Fail |
|---|---|---|---|
| 5.1 | Back up, then run `python -m scripts.cutover_hfw --rollback --backup pre-rollback-staging.dump`. | ☐ | ☐ |
| 5.2 | M1–M6 are PUBLISHED, the HFW modules are DRAFT, and the progress and test row counts are unchanged. | ☐ | ☐ |
| 5.3 | A phone syncs back to M1–M6, with old progress shown. No notice appears. | ☐ | ☐ |
| 5.4 | Back up, then run the cutover again (as in 3.2). Repeat 3.3 to 3.5, 4.1 and 4.3. | ☐ | ☐ |

## 6. Before go/no-go

| # | Step | Pass | Fail |
|---|---|---|---|
| 6.1 | `clinician_signoff.md` is complete and signed, including the confirmed safeguarding address. | ☐ | ☐ |
| 6.2 | Any change from 6.1 was applied through `_build/`, the CSVs were regenerated, and `_build/hfw_verify.py` shows 0 mismatches. Then staging was re-imported (repeat section 3). | ☐ | ☐ |
| 6.3 | The image rights and consent items (`open_questions.md`, section D) are resolved, or accepted in writing by the programme owner. | ☐ | ☐ |
| 6.4 | The programme owner has set `CUTOVER_DATE` for production and planned how learners will be told. | ☐ | ☐ |

## 7. Go / no-go

| Question | Yes | No |
|---|---|---|
| Sections 1–6 all passed on staging? | ☐ | ☐ |
| The clinician has signed `clinician_signoff.md`? | ☐ | ☐ |
| A fresh production backup can be taken and verified on the day? | ☐ | ☐ |
| A rollback was rehearsed on staging and took ____ minutes? | ☐ | ☐ |
| Field supervisors know about the change and the app version (0.1.10 recommended; 0.1.9 works)? | ☐ | ☐ |

Decision: ☐ **GO** on `CUTOVER_DATE` = __________  ☐ **NO-GO**. Reason: ______________________

| Role | Name | Signature | Date |
|---|---|---|---|
| Technical owner (app and backend) | | | |
| Programme owner (changeover) | | | |
| Clinician (content) | | | |

## 8. Production (only after GO)

| # | Step | Pass | Fail |
|---|---|---|---|
| 8.1 | `CUTOVER_DATE` is set in production `.env` by the programme owner. The backend is restarted. | ☐ | ☐ |
| 8.2 | Deploy the branch the usual way; `alembic upgrade head` runs. Copy `content/hfw_flipbook/` to `/opt/sarmaan/content/hfw_flipbook/`. | ☐ | ☐ |
| 8.3 | Dry run: `python -m scripts.cutover_hfw --dry-run --content-dir /content/hfw_flipbook`. The counts are close to the staging counts. | ☐ | ☐ |
| 8.4 | Take a production backup (`pg_dump -Fc`, in the database container) and copy it where the backend can read it. | ☐ | ☐ |
| 8.5 | Run `python -m scripts.cutover_hfw --backup <file> --confirm-production --content-dir /content/hfw_flipbook --report cutover_production.md`. | ☐ | ☐ |
| 8.6 | Repeat checks 3.3 to 3.5 on production. One staff phone per role signs in and syncs (4.1 to 4.3). | ☐ | ☐ |
| 8.7 | For the first week, watch for sync errors and Legacy uploads in the admin portal. | ☐ | ☐ |

**Rollback in production.** Run `--rollback --backup <fresh dump> --confirm-production`. Phones return to M1–M6 at their next sync, and no data is lost. If the database itself is damaged, restore the 8.4 backup instead.
