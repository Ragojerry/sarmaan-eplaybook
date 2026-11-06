# Runbook: import the HFW role modules (staging first)

**Scope:**
- Load the 17 HFW modules alongside M1–M6.
- Then credit learners from their old completions.

**Order:** dry run → staging import → phone checks → production.

**Do not run any step against production until staging is signed off.**

Both scripts refuse to run when `ENVIRONMENT=production` unless `--allow-production` is given.

## 0. Before you start

**Approvals.**
- The module split is approved.
- A clinician has signed off the English content (open_questions.md, section B).
- Hausa is not needed for this import. It comes later.

**Code.** The import scripts and the credit table are on branch `hfw-role-modules`. That branch is not merged. Merge it, or deploy it to staging only.

**Optional patch.** The `importer-alt-text` patch is separate. It is only needed to import *translated* alt text later.

**There is no staging environment today: production is the only server.** Build one from the latest production backup:

1. Take a fresh production dump. It is a read-only `pg_dump`, run the way the deploy SSM command does (`pg_dump -Fc`).
2. Restore it into a separate database, on a separate EC2 instance or locally in Docker. Set `ENVIRONMENT=staging` there.
3. Point a test APK at the staging API. Build with `--dart-define=API_BASE_URL=<staging URL>`.

A test APK must **never** point at production.

## 1. Dry run (no changes)

```
cd backend
alembic upgrade head            # adds the module_completion_credits table (c7d1e5a93f20)
python -m scripts.import_hfw_content --dry-run --report ../content/hfw_flipbook/import_dry_run_report.md
```

Continue only when the report says **Blocking problems: none**. The dry run checks for:

- missing image files;
- CSV keys with no matching section;
- image sections with no caption or alt text;
- modules with no role assigned;
- section or quiz UUIDs that collide with an existing non-HFW record.

## 2. Import to staging

```
python -m scripts.import_hfw_content --report ../content/hfw_flipbook/import_staging_report.md
python -m scripts.import_hfw_content --dry-run      # re-run check: expect 0 created, 17 modules updated
```

What the import creates:
- 17 modules, all DRAFT.
- English module texts, all DRAFT.
- 254 sections, with the UUIDs the CSV keys use.
- 39 images in `content/media/images/hfw/`.
- The role lists.
- 170 quiz questions.

What it never does:
- It never touches M1–M6.
- On a re-run it updates rows. It never duplicates them.

## 3. Review and publish on staging

In the admin portal:

1. Open each HFW module and read it through.
2. Approve its English text.
3. Set the module to PUBLISHED.
4. Build and publish a content release.

Phones only receive PUBLISHED modules that have an approved text.

## 4. Credit on staging

```
python -m scripts.credit_hfw_modules --dry-run --report ../content/hfw_flipbook/credit_staging_dry_run.md
python -m scripts.credit_hfw_modules --report ../content/hfw_flipbook/credit_staging_run.md
```

Note the `run_id` printed by the real run. `--undo <run_id>` reverses it.

Check the pre/post-test report:
- Credited rows show "credited from M…".
- Earned rows show "earned".

## 5. Phone checks on staging (one test learner per role)

Create five learner accounts on staging: CDD, Health worker, Logistician, Monitor/supervisor and Other. Sign in on the staging APK.

| Check | Expected |
|---|---|
| CDD sees | HFW-01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 12, 14, 17 |
| Health worker sees | HFW-01, 02, 04, 05, 06, 09, 10, 12, 13, 14, 17 |
| Logistician sees | HFW-01, 02, 04, 06, 10, 12, 14, 16, 17 |
| Monitor/supervisor sees | HFW-01, 02, 04, 06, 08, 09, 11, 12, 14, 15, 17 |
| Other sees | HFW-01, 02, 04, 06, 09, 11, 12, 14, 17 |
| **Shared module HFW-09 (Call-in data)** | Shows for CDD, Health worker, Monitor/supervisor **and** Other, as one module. It does not show for the Logistician. |
| One module per role, opened end to end | Pre-test, then reading with pictures and captions, then post-test. A score of 90% or more completes it. |
| Credited learner (a copy of a real account with M4 completed) | HFW-06, 07, 08, 10 show as completed for a CDD. Old M4 is still completed. |
| Offline | Turn on airplane mode after the sync: lessons and pictures still open. |
| Screen reader (TalkBack) on an image | Reads the image's alt text. |

**Decide the learning order before go-live** (open_questions.md A1). The new modules unlock only after M1–M6 are complete.

## 6. Production (only after staging sign-off)

1. **Back up.** Run the usual pre-deploy `pg_dump` to `/opt/sarmaan/backups/pre-hfw-<date>.dump`.
2. **Deploy.** Deploy the merged branch the usual way. The deploy runs `alembic upgrade head` and adds the credit table.
3. **Copy the content folder.** The deploy bundle excludes `content/`, so copy `content/hfw_flipbook/` to `/opt/sarmaan/content/hfw_flipbook/`.
4. **Dry run.** Inside the backend container: `python -m scripts.import_hfw_content --dry-run --allow-production --content-dir /content/hfw_flipbook`.
5. **Import.** `python -m scripts.import_hfw_content --allow-production --content-dir /content/hfw_flipbook`. Then review, approve, publish and release, as on staging.
6. **Credit dry run.** `python -m scripts.credit_hfw_modules --dry-run --allow-production --map /content/hfw_flipbook/content_sections.json`. Check the counts against expectations.
7. **Credit.** Run the same command without `--dry-run`. Keep the `run_id`.
8. **Spot-check.** Check two learners in the pre/post-test report.

## Rollback

| Step | How to undo |
|---|---|
| Credit | `python -m scripts.credit_hfw_modules --undo <run_id>`. It removes that run's credits and restores the new-module progress as it was. Old records were never changed. |
| Import, before publishing | The modules are DRAFT, so phones never see them. Leave them, or archive them (status ARCHIVED). Never delete M1–M6. |
| Import, after publishing | Set the HFW modules to ARCHIVED and publish a new release. Phones drop them at the next sync. |
| Schema | Undo the credits first (`--undo`), then `alembic downgrade b4e9d2a71c58`. Or restore the pre-deploy dump. |
