# Brand compliance checklist

Checked against the IHS Towers Brand Manual (Aug 2021, v1.01, all 35 pages), for the mobile app and the admin portal on branch `rebrand`.

Legend:
- ✅ meets the guide;
- ⚠️ meets it with a stated limit;
- ❌ not done, see the note.

## 1. Palette

| Check | Result | Where |
|---|---|---|
| One token file for colours, type scale, spacing and radius | ✅ | `brand/tokens.json`. App: generated `mobile/lib/theme/brand_tokens.g.dart` and `values/brand_colors.xml`. Admin: `admin/src/brand/tokens.json`, read by `tailwind.config.js` and `src/brand/tokens.ts`. `python scripts/brand_sync.py --check` fails if any copy is out of date. |
| Forest Green `#002D14` with white is the core | ✅ | Primary buttons, app bars, splash, admin navigation, headings |
| White is `#FFFFFF` (the guide prints `#000000` by mistake) | ✅ | `palette.white` |
| Red and Grass Green used sparingly | ✅ | Red: error and "Do not" warnings, the wrong quiz answer, destructive buttons (as borders only). Grass Green: success (completed ticks, correct answers, "Correct.") |
| Neutrals | ✅ | Light Grey: dividers and card outlines. Light Grey 20%: muted panels and locked cards. Dark Grey: body text. Dark Grey 80% tint: secondary text and field borders |
| Indicating colours only with a purpose, never decoration | ✅ | Blue: information callouts (job aids), BETA badges, "update available". Orange: warning status (update available on the Updates screen; left bar of the AI "not matched" answer). Teal: not used in the app; in the admin only behind the old `teal` class names, as a surface. The old decorative gold bars were replaced with Forest Green. |
| Tints | ⚠️ | Guide tints used: Forest 40%, Grass 50%, Teal 60%, Orange 60%, Blue 50%, Light Grey 20%. Derived with the same mixing rule (not printed in the guide): Forest 10% and 85%, Grass 10%, Orange 15%, Blue 10%, Red 10% and 40%, Light Grey 40%, Dark Grey 80%. All are listed in `tokens.json` → `_tints_note` and in `admin/tailwind.config.js`. |
| No old palette left | ✅ | See section 7 |
| Gradients | ✅ | The guide has none; the six teal gradients were replaced by flat Forest Green |

## 2. Fonts

| Check | Result | Notes |
|---|---|---|
| Helvetica Neue first, fallbacks Helvetica (Apple) and Arial (Windows) | ✅ | App: `fontFamily: 'Helvetica Neue'`, fallback Helvetica, Arial, Roboto, Noto Sans. Admin: `"Helvetica Neue", Helvetica, Arial, sans-serif` |
| Plain Helvetica never used where Helvetica Neue exists | ✅ | Helvetica only comes after Helvetica Neue in the stack |
| Licensed font not bundled | ✅ | Fraunces, Manrope and JetBrains Mono were unregistered from `pubspec.yaml`; nothing new was bundled |
| What users actually see | ⚠️ | iOS: Helvetica Neue. Android: Roboto (no phone ships Helvetica Neue). Admin on Windows: Arial (see the screenshots). Admin on Mac: Helvetica Neue. |
| Hausa letters | ✅ Android and Windows / ⚠️ iOS not checked | Font coverage of ɓ Ɓ ɗ Ɗ ƙ Ƙ ƴ Ƴ ʼ and the long-vowel and tone marks (20 characters): Roboto (Android 15 emulator) 20/20; Arial 20/20. The removed fonts covered Manrope 8/20, Fraunces 12/20 and JetBrains Mono 12/20, so Hausa used to fall back mid-word; now it renders in one font. No extra fallback font is needed. iOS was not checked (no Mac): iOS substitutes missing letters per character automatically. Screenshots: `before/hausa_lesson.png`, `after/hausa_lesson.png`. |
| Widgets do not set their own font | ✅ | Every `fontFamily:` was removed from screens; text inherits the theme |

## 3. Logos

| Check | Result | Notes |
|---|---|---|
| Files used as supplied | ✅ | `brand/logos/*` are byte-identical to the supplied files (checked with `cmp`); the app and admin copies are byte-identical too (`brand_sync.py --check`) |
| Fragment file (red arc) not used | ✅ | Not copied |
| No distortion | ✅ | Width is always calculated from the file's own aspect ratio; `BoxFit.contain` / `object-fit: contain` |
| No recolouring, rotation, effects or shadows | ✅ | None applied (the old shadow on the login mark was removed) |
| Not upscaled | ✅ | Each logo is capped at its own pixel size (`heightPx / devicePixelRatio`). Because of this, SARMAAN-II shows smaller than the others; see open_questions.md §3 |
| IHS clear space = width of the "I" | ✅ | `clearSpaceRatio` 0.165 (275 px "I" / 1668 px logo), applied around the row and between logos, for all four logos |
| IHS minimum width 95 px | ✅ | `minWidthDp: 95`; row height 54 dp gives IHS 95 dp wide |
| Approved backgrounds | ✅ | The supplied IHS file is the full-colour primary logotype, which goes on white or light grey only, so every logo row sits on white, including the white band on the Forest Green splash. A white reversed version was not supplied (open_questions.md §3) |
| Without-strapline version only when too small | ✅ | Not used (and not supplied) |
| Same visual height in a row | ⚠️ | All logos are at 54 dp except SARMAAN-II, which is capped at its 118 × 50 px file (≈ 19 dp on a 2.6× phone) |
| Order and positions in one config file | ✅ | `brand/logos.json`: order, placements (splash, login, about, adminHeader, adminFooter), row heights and the partnership line |
| Bundled, no remote images | ✅ | App: `assets/brand/`. Admin: `public/brand/` (served by the portal itself) |
| No logo altered to make a launcher icon | ✅ | Launcher icon unchanged |
| Lead brand and order not decided in code | ✅ | Placeholder order = supplied order, marked `UNCONFIRMED` |

