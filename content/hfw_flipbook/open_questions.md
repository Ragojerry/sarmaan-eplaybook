# Open questions: HFW flipbook (items still undecided)

Page numbers are HFW PDF pages; the printed page number is one lower.

**Already decided, so removed from this list:**

- **Module split:** audience per module, 17 modules. See `modules.csv`.
- **First and only content:** the HFW modules are treated as the first content; M1–M6 are deleted.
- **Learning order:** General modules first, then the learner's role modules.
- **Credit:** none. All training history is test data and is wiped, so every user starts from nothing.
- **Staging:** no staging server. Dry run locally, then run on production with a verified backup; rollback is a restore.
- **Quiz length:** 10 questions per module.

See `migration_plan.md`.

## A. Changeover and launch

**A1. `CUTOVER_DATE`.**
- Not chosen.
- The programme owner sets it in production configuration.
- The cutover script refuses production without it.

**A2. Minimum app version.**
- App 0.1.9 handles the changeover correctly (`offline_and_app_version_tests.md`), so `MIN_APP_VERSION` can stay unset.
- **Decision needed:** require 0.1.10 at launch, to guarantee the one-time notice and the clearer messages; or later; or never.

**A3. App 0.1.10.**
- The version is set to 0.1.10+11 in the code, but no APK has been built or published.
- Build it and test it on a phone first (runbook 1.3).
- Publishing the production APK is a separate step.

**A4. Apps older than 0.1.8 in the field.**
- They can't do the new pre-/post-tests.
- Confirm none are in use (runbook 4.6).

**A5. Importer patch for translated alt text.**
- It is on branch `importer-alt-text` and not merged (`alt_text_importer_spec.md`).
- It is needed before Hausa alt text is imported.

**A6. Estimated durations.**
- 15–30 minutes per module, 335 in total.
- Per role: CDD 265, Health worker 220, Monitor/supervisor 220, Other 185, Logistician 180 minutes.
- Confirm after the first real-phone run.

**A7. Branches.**
- Both merged into `main` on 2026-11-06.

## B. Clinician sign-off needed

All values below match the PDF on the second-pass check (`verification_report.md`). They are open because the **content itself** looks questionable, not because it was copied wrongly.

**Items B1, B2, B3 and C1 are on the one-page form `clinician_signoff.md`.** The programme decided on 2026-11-06 to publish without waiting for it, so the content is live exactly as printed (including the email "concenrns@"). Answers lead to a content update and a new release.

**B1. Height-based dosing table on the Child Record Card (p34).**
- The doses run 2, 4, 6, 8, 10, 12, 14, 16, then **19** and **25 ml**.
- The table starts at 50–53 cm, but it is labelled for 12–59 months.
- It ends at 137–140 cm.

**B2. Bottle arithmetic.**
- The PDF says "each bottle of AZM will be used to reach 4 children" (p30), and to multiply empty bottles by 4 (p45).
- But a bottle makes 30ml, and the height doses reach 8–25 ml.
- Is "4 children per bottle" a planning average?

**B3. Malnutrition and eligibility.**
- The eligibility chart refers children with "mild/severe/acute malnutrition" (p16).
- p13 and p15 exclude only SAM.
- MAM is "Immediate referral to health facility for counselling" (p18).
- Is a child with MAM (11.5–12.4 cm) given AZM?

**B4. Crawl/sit age band.** The p11 text says 3–11 months; the p12 picture says 5–11 months.

**B5. Integrated campaigns.** Call-in data for integrated campaigns uses 6–11 months (p42), while AZM starts at 1 month. How are 1–5 month olds counted?

**B6. Repeat vomiting.** The book says to redose once if the child vomits within 5 minutes. It does not say what to do if the child vomits again.

**B7. Partly used bottle.** Viability is now "2 to 3 days" (it was 2 days). Are there storage conditions?

**B8. What SAE stands for.** "Severe adverse Reaction" (p3) or "Serious Adverse Event" (p63)?

**B9. Allergy scope.** "Macrolide antibiotics" (p13) or "similar antibiotics" (elsewhere)?

**B10. Quiz questions.** The 170 questions reuse these values and need the same sign-off.

## C. Wording conflicts and typos

**C1. Top priority: the safeguarding email.**
- The PDF prints **concenrns@malariaconsortium.org** (p87).
- Earlier materials use **concerns@malariaconsortium.org**.
- The content uses the PDF spelling. Confirm before publishing.

