# Backend change: accept `|alt` rows in the translation importer

**Status.** Merged into `main` on 2026-11-06 (commit `1bbeb30`). With it, the backend suite passes (311 tests). The English import does not need it, because the English alt text goes in with the sections. It is needed before translated alt text (Hausa) can be imported.

## Today

- **Export only knows `caption`.** `backend/app/content/translation_io.py` builds the list of translatable strings (`flatten()`), and for an IMAGE section that list holds only `caption`.
- **Import rejects anything else.** `import_csv()` refuses every key the module does not expose: "N row(s) do not belong to this module".
- **The phone already reads alt text.** It takes the image's alt text from `content["alt"]` and passes it to Flutter as `Image.semanticLabel`, which TalkBack reads aloud (`mobile/lib/widgets/offline_aware_image.dart`). Translated section content replaces the English keys (`reader_screen.dart`), so a translated `alt` would already be read aloud.

That's why the module CSVs carry no `|alt` rows for now. They are in `alt_text.csv` (`key,english,translation`, UTF-8 with BOM).

## Change

1. **`flatten()`:** for IMAGE sections, return `alt` after `caption` when it is non-empty. The export then writes a `<section-id>|alt` row, labelled "Section N (IMAGE) alt".
2. **`import_csv()`:** no other change. Allowed keys come from `flatten()`, so `|alt` is accepted. The value is stored in the section translation for that language at `content["alt"]` by the existing `_set_path()`. As for every imported string, the translation goes back to DRAFT and must pass review, including localisation review.
3. **Fallback:** an empty translation is ignored, as today, so the phone falls back to the English alt text.
4. **Phone:** no change. The translated `content["alt"]` reaches `semanticLabel`, so screen readers use it.
5. **Release package:** no change. Section translations already carry the whole content dictionary.

## Tests in the patch

- Exporting a module with an image includes `|alt`.
- Importing a CSV with a `|alt` translation stores it in the section translation's content, leaves the caption alone, and resets the translation to DRAFT.
- An unknown key is still rejected.

## How the HFW import uses it

- `scripts/import_hfw_content.py` checks whether `flatten()` exposes `alt`.
- **When it does:** the script adds the rows of `<language>/alt_text.csv` to that module's translation CSV before importing.
- **When it doesn't:** the script skips those rows and reports how many were skipped.
