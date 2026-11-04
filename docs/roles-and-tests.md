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

## Pre-test, reading, post-test

For every module with active questions (`app/learning/state.py`, mirrored in
`mobile/lib/learning/learning_rules.dart`):

1. **Locked** until every earlier module in the learner's own order is completed.
2. **Pre-test** before reading. Reading is blocked until it is taken. It is taken once: it is the baseline, and a later pre-test is stored but does not count, so it cannot lower the bar. The phone shows only the score, not the answers.
3. **Reading.** Reaching the end of the module records `reading_completed_at`.
4. **Post-test** only after reading. Retakes are unlimited and every attempt is kept.
5. **Completed** when a post-test scores **at least 90%** and **strictly higher than the pre-test**. Scores are compared as exact fractions. Completing unlocks the next module. The server completes the module itself when it receives the qualifying post-test. The phone does the same offline.

A **100% pre-test** cannot be beaten. The learner sees an explanation, and the
module waits on the "Roles & tests" page. A content admin or programme reviewer
(or a super admin) approves an exception with a reason, and the approval is
audited. With the exception, a post-test of at least 90% completes the module;
if one was already taken, the module completes on approval. The 90% pass mark
is never waived. A training restart removes exceptions together with attempts
and progress.

Questions are tagged **BOTH** (default), **PRE** or **POST**. If no question is
left for one of the tests, that test uses every question, and the quiz editor
warns about it. Modules without questions are completed with "Mark as complete",
as before.

**Server validation of attempts** (`/sync/quiz-attempts`):
- Every attempt is stored.
- An attempt that breaks the sequence is stored with `valid = false` and an `invalid_reason`, such as no pre-test, reading not finished, locked, or pre-test already taken.
- The pass decision is recomputed from the counts.
- Uploads are idempotent per `client_id`.

The phone uploads progress before attempts. That way a backlog from days offline still lands in an order the server accepts.

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
2. Run `alembic downgrade f5b3d9e1a246`. It drops the new columns and the `test_exceptions` table, so learner roles, audiences, question usage, pre-test types and exceptions are lost.
3. Restore the previous backend image and admin bundle.

Phones on 0.1.8 keep working offline, and their uploads of the new fields are ignored by the old server.

## App compatibility

**Minimum app version for the new flow: 0.1.8.** Older apps keep syncing
reading progress and receive only their role's content, because filtering
happens on the server. They cannot complete a module that has questions: their
quiz attempts have no test type, so they are stored as history and do not count.
Update every learner's app before switching the flow on.

## Admin portal

- **Users:** portal role and learner role, filters, needs-review badge, bulk template.
- **Content:** a module page has "Who sees this module". The quiz editor has "Used in: pre-test / post-test / both".
- **Roles & tests:**
  - Confirm module audiences.
  - Set learner roles for flagged accounts.
  - Approve 100% pre-test exceptions.
- **Reports, "Pre/post tests" tab:** per learner and module, the pre-test score, post-test attempts with best and latest score, whether both rules were met, the exception, and attempts that did not count. Click a row for every attempt. CSV export is included.