**C2. House-mark code (p35–36).**
- The rule says "CDD team code (4 digits)", but every example uses 56708 (5 digits).
- `021` (the house number in the CDD book) is no longer explained.
- An R/C example appears, but R/C is not in the status list.
- The photo shows AZM/25/1, with a 6 pasted over the 5.

**C3. Round numbering.**
- House mark: rounds 1–6 (p36).
- Referral form: rounds 1–6 in the CDD part, 1–2 in the health-facility part (p26).
- Child Record Card: round 1 or 2 per year (p34, p50).

**C4. Two Child Record Card versions** (p34, p49). "Last Polio" (p51) is on neither card.

**C5. Two data systems.** Kobo Collect (MUAC p17, call-in data p42) and DIGIT HCM (treatment).

**C6. "Seasonal Malaria Chemoprevention (SMS)" (p8).** The acronym was left out of the app text. Restore it?

**C7. Printed oddities kept as they are.**
- The referral-form age box reads "1 11 month:"; no dash is visible at 600 dpi (p26).
- The card message is cut off: "…during all" (p34).
- Contents page numbers are one too low from M4 onwards (p2).

**C8. Spelling corrected in the app text (9).** Please review:

| Page | Printed | In the app text |
|---|---|---|
| p13 | "Do NT give" | "Do NOT give" |
| p15 | "Visible sever wasting" | "severe" |
| p17 | "MAUC" | "MUAC" |
| p34 | "doing strategy (age of height-based)" | "dosing strategy: age-based or height-based" |
| p35 | "later 'R'" | "letter 'R'" |
| p64 | "a free smart phone for reporting" | "a free smartphone app" |
| p68 | "How was the medium administered" | "How administered" |
| p80 | "DIGIT GCM" | "DIGIT HCM" |
| p83 | "medicined" | "medicines" |

"Lots Quality Assurance Sampling" and "Severe adverse Reaction" stay as printed.

**C9. p88 photo captions.** Camera and phone photos are matched to "Avoid taking pictures without consent"; the money photo to "Avoid bribery…".

**C10. The PV form** is mentioned on p22 but not shown in the PDF.

## D. Image rights and consent

Details are in the `rights_or_consent_flag` column of `images_manifest.csv`.

- **Getty Images credit:** visible on `m9_p88_03.jpg` (Dan Kitwood/Getty Images).
- **AI-generator sparkle watermark:** on 7 images: `m1_p05_01`, `m2_p09_01`, `m3_p21_01`, `m4_p39_01`, `m4_p41_01`, `m6_p73_01` and `m8_p81_01`.
- **Identifiable children and adults:** `m4_p28_01`, `m9_p84_01`, `m7_p77_01`, `m2_p20_01`, `m4_p35_01` (edited) and `m5_p66_01`.
- **Third-party marks:** UNICEF (`m2_p20_02`), "GLOBAL" on the truck (`m8_p81_01`), and Malaria Consortium inside `m4_p60_01`.
- **Privacy:** the NAFDAC screenshot shows someone's browser bookmarks (`m5_p64_01`). Recapture it.

## E. Unreadable or incomplete in the source

- **p20:** the MUAC tape's millimetre labels are unreadable.
- **p64:** the NAFDAC screenshot's URL and tabs are unreadable.
- **p49:** the second card version is a 403 px raster with one line hidden.
- **p39, p41, p77:** background signage is illegible.
- **p14:** the fifth "NOT Eligible" picture has no label.
- **p66:** an empty blue box sits under the photo.
- **p33:** there is no positioning picture.

## F. Hausa: not started

Hausa can start; clinician review is no longer a gate. Any clinical change later means re-translating the changed strings.

- **New phone texts in draft Hausa, for native review:**
  - the notice: "An sabunta horon. Fara sababbin darussa." ("The training has been updated. Start the new modules.");
  - the button: "To" (OK);
  - the update screen: "An sabunta horo, da fatan za a sabunta manhajar." ("Training updated, please update the app.").

- No glossary file exists. The Hausa in `module_ha_*.csv` will serve as the glossary.
- "Cup" will be "kofi" (not "kwafi"), flagged for native review.
- Codes, numbers, app names, the URL and the email stay untranslated.
- Alt text is translated in `<language>/alt_text.csv`. Loading it needs the `importer-alt-text` patch.