## 4. Connectivity graphic and icons

| Check | Result | Notes |
|---|---|---|
| Connectivity graphic | ❌ (by instruction) | Skipped: no graphic file was supplied, and drawing it from the description would be guessing |
| IHS icon style not copied | ✅ | Existing Material icons kept, recoloured with tokens |

## 5. Contrast

All text and control pairs pass. The full table with every ratio is in `contrast_report.md`, generated by `scripts/brand_contrast.py`, which exits non-zero if any pair fails. These adjustments were made because the guide's colours fail as text:

| Pair | Ratio | Adjustment |
|---|---|---|
| Red text on white | 3.57 | Error and "Do not" text is Forest Green; Red is the border, bar or tint |
| White text on Red (old "danger" buttons) | 3.57 | "Start over" and "Sign out" keep a white or Forest fill with a Red border |
| Orange text or icon on white | 2.73 | Warning text is Forest Green on Orange 15%; the Orange bar is decorative |
| Teal on white | 2.65 | Not used as text or as an icon |
| Blue text on white | 3.90 | Information text is Forest Green on Blue 10%; Blue is the border, bar or icon (3.90 ≥ 3 for icons) |
| Mid Grey text on white | 2.38 | Secondary text uses Dark Grey 80% (5.35); Mid Grey only for disabled items |
| Old wrong-answer text (clay `#B5652F`, about 4.0) | — | Now Forest Green |
| Old muted text (`#7C8A83`, about 3.6) | — | Now Dark Grey 80% (5.35) |
| Answered quiz buttons (disabled grey text) | about 2.4 | The chosen answer keeps Forest Green text |
| Admin sidebar labels on Forest Green | 2.83 if Dark Grey 80% | Light Grey (9.81) or white |

## 6. Not changed (as instructed)

Lesson text, translations, clinical content and app behaviour are unchanged:
- The diff touches only styling, the logo widget and screen layout around it.
- The mobile test suite passes (182/182).
- The admin type-check and build pass.

## 7. Search for old palette codes

Command (from the repository root):
```
grep -rniE "0B5D51|08322C|E4EEEA|E8A93C|B5792A|F4EFDF|E9DFC0|B5652F|F3E2D3|B23B3B|16241F|5B6B62|7C8A83|334039|5B3A1F|0D3F37|1E3D37|123F38|7FE0B0|B7C0BA|0F7A4C|93c5fd|Fraunces|Manrope|JetBrains|AppColors\.(teal|gold|sand|clay|ink|danger)" mobile/lib mobile/android/app/src/main/res admin/src admin/index.html admin/tailwind.config.js content
```
Result: no matches (see the change list for the run).

## Revision 2026-11-11

| Check | Result |
|---|---|
| Base | ✅ Forest Green with Light Grey 20% page background (decision) |
| Fonts | ⚠️ By decision the app uses its original fonts (Fraunces / Manrope / JetBrains Mono) and the admin its original system stack, not the guide's Helvetica Neue. Hausa letters fall back to the system font (Manrope 8/20, Fraunces 12/20 coverage) |
| Contrast on the grey page | ✅ All pairs pass (`contrast_report.md`). Grass Green text is 4.30 on the grey page, so it is used only on white cards (the one use is "Correct." in the quiz card) |
| Logo order | ✅ IHS first (decision) |
| Launcher icon | ⚠️ SARMAAN-II logo, unmodified, centred on white, downscaled only. From the 118 × 50 px file it is small in the icon and its "PROJECT" line is unreadable at launcher size; a vector file is needed for a full-size icon |
| Login mark | ⚠️ SARMAAN-II logo at its own pixel size (≈ 45 × 19 dp on a 2.6× phone) |
| Tab header logo | ⚠️ By decision (2026-11-11) the IHS logo at the top of the Home, Modules, Videos, Ask and About tabs is 36 dp high, 63 dp wide: below the guide's 95 px minimum width. Clear space (width of the "I") is kept at that size; the band is 58 dp. Set in `brand/logos.json` → `placements.tabHeader` (`minWidthDp: 0`); every other placement keeps the 95 dp minimum |
