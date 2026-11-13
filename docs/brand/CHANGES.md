# Rebrand: files touched (branch `rebrand`)

The branch starts from commit `8ddaf9a` (the go-live code as deployed on 2026-11-11). Nothing was merged, pushed or deployed, and no production or learner data was touched.

## New
| File | Purpose |
|---|---|
| `brand/tokens.json` | The one design-token file (colours, tints, semantic roles, font stack, type scale, spacing, radius) |
| `brand/logos.json` | Logo order, placements, row heights, partnership line (order and wording marked UNCONFIRMED) |
| `brand/logos/malaria_consortium.jpg`, `sarmaan_ii_project.png`, `gf.png`, `ihs_towers_primary.png` | The supplied logo files, byte-identical |
| `scripts/brand_sync.py` | Generates or copies the tokens and logos into the app and admin; `--check` for CI |
| `scripts/brand_contrast.py` | WCAG contrast for every pair; writes `docs/brand/contrast_report.md` |
| `mobile/lib/theme/brand_tokens.g.dart` | Generated Dart tokens |
| `mobile/lib/widgets/partner_logo_row.dart` | Config-driven logo row (no upscaling, IHS minimum width, "I" clear space, white background) |
| `mobile/assets/brand/*` | Bundled copies of the logos and `logos.json` |
| `mobile/android/app/src/main/res/values/brand_colors.xml` | Generated Forest Green and white for the native launch screen |
| `mobile/android/app/src/main/res/values-v31/styles.xml` | Android 12+ system splash background (Forest Green) |
| `admin/src/brand/tokens.json`, `admin/src/brand/logos.json` | Copies for the admin (synced) |
| `admin/src/brand/tokens.ts` | Token colours for chart fills |
| `admin/src/components/PartnerLogos.tsx` | Config-driven logo row for the admin |
| `admin/public/brand/*` | The logos served by the admin portal |
| `docs/brand/README.md`, `brand_compliance.md`, `contrast_report.md`, `open_questions.md`, `CHANGES.md` | Documentation |
| `docs/brand/screenshots/before/*`, `docs/brand/screenshots/after/*` | 45 screenshots |

## Changed: mobile
| File | Change |
|---|---|
| `mobile/pubspec.yaml` | Fraunces, Manrope and JetBrains Mono unregistered; `assets/brand/` added |
| `mobile/lib/theme/app_theme.dart` | Rewritten on the tokens: semantic `AppColors`; Helvetica Neue stack; white dialogs and sheets; button padding; input, checkbox, progress and snackbar themes; error text in Forest Green |
| `mobile/lib/screens/splash_screen.dart` | Forest Green title area plus a white logo band (`PartnerLogoRow('splash')`); gradient removed |
| `mobile/lib/screens/login_screen.dart` | Logo row and partnership line at the bottom; mark kept square (it was stretched full width); error box Red bar with Forest text; gradient and shadow removed |
| `mobile/lib/screens/about_screen.dart` | Logo row and partnership line; restart and sign-out buttons re-coloured (Red border, Forest text) |
| `mobile/lib/screens/home_screen.dart` | Header gradient → Forest Green; badges, update banner and "update" pill → information Blue tint; completed tick → Grass Green; FAB → Forest Green |
| `mobile/lib/screens/reader_screen.dart` | Callouts: warning = Red, job aid = Blue, callout = Forest; True/False answers: correct = Grass Green, wrong = Red, chosen text keeps full contrast; completed card → Grass Green; audio button gradient → Forest Green |
| `mobile/lib/screens/modules_screen.dart`, `quiz_screen.dart`, `language_screen.dart`, `consent_screen.dart`, `ai_screen.dart`, `updates_screen.dart`, `update_required_screen.dart`, `video_screen.dart`, `video_library_screen.dart` | Old palette → semantic tokens; fonts inherited from the theme; gradients → Forest Green; BETA badge → information Blue |
| `mobile/lib/widgets/authenticated_image.dart`, `offline_aware_image.dart`, `section_audio_player.dart` | Grey placeholders and white icons → tokens |
| `mobile/android/app/src/main/res/drawable*/launch_background.xml`, `values/styles.xml`, `values-night/styles.xml` | Native launch screen Forest Green (was black); window background white. The launcher icon is unchanged. |

## Changed: admin
| File | Change |
|---|---|
| `admin/tailwind.config.js` | Palette replaced by the tokens (existing class names now resolve to brand colours; text shades accessible); brand font stack; `brand-*` semantic names |
| `admin/src/layouts/AdminLayout.tsx` | Forest Green sidebar, white active item; logo header and footer |
| `admin/src/pages/LoginPage.tsx` | Logo footer with partnership line |
| `admin/src/pages/DashboardPage.tsx`, `AnalyticsPage.tsx` | Chart fills from tokens (Forest Green, Grass Green 50%) |

