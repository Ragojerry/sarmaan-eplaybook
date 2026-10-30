# User areas, activity reports and Power BI

## Areas (Country > State > LGA > Ward > Facility)

- **Admin -> Areas** (SUPER_ADMIN): browse, add and delete areas, or import a CSV
  (`docs/sample_boundaries.csv`: columns `country,state,lga,ward,facility`). Re-importing is safe; one bad row rejects the file.
  An area that has children or users cannot be deleted.
- **Admin -> Users**: pick the deepest area known (its parents are filled in) and a training session.
  Edit later with *edit area / session* in the Area & session column.
- API: `GET/POST /boundaries`, `PATCH/DELETE /boundaries/{id}`, `POST /boundaries/import`.
  Users: `boundary_id`, `clear_boundary`, `training_session_id`, `clear_session`.

## Training sessions (Admin -> Sessions, SUPER_ADMIN)

A session is a cohort with a **start date and end date** (status: upcoming, ongoing, ended is worked out
from today's date). Sessions can overlap. Each user belongs to **one** session (set on the user form,
in *edit area / session*, or in bulk on the Sessions page: select a session, tick people, *Add*; someone
already in another session is moved). A session can only be deleted when it is empty.
Every report can be limited to one session (`session_id`) so each runs and is read independently.
"Finished by end date" counts people who completed every module on or before the session's end date.
API: `GET/POST /sessions`, `GET/PATCH/DELETE /sessions/{id}`, `POST /sessions/{id}/assign|unassign`.
Phones are not told their session yet (the app is unchanged).

## Reports (Admin -> Reports; everyone except field staff)

Filters: training session, area (any level), dates, team code, include staff. Default population is CDDs only.
Dates limit activity to that period, and "completed" means completed in it.

| View | One row per | Highlights |
|---|---|---|
| By session | training session | dates, status, days left, people, not started, avg completion %, finished all, **finished by end date**, quizzes, activity categories |
| By area | country / state / LGA / ward / facility | users, active (30 days), avg completion %, finished all, quizzes passed, avg quiz %, activity categories |
| By user | user | area, location, modules completed, completion %, quizzes, activity categories, last activity |
| By module | module (optionally x area or x session) | started, completed, completion %, quiz takers/passed, avg quiz % |

Activity categories: **training** (module open/complete), **video**, **quiz** (attempts), **Q&A**
(questions asked/unanswered), **technical** (download, sync, app, storage errors), **session**
(heartbeats, updates). Each has **Export CSV** (UTF-8 with BOM; opens correctly in Excel).

## Power BI / API

1. **Reports -> Power BI access** (SUPER_ADMIN): create a key. It is shown once; only a hash is stored.
   Revoke it there at any time. Creating and revoking are audited.
2. Endpoints, header `X-API-Key: <key>`, read-only, JSON array (or `?format=csv`):
   - `/bi/users`
   - `/bi/sessions`
   - `/bi/boundaries?level=state|lga|...`
   - `/bi/modules[?level=state|session]`
   Same filters as the admin: `session_id, country_id, state_id, lga_id, ward_id, facility_id, team_code, date_from, date_to, all_roles`.
3. Power BI Desktop: Get data -> Blank query -> Advanced editor, then the query shown on that page
   (`Web.Contents` with the `X-API-Key` header, access = Anonymous).
4. Scheduled refresh in the Power BI service needs the API reachable over HTTPS from the internet.
   `localhost` works for Desktop on the same computer only. Do that in Phase 16 (HTTPS, rate limiting).

## Privacy

The data includes names, usernames and work areas (never passwords, emails or phone numbers).
Give keys only to people who may see this. No GPS or coordinates are stored.

## Limits

- Reports are computed on request from the synced data, so they are only as current as the last phone sync.
- "Active" uses the latest of progress, events, quiz attempts and questions.
- Large programmes (tens of thousands of users) will want a database view or a nightly snapshot; say so and it can be added.

## Training restart (newest attempt replaces the old one)

A CDD can choose **About → Start training over** on the phone (with a confirmation), and a
SUPER_ADMIN can use **reset training** on the Users page. Either way:

- Progress and quiz attempts for ALL modules are deleted and replaced by the new attempt;
  the "Mark as complete" quiz gate applies again from zero.
- `users.training_attempt` goes up by one and `training_restarted_at` is stored; both appear in the
  user report (`training_attempt`, `restarted_at`).
- Videos, Q&A and technical events from before the restart stay in the raw tables but are ignored by
  every report, so they never count toward the new attempt.
- Anything a phone uploads that is stamped before the restart (a second device still holding the old
  attempt) is rejected as "before training restart".
- The restart is audited (`TRAINING_RESTART`, with what was removed). The phone queues the restart
  and uploads it first on the next sync; it will not restore old server progress until it has.
- Content (lessons, videos, translations) is not touched. All modules restart together, not one at a time.
