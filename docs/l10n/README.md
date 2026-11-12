# Mobile app interface text (localisation)

The buttons, labels and messages of the mobile app can be translated in the admin portal (**App interface text**) and reach phones without a new app. Module content keeps its own translation workflow (module page → Translations); the consent screen keeps the Consent text page.

## How it fits together

| Part | Where |
|---|---|
| English source (one file) | `mobile/l10n/app_strings.json`: key, English, translator note, optional singular form (`en_one`) |
| English built into the app | `mobile/lib/l10n/app_strings_en.g.dart` (generated) |
| Backend copy the registry is seeded from | `backend/app/l10n/app_strings.json` (generated) |
| Generator and check | `python scripts/l10n_sync.py` (write) / `--check` (fails if a copy is stale or the code uses a key that is not in English) |
| Registry tables | `app_strings`, `app_string_translations` (migration `f9c2a6d4e815`) |
| Seed (English only, safe to repeat) | `cd backend && python -m app.l10n.seed` |
| Portal page | `admin/src/pages/AppTextPage.tsx` (`/app-text`) |
| Phone runtime | `mobile/lib/l10n/l10n.dart` (lookup, fallback, placeholders, plurals), `app_strings_service.dart` (download), Drift table `cached_app_strings` (schema v9) |

**One language setting.** The language picked at first run (or later in About → Language) drives both the interface and the content. Each string and each module falls back to English on its own when it has no published translation.

**Fallback.** A phone shows a translation only if it is published, non-empty, and uses no placeholder the English lacks. Otherwise it shows the English built into the app, so it never shows a key or a blank.

**Governance.** Same stages and roles as module translations:
- DRAFT → PROGRAMME_REVIEW → LOCALISATION_REVIEW → TECHNICAL_QA → PUBLISHED.
- Content admins and localisation reviewers may type or import translations. Every edit returns the string to DRAFT.
- Moving DRAFT → PROGRAMME_REVIEW is the content admin's step, as for modules. A localisation reviewer may also submit their own drafts (decision 2026-11-12).
- Nobody approves their own edit at a review stage.
- Every change is in the audit log (`app_string_translation`, `app_string_registry`).

**Published copy.** Editing a published string keeps the approved text on phones until the new version is published.

**Needs update.** When the English of a string changes, its version number goes up and older translations are flagged "needs update". They stay published until someone redoes them.

**Sync.** `GET /sync/app-strings?language=ha&since=<server_time>` is public, like `/languages`, so the sign-in screen can already be translated.
- The first call returns everything (`full: true`).
- Later calls return only strings published or changed since, plus `removed` keys.
- Phones call it when the language is chosen, at app start, and on every sync.

## Files for translators

**CSV** is recommended: it opens in Excel, works like module translation, and has a BOM so Hausa letters show correctly. JSON is also available for translation tools. XLIFF was not added because the team does not use CAT tools.

**Columns:**
- `key` (do not edit);
- `where` (the translator note);
- `placeholders`;
- `english`;
- `english_singular`;
- `translation`;
- `translation_singular`;
- `status`;
- `needs_update`.

Only `key`, `translation` and `translation_singular` are read back. Empty cells are skipped.

**Import is all-or-nothing.** Any unknown key, duplicate row, missing singular form or unknown placeholder rejects the whole file, with a report of every row. A left-out placeholder is only a warning.

## Adding or changing app text (developers)

1. Use `context.t('area.name')` (or `context.tn(...)` for plurals) in widgets, and `L10n.t(...)` outside them.
2. Add the key to `mobile/l10n/app_strings.json`, with a note saying where it appears.
3. Run `python scripts/l10n_sync.py`, then `python scripts/l10n_sync.py --check`.
4. After deploying the backend, run `python -m app.l10n.seed`. New keys appear for translators, and changed English is flagged "needs update".

## Existing Hausa drafts to review

Before this change, the app had two Hausa sentences written in its code, marked "DRAFT that a native speaker must review". They were moved out of the code and **not** loaded into the registry, so no unreviewed text is published. A Hausa reviewer can enter them in the portal if they are correct:

| Key | English | Draft Hausa from the old code |
|---|---|---|
| `notice.trainingUpdated` | The training has been updated. Start the new modules. | An sabunta horon. Fara sababbin darussa. |
| `update.required` | Training updated, please update the app. | An sabunta horo, da fatan za a sabunta manhajar. |
| `common.ok` | OK | To |

Until then, Hausa phones show these in English.

## Plurals

Each plural string has two forms: singular (`one`) and plural (`other`).
- English, Hausa and Kanuri use the singular for 1 only. The Kanuri rule was confirmed by a Kanuri speaker on 2026-11-12.
- Fulfulde uses the singular for 0 and 1.