## Not changed
- **Content and behaviour:** lesson text, translations, clinical content, backend, data, and app behaviour.
- **Launcher icon.**
- **Font files:** `mobile/assets/fonts/*.ttf` (no longer registered, so not in the APK; left on disk, see open_questions.md §13).
- **`mobile/android/gradle/wrapper/gradle-wrapper.properties`:** local change, kept out of the commit as before.

## Checks run
| Check | Result |
|---|---|
| `flutter analyze` | No errors (2 older infos, not from this change) |
| `flutter test` | 182/182 passed |
| `npx tsc -b && npx vite build` (admin) | Pass |
| `python scripts/brand_contrast.py` | All pairs pass |
| `python scripts/brand_sync.py --check` | Up to date |
| Old-palette search | No matches (command in brand_compliance.md §7) |
| Raw colour literals | 0 in Dart outside the generated token file; 0 hex values in admin source outside `src/brand/` |
| Release APK | 62,722,600 → 62,489,561 bytes |

## Revision 2026-11-11
| File | Change |
|---|---|
| `brand/tokens.json` | Page background → Light Grey 20%; font section → Manrope / Fraunces / JetBrains Mono with Roboto and Noto Sans fallback; each type style names its family |
| `brand/logos.json` | Order: IHS, Malaria Consortium, SARMAAN-II, GF |
| `scripts/brand_sync.py` | Generates the three font families |
| `scripts/brand_contrast.py` | Pairs for the grey page and white cards |
| `mobile/pubspec.yaml` | Fonts registered again |
| `mobile/lib/theme/app_theme.dart` | `AppFonts.serif/sans/mono` restored; base family Manrope |
| `mobile/lib/screens/*.dart`, `widgets/section_audio_player.dart` | The per-screen Fraunces and JetBrains Mono styles restored exactly as in 8ddaf9a (3-way merge, 26 of 27; login's "S" is now the logo) |
| `mobile/lib/screens/login_screen.dart`, `widgets/partner_logo_row.dart` | `SarmaanLogoMark` replaces the "S" |
| `mobile/android/app/src/main/res/mipmap-*/ic_launcher.png` | SARMAAN-II launcher icon (48–192 px) |
| `admin/tailwind.config.js` | Original system font stack |
| `docs/brand/screenshots/revision2/*` | New screenshots |

## Follow-ups 2026-11-11
| File | Change |
|---|---|
| `mobile/lib/screens/home_screen.dart` | Locked modules no longer appear under "Continue reading", and their cards show no progress bar |
| `mobile/lib/screens/login_screen.dart` | Title "SARMAAN II e-Playbook"; eyebrow "Sign in" (was "Admin & CDD sign in") |
| `mobile/lib/screens/home_screen.dart` | Header greets the user by first and last name (was role and team); title "Welcome to SARMAAN II Training Session" (was "Ready for today's round") |
| `brand/logos.json` (and its synced copies) | New `tabHeader` placement: IHS alone, row height 54 dp |
| `mobile/lib/widgets/partner_logo_row.dart` | `BrandTopBar`: the `tabHeader` logo in a white band under the status bar (dark status icons), above the screen's own title bar; fixed while the page scrolls |
| `mobile/lib/screens/home_screen.dart`, `modules_screen.dart`, `video_library_screen.dart`, `ai_screen.dart`, `about_screen.dart` | IHS logo at the top of each tab (`BrandTopBar`) |
| `brand/logos.json`, `partner_logo_row.dart` | Tab header made smaller by decision: logo 36 dp high (63 dp wide, below the IHS 95 dp minimum), band 86 → 58 dp; a placement's `minWidthDp` now overrides the logo's |
| `mobile/lib/screens/splash_screen.dart`, `mobile/lib/main.dart`, `mobile/android/app/src/main/AndroidManifest.xml` | App name "SARMAAN II e-Playbook" on the splash, in the app title and under the launcher icon (was "SARMAAN e-Playbook") |
| `mobile/lib/screens/splash_screen.dart` | The "S" mark replaced by the SARMAAN-II logo (`SarmaanLogoMark`, on white), matching the login screen |

## Decisions 2026-11-12
| File | Change |
|---|---|
| `brand/logos.json` (and copies), `mobile/lib/widgets/partner_logo_row.dart`, `admin/src/components/PartnerLogos.tsx` | "In partnership with" removed: logo rows show the logos only |
| `docs/brand/open_questions.md` | §2 partnership wording decided (none); §4 GF logo confirmed |
| `mobile/pubspec.yaml`, `mobile/assets/fonts/Arimo-*.ttf`, `OFL-Arimo.txt` | App fonts unchanged (Fraunces, Manrope, JetBrains Mono): Arimo was tried for all text and reverted the same day by decision. Arimo (SIL OFL 1.1) is bundled only for the certificate PDF, so learners' names with ɓ ɗ ƙ ƴ print correctly. |

## IHS Teal base (2026-11-12)
| File | Change |
|---|---|
| `brand/tokens.json` (and generated copies) | Base colour IHS Teal `#05B39C` (decision, after the IHS report layout). New: `primaryText` deep teal `#037D66` (Teal blended with Forest Green; small accent text and fills behind small white text), `teal10`/`teal20`/`teal80` tints, sheen colours, radii +2 |
| `mobile/lib/theme/app_theme.dart` | Teal app bars with white bold titles; `AppSheen` (hero and button gradients, glossy top edge, soft teal card shadows and glow); filled buttons get the sheen |
| `mobile/lib/screens/*` | Hero header, splash, video tiles on the Teal gradient; small teal text in deep teal; card shadows |
| Android launch screen | `brand_primary` (Teal) instead of Forest Green |
| `admin/` | Deep-teal-to-Teal sidebar, deep teal buttons with gloss, soft card shadows (all via tokens) |
| `scripts/brand_contrast.py`, `contrast_report.md` | White on Teal (2.65:1) and Teal titles on the page recorded as **accepted by decision**; every other pair passes |

## Palette of 2026-11-12 (replaces the IHS Teal base the same day; visual only)
Forest `#245C3E`, deep forest `#1F5035` (bottom navigation), logo teal `#00685C` (primary), mid-blend `#14614C`, background `#D9E8E7`, gold `#F2A33A`; supporting ink `#1F2A28`, muted `#43544F`, card `#F2F8F7` with a `rgba(0,104,92,0.18)` border (stored opaque as `#C6DEDB`), pale teal `#E6F2F0`, warning `#C2410C`, error `#B42318`. The subtle sheen is kept in the new colours. Every text pair passes 4.5:1 (no pair "accepted by decision" any more).

| File | Change |
|---|---|
| `brand/tokens.json` (and generated copies) | New palette and roles; the IHS palette, tints and teal blends removed |
| `scripts/brand_sync.py` | Android `brand_deep_forest` |
| `mobile/lib/theme/app_theme.dart` | New roles (`forest`, `deepForest`, `midBlend`, `gold`, `onGold`, `onPrimaryMuted`, `nav*`); forest-to-teal hero gradient, `photoFade` for a future hero photo; deep forest bottom bar with a white pill; deep forest snack bars |
| `mobile/lib/screens/home_screen.dart` | "Continue" hero card (forest to teal, gold label, gold Continue button, gold progress on a 28% white track); module states: completed forest disc with a white tick, next module teal 2 dp outline with a gold number, locked dashed teal outline with muted text |
| `mobile/lib/screens/modules_screen.dart`, `mobile/lib/widgets/module_state_marks.dart` | The same three states in the Modules list |
| `mobile/lib/screens/*` | Card surfaces `#F2F8F7` instead of white (white kept only behind partner logos and the certificate preview) |
| `mobile/lib/widgets/partner_logo_row.dart` | Deep forest system navigation bar (logo band stays white: logos are approved on white) |
| Android `launch_background.xml`, `values*/styles.xml` | Forest-to-teal launch gradient; forest status bar and Android 12+ splash; deep forest navigation bar |
| `admin/tailwind.config.js`, `src/index.css`, `src/layouts/AdminLayout.tsx`, `src/components/PartnerLogos.tsx`, `src/brand/tokens.ts` | Forest-to-deep-forest sidebar with pale teal secondary text, teal buttons, `#D9E8E7` page, `#F2F8F7` cards, status colours from the palette, charts teal and gold; `bg-paper` (white) only behind logos |
| `scripts/brand_contrast.py`, `contrast_report.md` | Pairs for the new palette |
| `brand/tokens.json`, `app_theme.dart`, `home_screen.dart`, `modules_screen.dart`, `admin/src/brand/tokens.ts` | Same day, by decision: the gold accent replaced by the pale teal tint `#D9E8E7` (token `accent`, dark text `onAccent`) on the hero card and the Online dot; the next module's number badge is logo teal with a white number (pale teal does not show on cards); admin charts teal and Forest Green |
| `app_theme.dart` (`AppSheen.header`), `home_screen.dart`, `splash_screen.dart`, Android `launch_background.xml` | Same day, by decision: Home header, splash and launch screen Forest Green to deep forest; the Continue card and banners stay Forest Green to logo teal |
| `brand/logos.json` (and copies), `partner_logo_row.dart` | Malaria Consortium added to the tab header band after IHS, 32 dp apart (new placement setting `gapDp`) |
