# Change log: FLIPBOOK HFW (Aug 2026) against earlier content

**Compared against:**
- **CDD flipbook:** `Training Flipbook CDDs-Updated.pdf`, 65 pages.
- **Module CSVs:** `module_ha_translated_UTF8.csv` (intro), `module_ha_1.csv` (eligibility), `module_ha_4.csv` (referral), `module_ha_5.csv` (administration), `module_ha_6.csv` (IPC/SBC) and `module_ha_7.csv` (safeguarding).

The HFW PDF is the source of truth, and the new content follows it. Every conflict is listed below. Nothing in the old CSVs was overwritten: the old files are untouched in Downloads, and the new content is in `en/module_hfw_*.csv`.

**Page references:**
- "HFW p" means the PDF page of the HFW flipbook. The printed page number is one lower.
- "CDD p" means the PDF page of the CDD flipbook.
- "CSV" means the old module CSVs.

## Module map

| HFW module | HFW pages | Earlier source |
|---|---|---|
| Front matter (purpose, acronyms) | 1-4 | CDD p1-4 |
| M1 Introduction | 5-8 | CDD M1 (p5-8), `module_ha_translated_UTF8.csv` |
| M2 Eligibility + MUAC | 9-20 | CDD M2 (p9-19), `module_ha_1.csv` |
| M3 Referral | 21-27 | CDD M3 (p20-26), `module_ha_4.csv` |
| M4 Administration and recording, call-in data, accountability, Child Record Card steps, cohort tracking | 28-60 | CDD M4 (p27-56), `module_ha_5.csv` |
| M5 Pharmacovigilance, NAFDAC e-reporting, DSNOs | 61-72 | **New** |
| M6 IPC and SBC | 73-76 | CDD M5 (p57-60), `module_ha_6.csv` |
| M7 Monitoring and supervision | 77-80 | **New** |
| M8 Supply chain | 81-83 | **New** |
| M9 Safeguarding | 84-88 | CDD M6 (p61-65), `module_ha_7.csv` |

The app currently has modules M1 to M6 under the old numbering, so the module codes change when this content is loaded (see `migration_plan.md`).

## New content

- **M5 Pharmacovigilance (HFW p61-72):**
  - Drug safety, with definitions of side effect, adverse event and serious adverse event (p63).
  - Objectives of pharmacovigilance (p63).
  - The NAFDAC Med Safety app (p64).
  - Step-by-step NAFDAC e-reporting, marked "for Health Workers only" (p65-69). This includes the state codes KD, KB, JG, AD and GOM, and the link https://vigiflow-eforms.who-umc.org/ng/adr.
  - The role of DSNOs (p70-72).
- **M7 Monitoring and supervision (HFW p77-80):** what supervision is, key actions, the three levels of supervision, and competencies.
- **M8 Supply chain management (HFW p81-83).**
- **Call-in data (HFW p37-42):** expanded from one page (CDD p39). Adds:
  - why call-in data matters and its key components;
  - roles from CDD to National M&E;
  - common issues, uses and quality checks;
  - a separate set of steps for **integrated campaigns** using the age bands **6–11 months** and 12–59 months (p42).
- **Drug accountability at the facility (HFW p43-46):**
  - Issue and Receipt Voucher and Inventory Control Card (p44).
  - Empty bottles × 4 compared with DIGIT HCM (p45).
  - Separate cartons; escalation to the LGA logistician and NTD coordinator; return to the LGA store within 3 days (p45).
  - Key takeaways (p46).
- **Child Record Card:**
  - Full transcription of the card, including the **height-based dosing table** (HFW p34).
  - A second card version (p49).
  - Field-by-field instructions (p50-54), including the Kebbi State SMC/SPAQ section (p53-54).
- **Cohort tracking (HFW p55-60):** expanded with reasons, roles and a responsibility-flow diagram (p60).
- **M2:**
  - Why only 1–59 months are eligible (p11).
  - "A child who is 59 months in round one should receive AZM but will not be eligible in the next round" (p11).
  - Older-than-59-months signs, including "stand on one leg for 10 secs" (p11).
  - Allergy questions for the caregiver (p13).
  - Look-and-feel SAM signs and the pitting-oedema test, "about 3 seconds" (p15).
- **M3:**
  - Reasons to refer (p23).
  - Full referral-form transcription, including the health-facility part (p26).
  - Key takeaways (p27).
- **M4:**
  - "Limit AZM administration to 5 eligible children at a time" and "Ask the caregiver to bring drinking water in a small cup" (p31).
  - Mixing steps, including "shake well for at least 30 secs" (p33).
  - "CDD must ensure that dosing poles are returned to the health facility daily" (p32).
- **M1:** delivery platforms (NTDs, polio, SMC, MNCH) (p8).
- **M9:** examples of safeguarding, protection measures and the reporting chain (p86-87).

## Changed content (conflicts: the HFW PDF is used)

