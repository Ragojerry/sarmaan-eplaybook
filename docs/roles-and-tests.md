# Learner roles, role-based content and pre/post tests

## Learner roles

Every account keeps its **portal role** (`users.role`: SUPER_ADMIN, CONTENT_ADMIN,
reviewers, SUPERVISOR, READ_ONLY, or CDD = the learner account with no portal
access). Learners also have a **learner role** (`users.learner_role`):

| Value | Label |
|---|---|
| CDD | CDD |
| HEALTH_WORKER | Health Worker |
| LOGISTICIAN | Logistician |
| MONITOR_SUPERVISOR | Monitor/Supervisor |
| OTHER | Others |

The learner role only decides which modules someone sees. It is never checked
for permissions. It is required when creating a learner account (portal role
CDD). Bulk upload has a `learner_role` column that accepts the labels above. An
old template without that column still works, and its CDD rows mean CDD.

## Module audience

`modules.audience` is either **GENERAL** (every learner role) or **ROLE_SPECIFIC**
(only the roles in `modules.learner_roles`). Learners see GENERAL modules plus
their role's modules. A learner without a learner role sees GENERAL modules only.
Staff accounts see everything, so reviewers can preview on a phone.

Enforcement is on the server (`app/learning/access.py`):

- **Module and progress routes:** `/modules` (list, detail, sections, translations), `/sync/translations`, `/sync/quiz-questions`, `/sync/progress` and `/sync/quiz-attempts`. Uploads for a module the learner may not see are rejected.
- **Search and media:** `/ai/chunks` and `/ai/ask`; videos attached to a module; pictures used only by hidden modules.
- **Release downloads:** `/sync/release/*`. The frozen package is filtered to the account's modules. The result is cached per set of modules with its own SHA-256, so the phone's checksum check still applies (`app/releases/variants.py`).

The phone hides modules a second time (`LocalDatabase.setActiveUser(learnerRole:, staff:)`) in its module lists, search, Ask, the reader and quiz routes, and downloaded videos.

**When a learner role changes:**

1. The phone sees the new role at its next sync.
2. It installs its new copy of the package straight away, which removes the other role's modules, passages, quizzes, pictures and downloaded videos.
3. Progress and attempts are never deleted. They come back if the role changes back.

### CDD flipbook (2026-11-10)

CDD learners have their own curriculum, CDD-01 to CDD-06, built from the CDD
training flipbook (`content/cdd_flipbook`, loaded by `scripts/migrate_cdd_content.py`).
They see only those six modules. The HFW modules are tagged for the other four roles:

| Modules | Who sees them |
|---|---|
| HFW-01, 02, 04, 06, 12, 14, 17 (were GENERAL) | Health Worker, Logistician, Monitor/Supervisor, Others |
| HFW-03, 05, 07 | Health Worker |
| HFW-08, 15 | Monitor/Supervisor |
| HFW-09 | Health Worker, Monitor/Supervisor, Others |
| HFW-10 | Health Worker, Logistician |
| HFW-11 | Monitor/Supervisor, Others |
| HFW-13 | Health Worker |
| HFW-16 | Logistician |
| CDD-01 to CDD-06 | CDD |

No module is GENERAL any more, so a learner without a learner role sees no
modules until one is set. A new module meant for everyone can still be made
GENERAL in the portal; CDD learners would then see it too.

## General test, module quizzes and time (since 2026-11, migration `e7b2c4d91a35`)

The rules live in `app/learning/state.py` and `app/learning/rules.py`, mirrored in
`mobile/lib/learning/learning_rules.dart`. The shared file `tests/learning_vectors.json`
keeps both sides identical.

### General pre-test and post-test

