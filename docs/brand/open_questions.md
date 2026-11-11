# Rebrand: open questions

These need a decision from the programme. Nothing below was decided in the code: each one is either left as it was, or set to a clearly marked placeholder in `brand/logos.json`.

## 1. Logo order and lead brand. DECIDED 2026-11-11: IHS first
`brand/logos.json` → `order` currently lists the logos in the order the files were supplied: Malaria Consortium, SARMAAN-II Project, GF, IHS Towers. This is a placeholder (`status: UNCONFIRMED`).

**Decide:** which logo leads, and in what order. To apply it, change `order` (or a placement's own `logos` list) and run `python scripts/brand_sync.py`. No code changes are needed.

## 2. Partnership wording
The login screen, the About screen and the admin footer show **"In partnership with"** above the logo row. This is a placeholder (`partnershipLine.status: UNCONFIRMED`).

**Decide:** the wording ("In partnership with", "Developed with", or other).

## 3. Logo files: resolution and vectors
| Logo | File supplied | Problem | Needed |
|---|---|---|---|
| SARMAAN-II Project | PNG, 118 × 50 px | Too small. It can't be shown at the row height without being enlarged, which the rules forbid. The app caps it at its own pixel size, so it shows **shorter than the other logos**, and at about 18 dp tall on a typical phone its small text is hard to read. | Vector (SVG/PDF/EPS) or PNG at least 600 px tall |
| GF | PNG, 228 × 158 px | Usable up to about 57 dp tall on a 2.75× phone; larger rows would blur. | Vector or PNG at least 600 px tall |
| Malaria Consortium | JPG, 1432 × 677 px | Big enough, but JPEG: the edges have compression artefacts and the coloured background is part of the file. | Vector, or PNG with a transparent background if their guidelines allow |
| IHS Towers | PNG, 1668 × 948 px (primary, two-colour) | Big enough. The guide's **white reversed** and **secondary single-colour** versions were not supplied. Because of this the logo can only go on white or light backgrounds, so the splash puts the logo row on a white band. | White reversed logotype and secondary (Forest Green 90%) logotype files; the "without strapline" version if small placements are wanted |
| IHS fragment (red arc) | PNG | Not used, as instructed. | — |

## 4. What the "GF" logo is
The file was described as the Gates Foundation "GF". We could not confirm that this gold-on-slate "GF" mark is the Gates Foundation's current logo. **Please confirm it with the partner and send their official file.** It is shown under the label "GF" until then.

## 5. Each partner's usage guidelines
Only IHS supplied guidelines. For Malaria Consortium, SARMAAN-II and GF we applied the IHS rules (clear space = width of the IHS "I", no recolouring, cropping, stretching, rotation or effects). **Needed:** each partner's own logo guidelines (clear space, minimum size, approved backgrounds).

## 6. Permission to appear in the app
**Needed:** written permission from each partner (Malaria Consortium, SARMAAN-II, GF and IHS Towers) to show its logo in the app and the admin portal.

## 7. Helvetica Neue licence. Not needed now: the app keeps its original fonts (decision 2026-11-11)
Helvetica Neue is not bundled. The app asks for "Helvetica Neue" and falls back to Helvetica, then Arial, then the system sans:
- iOS has Helvetica Neue.
- Android has none of the three and uses Roboto.
- The admin portal uses whatever the viewer's computer has (Helvetica Neue on Mac, Arial on Windows).

**Decide:** whether to license Helvetica Neue for app embedding. Only then can Android show it.

## 8. Launcher icon. DECIDED 2026-11-11: SARMAAN-II logo (needs a vector or 512 px file to fill the icon; the current one is built from the 118 × 50 px PNG)
Not changed. The launcher icon was not altered, and no logo was cropped or changed to make one. **Decide:** whether a new launcher icon is wanted, and who designs it (it must not be made by altering a partner logo).

## 9. Dark mode
The app has no dark mode today, and none was added. The guide has no dark palette. **Decide:** whether one is needed. If so, it would be derived from Forest Green and marked as not covered by the guide.

## 10. Training video cards
The request asked to re-skin the training video cards (title, step, dosing table, warning, closing). **These cards are not in this codebase.** The app plays uploaded video files, so the cards are drawn inside the videos themselves. Re-skinning them means re-editing the video source files in the video editing project. **Needed:** that project, or the person who produces the videos, plus a decision on whether the existing videos are re-rendered.

## 11. Connectivity graphic
Not used. The guide describes it (seven white wave lines, 0.3 pt, 80% opacity), but no graphic file was supplied, and drawing it from the description would be guessing. **Needed:** the official Connectivity graphic file (SVG), if it is wanted on the splash screen or module covers.

## 12. iOS
There is no iOS build or Mac here, so nothing was checked on iOS, including the Hausa letters in Helvetica Neue. **Needed:** a check on an iPhone before an iOS release.

## 13. Old font files. RESOLVED: in use again (decision 2026-11-11)
Fraunces, Manrope and JetBrains Mono are no longer registered, so they are not in the APK. The files are still in `mobile/assets/fonts/`, because nothing is deleted without asking.

**Decide:** whether to remove them.

## 14. Error text in the admin portal
Brand Red fails 4.5:1 as text, so error messages and "Delete" links that were red text (`text-red-600`) are now Forest Green. Where a message sits in a box, the box keeps a Red tint and border; plain error text on white now has no colour cue.

**Decide:** whether to add an error icon or a Red left bar to those messages, which is a small follow-up.

## 15. Admin header and footer
The admin shows the logo row both above and below each page, as asked. The header row is 54 px tall, because of the IHS minimum width.

**Decide:** whether both are wanted, or only one.
