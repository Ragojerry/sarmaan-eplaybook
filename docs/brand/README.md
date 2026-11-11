# Brand (IHS Towers Brand Manual, Aug 2021, v1.01)

The app and the admin portal take every colour, the font stack, the type scale, spacing, radius and the partner logos from one place: `brand/` at the repository root.

| File | What it holds |
|---|---|
| `brand/tokens.json` | The one token file: palette, tints, semantic roles (`primary`, `errorText`, ...), font stack, type scale, spacing, radius |
| `brand/logos.json` | Logo order, placements (splash, login, about, admin header and footer), row heights, partnership line |
| `brand/logos/` | The supplied logo files, unmodified |

## Changing something

1. Edit `brand/tokens.json` or `brand/logos.json`.
2. Run `python scripts/brand_sync.py`. It writes:
   - `mobile/lib/theme/brand_tokens.g.dart`;
   - `mobile/android/.../values/brand_colors.xml`;
   - `mobile/assets/brand/`;
   - `admin/src/brand/`;
   - `admin/public/brand/`.
3. Run `python scripts/brand_contrast.py --write`. It exits 1 if any text or control pair drops below WCAG 2.1 (4.5:1 for text, 3:1 for large text and controls), and rewrites `contrast_report.md`.
4. CI or a reviewer can run `python scripts/brand_sync.py --check`. It exits 1 if a generated copy is stale.

To change the logo order or the lead brand, edit `order` in `brand/logos.json` (or a placement's own `logos` list). No code changes are needed.

## Rules the code follows
- **Widgets use semantic colours** (`AppColors.primary`, `AppColors.errorText`, ...), never hex values. The admin uses Tailwind classes, whose palette is replaced by the tokens (`admin/tailwind.config.js`).
- **Red, Orange, Blue and Teal are never text colours.** They are below 4.5:1 on white, so they are bars, borders, icons or tints, with Forest Green text.
- **Indicating colours carry meaning only:**
  - success = Grass Green;
  - warning = Orange;
  - error and "Do not" = Red;
  - information = Blue.
- **Logos** are never larger than their own pixels. IHS is at least 95 dp wide. Clear space is the width of the IHS "I". Logos always sit on white.

## Reports
- `brand_compliance.md`: the checklist.
- `contrast_report.md`: every pair and its ratio.
- `open_questions.md`: decisions for the programme.
- `CHANGES.md`: every file touched.

## Screenshots (`screenshots/before`, `screenshots/after`)

**How they were taken:**
- **App:** the Android 15 emulator (1080 × 2400, 2.625×) running a debug build against a local backend with local test data. A test learner, M1 with three True/False statements, and the General test switched on locally; production was not touched.
- **Admin:** headless Edge at 1440 × 900.
- **Fonts:** the app uses Roboto (Android's fallback for Helvetica Neue) and the admin uses Arial (the Windows fallback).

| Screen | Before | After |
|---|---|---|
| Android launch screen | `before/app_launch_native.png` | `after/app_launch_native.png` |
| Splash | `before/app_splash.png` | `after/app_splash.png` |
| Login | `before/app_login.png` | `after/app_login.png` |
| Login error | `before/app_login_error.png` (wrong password) | `after/app_login_error.png` (empty field) |
| Language | `before/app_language.png` | `after/app_language.png` |
| Home | `before/app_home.png` | `after/app_home.png` |
| Module list | `before/app_modules.png` | `after/app_modules.png` |
| Lesson | `before/app_lesson.png` | `after/app_lesson.png` |
| Quiz (General pre-test) | `before/app_quiz.png` | `after/app_quiz.png` |
| Result | `before/app_result.png` | `after/app_result.png` |
| Inline quiz, wrong answer | `before/app_quiz_wrong.png` | `after/app_quiz_wrong.png` |
| Inline quiz, passed | `before/app_quiz_passed.png` | `after/app_quiz_passed.png` |
| Completed module | `before/app_completed.png` | `after/app_completed.png` |
| Module list with a completed module | `before/app_modules_completed.png` | `after/app_modules_completed.png` |
| Home with a completed module | `before/app_home_completed.png` | `after/app_home_completed.png` |
| About (logos) | `before/app_about.png` | `after/app_about.png` |
| Restart dialog | — | `after/app_restart_dialog.png` |
| Hausa glyph test | `before/app_hausa_lesson.png` | `after/app_hausa_lesson.png` |
| Admin login | `before/admin_login.png` | `after/admin_login.png` |
| Admin dashboard | `before/admin_dashboard.png` | `after/admin_dashboard.png` |
| Admin content | `before/admin_content.png` | `after/admin_content.png` |
| Admin General test | `before/admin_general_test.png` | `after/admin_general_test.png` |
| Admin reports | `before/admin_reports.png` | `after/admin_reports.png` |

**Hausa glyph check (font files):** coverage of ɓ Ɓ ɗ Ɗ ƙ Ƙ ƴ Ƴ ʼ, ā ē ī ō ū Ā, à â and the combining grave, circumflex and macron (20 characters):

| Font | Covered |
|---|---|
| Roboto (Android emulator system font) | 20/20 |
| Arial regular and bold (Windows) | 20/20 |
| Manrope (old body font) | 8/20 |
| Fraunces (old headings) | 12/20 |
| JetBrains Mono (old labels) | 12/20 |

## APK size (release, `flutter build apk --release`, same API URL)

| | Bytes |
|---|---|
| Before: 0.1.12 as published (SHA-256 `aa558c20…04fbe1`) | 62,722,600 |
| After: rebrand branch | 62,489,561 |
| Difference | −233,039 (≈ −228 KB: three bundled font families removed, about 223 KB of logos added) |