Every learner (CDD, HFW and others) takes the same multiple-choice General test
(`general_test_questions`, the programme's 25 questions; see docs/test-content-review.md).

1. **Pre-test:** taken once, before any module can be opened. Until it is taken every module is locked ("take the General pre-test first").
2. **Post-test:** the same questions. It opens when every module the learner may see is completed, and it is taken once.
3. **Score:** points out of the number of active questions, plus a percentage. There is no pass mark. The server grades every upload itself from the chosen options; an unanswered question counts as wrong.
4. **Counting:** the first valid pre-test and the first valid post-test are the learner's results. Later ones are stored with `valid = false` ("pre-test already taken" / "post-test already taken"), as are ones that break the order. Reports show pre, post and the change (`/learning/general-report`, and the `general_*` fields of `/reports/users`).

The test is switched on with the setting `general_test_active` on the portal's
**General test** page. It can only be switched on when every active question has a
correct answer. While it is off, nothing is served (`GET /sync/general-test` is
empty) or counted, and modules open as before.

### Completing a module

A module can be completed when:

- it is **unlocked**: every earlier module in the learner's own order is completed, and the General pre-test is taken when the test is on;
- its **inline quiz** is passed, if it has one. The quiz is the module's `TRUE_FALSE` sections, answered in the reader right after the section that teaches each point. One attempt answers every statement. It passes at the same **90% pass mark**, with exact arithmetic, so with three statements all three must be right (2 of 3 is 66.7%). After a wrong answer the reader shows the right one and "Try again": the learner answers all the statements again. Retakes are unlimited until the module is completed, and every attempt is kept (`quiz_attempts`, `test_type = MODULE_QUIZ`);
- the learner has spent at least **`module_min_seconds`** of active time in it (default 180 = 3 minutes; set on the General test page).

**Active time** counts only while the module is on screen and the app is in front. It
stops when the app goes to the background or the screen locks, adds up across visits,
and works offline. The reader shows "Time in this module: 1:20 / 3:00". Reading and
the quiz are never blocked by the time; only completing is. The time is
**reported by the phone**, just as the phone grades the quiz: the server keeps the
largest value it receives (`user_module_progress.seconds_spent`) and refuses a
completion that reports less than the minimum ("less than 180 seconds in this module").

The learner completes the module with **Complete module** in the reader. The server
checks the same rules when the progress arrives. The phone uploads the restart, the
General tests and the quiz attempts before progress, so a backlog from days offline
lands in an order the server accepts.

**Completed modules are review-only**, and a module completed before this change stays
completed (it is never locked again for a missing quiz or time).

### The retired per-module pre/post tests

The migration archived every per-module pre/post question (`is_active = false`,
`archived_at` set) and wrote one audit entry listing their ids. The rows and every old
attempt stay for history. They are never served to phones or shipped in a release, and
in the portal they are read-only: no new questions can be added, and an archived one
cannot be re-activated or deleted. An older app that uploads a pre/post attempt has it
stored with `valid = false` ("per-module pre/post tests were replaced (2026-11)").
The `POST_TEST_AUTO_APPROVE_PERCENT` setting is no longer used for completion; it is
still sent to older apps.

### Training restart

A restart (by the learner or an administrator) also deletes the learner's General
test results and the time spent, together with progress and quiz attempts. Uploads
made before the restart are refused as before.

## Existing data (migration `a3c8e4f61b29`)

| Data | Mapping |
|---|---|
| Users with portal role CDD | learner_role CDD (it was the only learner role) |
| Users with portal role SUPERVISOR | no learner role, flagged for review |
| Other staff | no learner role |
| Modules | GENERAL, flagged for review (nobody loses access) |
| Quiz questions | BOTH |
| Quiz attempts | kept as history, `valid = false` ("legacy") |
| Completed modules | stay completed |
| Reading already recorded | kept (`legacy_reading`). Such a learner takes the pre-test for unfinished modules and then goes straight to the post-test |

On the phone (local schema 7):
- Old attempts become `LEGACY`.
- Reading already done is kept.

**Rollback:**
1. Take a `pg_dump` first. The deploy script already does this.
2. Run `alembic downgrade f5b3d9e1a246`. It drops the new columns, so learner roles, audiences, question usage and pre-test types are lost.

Migration `b4e9d2a71c58` removes the manual-approval table that the first version
used. It stops without deleting anything if that table, or the audit log, still
holds approvals.
3. Restore the previous backend image and admin bundle.

Phones on 0.1.8 keep working offline, and their uploads of the new fields are ignored by the old server.

## App compatibility

**Minimum app version for the new flow: 0.1.8.** Older apps keep syncing
reading progress and receive only their role's content, because filtering
happens on the server. They cannot complete a module that has questions: their
quiz attempts have no test type, so they are stored as history and do not count.
Update every learner's app before switching the flow on.

**Minimum app version for the General test, module quizzes and time: 0.1.12.**
Apps up to 0.1.11 do not know the quiz sections or the time, so the server would
refuse their "Mark as complete" (learners would be stuck below 100%). Publish 0.1.12
first and set `MIN_APP_VERSION=0.1.12` together with the migration: apps from 0.1.10
then show "please update the app" (0.1.9 and older ignore it).

## Admin portal

- **Users:** portal role and learner role, filters, needs-review badge, bulk template.
- **Content:** a module page has "Who sees this module". The quiz editor has "Used in: pre-test / post-test / both".
- **Roles & tests:**
  - Confirm module audiences.
  - Set learner roles for flagged accounts.
  - See the auto-approval threshold for 100% pre-tests.
- **Reports, "Pre/post tests" tab:** per learner and module, the pre-test score, post-test attempts with best and latest score, whether the module was completed by the rule, whether it was auto-approved after a 100% pre-test, and attempts that did not count. Click a row for every attempt. CSV export is included.