| Topic | Earlier wording | HFW wording (used) | Ref |
|---|---|---|---|
| Who supervises CDDs | CSV intro: "supervised by health workers, LGA, State and National teams" | "under the supervision of the CDD supervisors, LGA, State and National teams" | HFW p7 |
| What DIGIT HCM does | CSV intro: "Administration and reconciliation are done through the DIGIT HCM app installed on the CDD's own Android phone" | "The AZM administration data is collected using the Technology app (DIGIT HCM) installed in the devices of the CDDs" | HFW p7 |
| Health card | CSV M2: "health card (green card)" | "Ask to see the child's child health card" (no colour) | HFW p11 |
| ANC in the MUAC pilot | CSV M2 and CDD p18: CDDs also confirm ANC questions for pregnant women | MUAC only; ANC removed | HFW p17 |
| MUAC actions | CSV M2: MAM "Refer to health facility for counselling"; SAM "Refer to health facility immediately" | MAM "Immediate referral to health facility for counselling"; SAM "Immediate referral to health facility"; adds a Status column (Well-nourished, At Risk / MAM, SAM) | HFW p18 |
| Danger signs | CSV M3: "vomiting everything", "unable to drink or feed" | "Vomiting.", "Not able to eat or drink."; adds "Severe Acute Malnutrition" | HFW p23 |
| Allergy signs | CSV M3: "nausea or severe vomiting for more than 2 hours", "severe weakness", "unusual behaviour" | "Nausea or continuous vomiting", "Weakness or fatigue", "Body itching", "Abdominal pains, Diarrhoea"; no "unusual behaviour" | HFW p24 |
| Referral steps | CSV M3 and CDD p24 include "Confirm the caregiver understands by asking them to repeat the instructions" | Step not listed | HFW p25 |
| Referral forms per team | CDD p25: "a booklet of 20 Referral Forms which are double carbon copy" | "Each CDD team will have a referral forms which are double carbon copy" (no number) | HFW p26 |
| Referral role play | CDD p25: two scenarios (2 years with high fever for 2 days; 6 months and not breastfeeding) | One scenario (2 years with high fever for 2 days) | HFW p26 |
| CDD phone number | CSV M3: "CDDs should leave their phone numbers on the child record card" | Moved to the Child Record Card steps ("Passive ADR monitoring") | HFW p54 |
| Daily target | CDD p32: "a minimum of 100 children working for 4 days in the round" | "a total of 100 children each day during the 4 days distribution period" | HFW p32 |
| Partly used bottle | CSV M4 and CDD p32: "viable for up to 2 days" | "viable for up to 2 to 3 days" | HFW p32 |
| Reconciliation | CSV M4: "reconciled in DIGIT HCM at day's end"; CDD p32: "All reconciliation ... done through the DIGIT HCM platform" | OIC documents in the Inventory Control Card; empty bottles × 4 checked against DIGIT HCM; cartons; LGA store within 3 days | HFW p32, p44-45 |
| Dosing tool | CDD p33: "Give medicine slowly with an Infant Feeding Syringe or dispensing Cup" | "Give medicine slowly with the dispensing cup" (syringe removed) | HFW p33 |
| House-mark parts | CSV M4 and CDD p37 list "House number" and status "Completed after re-visit (R/C)"; round "1 or 2" | No "House number" in the list (examples still show `021`); no R/C status in the list (an R/C example is kept); round "1 or 2 or 3 or 4 or 5 or 6" | HFW p36 |
| House-mark examples | CSV M4 and CDD p37: round 1, e.g. `AZM/26/1/56708/021/3/3/C` | Round 3, e.g. `AZM/26/3/56708/021/3/3/C`; adds `AZM/26/3/56708/021/3/3/R/C` | HFW p36 |
| Card life | CDD p35: "used for 4 rounds (Two Years)" | "expected to last for 2 years" (the card grid still shows 4 rounds over 2 years) | HFW p34, p53 |
| Safeguarding email | CSV M9 and CDD p64: concerns@malariaconsortium.org | **concenrns@malariaconsortium.org**, kept as printed and flagged (see open question C1) | HFW p87 |
| Spoon/cup image in M9 | CSV M9 captions: "Avoid — using an improvised spoon instead of the provided dispensing cup" / "Correct — the proper cup" | The HFW picture marks **forcing** medicine into a lying child's mouth with an X, and drinking from a cup with a tick. The new caption follows the picture: do not force | HFW p84 |
| Module titles | CDD: M5 IPC, M6 Safeguarding | M6 IPC, M9 Safeguarding; new M5, M7 and M8 | HFW p2 |

## Removed content (in earlier materials, not in the HFW PDF)

| Removed | Was in | Note |
|---|---|---|
| "Summary of Module 1" (4 points) | CDD p8 | No M1 summary in HFW. |
| Picture table "Do NOT give Azithromycin to the following children" | CDD p15 | HFW p13 is text only. |
| ANC assessment for pregnant women | CDD p18, CSV M2 | |
| "Data Quality Assurance and Feasibility Measures" (Kobo constraints, dashboards, spot checks) | CDD p19 | |
| Allergy "Step 4: ASK" block | CDD p23 | |
| Dosing-pole photos ("A CDD measuring the height of a child ... with a dosing pole") | CDD p31 | HFW has no dosing-pole picture. |
| Positioning photo ("AZM is giving slowly and the child properly positioned") | CDD p34, CSV M4 image | HFW p33 has no picture. The do/don't collage appears only as the M9 cover (HFW p84). |
| Photo of a woman reading a card | CDD p47 | |
| Photo "Ensure that children who received AZM in the previous round also receive in the next round" | CDD p54, CSV M4 caption | |
| CSV M4 image captions for the house-marking, record-card and cohort photos | CSV M4 | Only the house-marking photo still exists (HFW p35), with a new caption. |
| JOB_AID section "Job aid tools" | CSV intro | Now a LIST "Tools for each participant" (HFW p6). |
