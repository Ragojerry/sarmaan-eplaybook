# Hausa, Fulfulde and Kanuri: what exists and what does not

## What is built (backend)

- `section_translations` table (migration `d3a7f95b1c48`): the translated title and
  text of one section per language. English sections stay the structural source of
  truth (type, order, media ids). A section translation is only shipped when the
  module's `module_translations` row for that language is `PUBLISHED`.
- **Export:** `GET /modules/{module_id}/translations/export.csv?language=ha`
  returns a UTF-8 (with BOM) CSV: `key, where, english, translation`.
- **Import:** `POST /modules/{module_id}/translations/import?language=ha`
  (multipart `file`). Writes a **DRAFT** only. Any import into an already-approved
  translation sends it back to DRAFT. The normal review chain still applies:
  DRAFT -> PROGRAMME_REVIEW -> LOCALISATION_REVIEW -> TECHNICAL_QA -> PUBLISHED.
- Empty `translation` cells are ignored, so a partial translation is allowed and
  untranslated parts fall back to English.
- Rules: do not edit the `key` column; the file must be UTF-8 (Excel: *CSV UTF-8*);
  rows that do not belong to the module reject the whole file (nothing is written).
- **Packaging:** a release now carries `section_translations` per module and
  Q&A chunks for every language with a published translation
  (`rebuild_all_chunks` runs inside Publish).
- Tests: `tests/test_translations.py` uses a fake language `zz` and `[zz]` text.
  It proves the plumbing only.

## What is NOT done, and why

1. **No real translations are included.** Health and dosing text must be written or
   verified by qualified translators and pass LOCALISATION_REVIEW. Nobody should
   machine-translate dosing instructions.
2. **The phone's module text now follows the chosen language** (see below). The Ask
   screen and the app's own buttons/labels are still English, and quizzes are English.
3. **Q&A is English-tuned.** Stop-words, `stem()` and `SYNONYM_GROUPS` are English.
   Each language needs its own list in Python and Dart plus regenerated
   `qa_vectors.json`. Until then, non-English questions may answer poorly or
   fall back to "not found".
4. **Fonts.** The bundled Fraunces, Manrope and JetBrains Mono lack the letters
   `ɓ ɗ ƙ ƴ ɲ ǝ ʼ` (only `ŋ` is present). Those characters render with the
   system font. A font with full Hausa/Fulfulde coverage (e.g. Noto Sans) should be
   bundled before launch.

## Adding a language end to end (admin -> phone)

1. **Admin -> Languages -> + New language** (code such as `yo`, name, native name). It starts NOT_STARTED.
2. **Admin -> Content -> a module -> Translations**: choose the language, *Download CSV for translator*,
   send it to a qualified translator, then *Upload translated CSV* (lands as DRAFT) and move it through
   Submit for review -> Approve (programme, localisation, technical QA) until PUBLISHED. Empty cells stay English.
3. **Phone:** the language appears in the picker (About -> Language, or first run). When someone selects it the
   phone calls `GET /sync/translations?language=xx` on every sync and stores the PUBLISHED module text and
   sections (Drift schema v5, table `cached_section_translations`). Module titles in the lists, the reader and its
   audio text switch to that language; any module or section without a published translation shows English.
4. No new release is needed: translations travel through `/sync/translations`, not the release package.

Still English: buttons and labels, the Ask screen, quiz questions, and text-to-speech voice (device voice).
