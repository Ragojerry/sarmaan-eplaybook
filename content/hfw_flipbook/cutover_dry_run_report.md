# Curriculum changeover report (DRY RUN, nothing changed, environment development)

Run at 2026-11-06T12:39:49+00:00.

## Checks

- CUTOVER_DATE not set (allowed outside production)

## Users (counted before the run)

- user accounts (all start the training from nothing; accounts are kept): **2**
- learner accounts: **1**
- users with any progress or test submission (wiped): **2**
-   of whom learners with started but unfinished modules: **1**
-   of whom learners who had completed at least one module: **0**

## Training history wiped

- module progress rows deleted: 5
- pre-/post-test attempts deleted: 0
- Ask (AI) question logs deleted: 10
- analytics events deleted: 8
- users reset to training attempt 1: 2

## Old modules deleted

- old modules deleted: 6
- section translations deleted: 9
- FAQ entries deleted: 0
- quiz questions deleted: 63
- module texts deleted: 7
- videos deleted: 4
- sections deleted: 62
- media rows deleted (files kept on disk): 11

## New curriculum

- new modules published: 17
- modules live after the cutover, in learning order: HFW-01, HFW-02, HFW-04, HFW-06, HFW-12, HFW-14, HFW-17, HFW-03, HFW-05, HFW-07, HFW-08, HFW-09, HFW-10, HFW-11, HFW-13, HFW-15, HFW-16

## Content release (devices refresh at their next sync)

- release code: `HFW-CUTOVER-20261106123949`; curriculum: `hfw-2026`
- modules 17, sections 254, media 39, quiz questions 170

Rollback: restore the backup taken before the run (`pg_restore`). There is no other way back.
