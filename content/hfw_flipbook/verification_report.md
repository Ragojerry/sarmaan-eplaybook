# Verification report: clinical values, time windows, cut-offs, codes and form fields

**Method.** Most of the PDF text is drawn as shapes and cannot be extracted, so each value was checked by eye. This is the **second pass**: every page holding a dose, time window, MUAC cut-off, code format or form field was rendered again, at 160–600 dpi instead of the 1100 px previews of the first reading, and each value was compared with the generated CSV text. `_build/hfw_verify.py` then confirms that the exact string is present in the CSVs and records the key that holds it.

**Result.** 88 values checked on 28 pages. Mismatches between the PDF and the CSVs: **0**. Values not found in the CSVs: **0**. No CSV value was changed in this pass.

Values that match the PDF but are still **open clinical or wording questions** (see open_questions.md): the height-based dose steps (p34), "4 children per bottle" against the height doses (p30, p45), "mild/severe/acute malnutrition" (p16), the 3–11 vs 5–11 month crawl/sit band (p11 vs p12), the house-mark team code ("4 digits" vs 56708, p36), the referral-form rounds (1–6 vs 1–2, p26) and age box "1 11 month:", and the email spelling (p87).

| # | Page | Category | Value in the CSV | PDF wording (second pass) | Result | Where in the CSVs |
|---|---|---|---|---|---|---|
| 1 | 7 | age range | 1-59 | AZM drug administration is aimed protection children aged 1-59 months | match | module_hfw_01.csv `fb14d992-6626-5925-aadc-1839746f0414|text`<br>module_hfw_02.csv `dd4c30e8-a7ad-5e3e-8645-4e8d9a2db189|items.4` |
| 2 | 8 | frequency | every six months (bi-annually) | AZM is administered every six-months (Bi-annually) to children 1 to 59 months | match | module_hfw_01.csv `3bd12798-c0b9-5764-a145-ce33d01d1fdf|text` |
| 3 | 11 | age range | between 1 to 59 months | AZM is given to only healthy children between 1 to 59 months of age | match | module_hfw_02.csv `97723073-29ec-598a-aa14-f85b06b0dcbc|items.0`<br>module_hfw_02.csv `c64b0aa5-73c5-514a-b006-02d04d713ed3|rows.0.0` |
| 4 | 11 | age range | less than one month or older than 59 months | Children who are less than one month or older than 59 months are not eligible | match | module_hfw_02.csv `97723073-29ec-598a-aa14-f85b06b0dcbc|items.1` |
| 5 | 11 | age rule | 59 months in round one | Children who are 59 months old in round one should receive AZM but will not be eligible in the next round | match | module_hfw_02.csv `97723073-29ec-598a-aa14-f85b06b0dcbc|items.3` |
| 6 | 11 | age signs | From 3 to 11 months | How to know if an infant is between 3 to 11 months: hold head and neck, crawl, sit without help | match | module_hfw_02.csv `b9e2662e-cf62-580a-b6c6-c8254c11147b|text` |
| 7 | 11 | age signs | 10 secs | Can stand on one leg for 10 secs | match | module_hfw_02.csv `38e31df4-99d5-5cc0-bed4-3b3e329b8ec1|text` |
| 8 | 12 | age signs | 1 to 2 months: cannot hold head and neck steady | Child 1 to 2 months - cannot hold head and neck steady when upright | match | module_hfw_02.csv `df9383eb-2e68-5ec0-a7c8-ee06a2d2a67c|items.0` |
| 9 | 12 | age signs | 3 to 4 months: can hold head and neck steady | Child 3 to 4 months - Can hold head and neck steady when upright | match | module_hfw_02.csv `df9383eb-2e68-5ec0-a7c8-ee06a2d2a67c|items.2` |
| 10 | 12 | age signs | 5 to 11 months: can crawl and can sit without help | Child 5 to 11 months - Can crawl / Can sit without help | match | module_hfw_02.csv `df9383eb-2e68-5ec0-a7c8-ee06a2d2a67c|items.3` |
| 11 | 12 | age signs | CANNOT raise the arm over the head and touch the opposite ear | CANNOT raise arm and touch opposite ear | match | module_hfw_02.csv `c7de322c-545d-5b28-9a0f-381e74fbcfde|items.1` |
| 12 | 13 | allergy scope | macrolide antibiotics | allergic to AZM or other macrolide antibiotics | match | module_hfw_02.csv `c9a179cb-3370-5a7e-9af6-55c6b5f75a2d|text` |
| 13 | 15 | time window | 28 days (4 weeks) | in the last 28 days or 4 weeks or one month | match | module_hfw_02.csv `efbb4def-7288-50e1-b0f8-cf4b6518c7cc|text`<br>module_hfw_02.csv `c64b0aa5-73c5-514a-b006-02d04d713ed3|rows.4.0` |
| 14 | 15 | time window | about 3 seconds | Press gently with your thumb on the top of both feet for about 3 seconds | match | module_hfw_02.csv `9c755642-3363-5ab9-b9c8-acd3dc3f763e|items.0` |
| 15 | 15 | age range | 60 months and older | Children from 60 months and older | match | module_hfw_02.csv `8ec81bb5-df16-5ddb-b675-615cf46f269a|items.0` |
| 16 | 15 | time window | in the last one month | Children who have received AZM or other antibiotics in the last one month | match | module_hfw_02.csv `8ec81bb5-df16-5ddb-b675-615cf46f269a|items.3` |
| 17 | 16 | eligibility chart | mild/severe/acute malnutrition | When the child has allergy ... or has mild/severe/acute malnutrition: X, refer tick | match | module_hfw_02.csv `c64b0aa5-73c5-514a-b006-02d04d713ed3|rows.3.0` |
| 18 | 16 | eligibility chart | last 28 days (4 weeks) | taken AZM or other similar antibiotics in the last 28 days (4 weeks): X, no refer tick | match | module_hfw_02.csv `efbb4def-7288-50e1-b0f8-cf4b6518c7cc|text`<br>module_hfw_02.csv `c64b0aa5-73c5-514a-b006-02d04d713ed3|rows.4.0` |
| 19 | 17 | MUAC age | 6–59 months | MAUC/Nutrition Assessment (Children 6–59 months) | match | module_hfw_03.csv `MODULE|description`<br>module_hfw_03.csv `d64948e4-dd35-5333-8d19-1b3ff719df25|text` |
| 20 | 17 | MUAC protocol | Use the left arm | Measurement protocol: Left arm. Correct midpoint. | match | module_hfw_03.csv `6d7ff1b8-bc0e-560d-a0c3-875e91e3613d|items.1` |
| 21 | 18 | MUAC cut-off | ≥ 12.5 cm | ≥12.5 cm | Well-nourished | Normal | No immediate action | match | module_hfw_03.csv `9f848974-6e4b-5623-817d-1ae8fd2ad55e|rows.0.0` |
| 22 | 18 | MUAC cut-off | 11.5 - 12.4 cm | 11.5 - 12.4 cm | At Risk / MAM | Moderate Acute Malnutrition | Immediate referral to health facility for counselling | match | module_hfw_03.csv `9f848974-6e4b-5623-817d-1ae8fd2ad55e|rows.1.0` |
| 23 | 18 | MUAC cut-off | < 11.5 cm | <11.5 cm | SAM | Severe Acute Malnutrition | Immediate referral to health facility | match | module_hfw_03.csv `9f848974-6e4b-5623-817d-1ae8fd2ad55e|rows.2.0` |
| 24 | 18 | MUAC action | Immediate referral to health facility for counselling | Immediate referral to health facility for counselling | match | module_hfw_03.csv `9f848974-6e4b-5623-817d-1ae8fd2ad55e|rows.1.3` |
| 25 | 20 | MUAC tape | red from 6 to 11 cm, yellow at 12 cm, green from 13 to 26 cm | tape scale: red 6-11, yellow 12, green 13-26 (low-resolution source) | match | module_hfw_03.csv `82b8420b-2004-5f4e-8398-722bcca2d686|caption` |
| 26 | 26 | form field | Round 1, 2, 3, 4, 5 or 6 | AZM [ ] Round 1 ... [ ] Round 6 (TICK) - CDD part | match | module_hfw_05.csv `68baa400-bd2d-5859-b542-bafdf6d48bbf|items.4` |
| 27 | 26 | form field | AZM Round: 1 or 2 | AZM Round: [ ]1 [ ]2 - health facility part | match | module_hfw_05.csv `09d19889-d864-5e61-992d-0c8351d8f329|items.0` |
| 28 | 26 | form field | 1 11 month: [as printed] or 12- 59 months | Age: [ ]1  11 month:  [ ]12- 59 months (no dash visible at 600 dpi) | match | module_hfw_05.csv `68baa400-bd2d-5859-b542-bafdf6d48bbf|items.1` |
| 29 | 26 | form field | NAFDAC E-Reporting Link / Med Safety App was filled | NAFDAC E-Reporting Link / Med Safety App was Filled YES/NO | match | module_hfw_05.csv `5d1bbc29-af2e-5a36-a1e3-d55e18de0eca|items.2` |
| 30 | 30 | reconstitution | 15ml of clean water to obtain 30ml | reconstituted with 15ml of clean water to obtain 30ml AZM suspension | match | module_hfw_06.csv `806c4bd1-42de-5476-8291-f9c0694cb601|items.2` |
| 31 | 30 | bottle use | reach 4 children | Each bottle of AZM will be used to reach 4 children | match | module_hfw_06.csv `806c4bd1-42de-5476-8291-f9c0694cb601|items.3` |
| 32 | 31 | group size | 5 eligible children at a time | Limit AZM administration to 5 eligible children at a time | match | module_hfw_06.csv `80413b96-3527-551e-b8ed-59cca00e6300|items.2` |
| 33 | 31 | dose | 1-2 months | 1-2 months will receive 2ml | match | module_hfw_06.csv `96a1b923-09b8-5f73-a4b3-5ea6092739a9|rows.0.0`<br>module_hfw_07.csv `ef661940-d3ef-5251-adeb-7e385d23c930|rows.0.0` |
| 34 | 31 | dose | 2ml | 1-2 months will receive 2ml | match | module_hfw_06.csv `96a1b923-09b8-5f73-a4b3-5ea6092739a9|rows.0.1`<br>module_hfw_13.csv `5c40deab-3c7c-5d2a-9260-5f79fd11e3cf|items.2` |
| 35 | 31 | dose | 3ml | 3-4 months will receive 3ml | match | module_hfw_06.csv `96a1b923-09b8-5f73-a4b3-5ea6092739a9|rows.1.1` |
| 36 | 31 | dose | 4ml | 5-11 months will receive 4ml | match | module_hfw_06.csv `96a1b923-09b8-5f73-a4b3-5ea6092739a9|rows.2.1` |
| 37 | 31 | dosing method | measure height with the dosing pole | For children 12-59 months: The dosing pole will be used to measure their height | match | module_hfw_06.csv `a4a06319-26a5-53c6-ab89-d5eefa00efa2|items.0` |
| 38 | 31 | time window | vomits within 5 minutes | If the child vomits within 5 minutes after receiving AZM, ... redosed with the same dose | match | module_hfw_06.csv `e7a50a3b-71da-5cd3-adf8-ad60a67bd107|items.0` |
| 39 | 31 | time window | 30 minutes | Observe the child for 30 minutes after administration | match | module_hfw_06.csv `e7a50a3b-71da-5cd3-adf8-ad60a67bd107|items.1` |
| 40 | 32 | daily target | 100 children each day, over the 4 days | reach a total of 100 children each day during the 4 days distribution period | match | module_hfw_06.csv `2e31daca-99c0-5cd8-b70f-fd0b5122cbdc|items.2` |
| 41 | 32 | time window | 2 to 3 days | Partially used AZM medicines remain viable for up to 2 to 3 days | match | module_hfw_06.csv `1a11b55d-4f7c-5658-9e0e-1e0336c71a1e|items.2` |
| 42 | 33 | mixing | 15ml of water to obtain 30ml final volume | Measure and add 15ml of water to obtain 30ml final volume | match | module_hfw_06.csv `583780b6-f024-5b9d-9d33-8546ff693013|items.1` |
| 43 | 33 | mixing | at least 30 secs | shake well for at least 30 secs | match | module_hfw_06.csv `583780b6-f024-5b9d-9d33-8546ff693013|items.3` |
| 44 | 34 | dose table (card) | 1-2 Months | 1-2 Months | 2 ml | match | module_hfw_06.csv `96a1b923-09b8-5f73-a4b3-5ea6092739a9|rows.0.0`<br>module_hfw_07.csv `ef661940-d3ef-5251-adeb-7e385d23c930|rows.0.0` |
| 45 | 34 | dose table (card) | 3-4 Months | 3-4 Months | 3 ml | match | module_hfw_06.csv `96a1b923-09b8-5f73-a4b3-5ea6092739a9|rows.1.0`<br>module_hfw_07.csv `ef661940-d3ef-5251-adeb-7e385d23c930|rows.1.0` |
| 46 | 34 | dose table (card) | 5-11 Months | 5-11 Months | 4 ml | match | module_hfw_06.csv `96a1b923-09b8-5f73-a4b3-5ea6092739a9|rows.2.0`<br>module_hfw_07.csv `ef661940-d3ef-5251-adeb-7e385d23c930|rows.2.0` |
| 47 | 34 | dose table (card) | 50-53 cm | 50-53 cm | 2 ml | match | module_hfw_07.csv `0ce1cf72-a25e-5b9c-a28c-2ce667174765|rows.0.0` |
| 48 | 34 | dose table (card) | 54-64 cm | 54-64 cm | 4 ml | match | module_hfw_07.csv `0ce1cf72-a25e-5b9c-a28c-2ce667174765|rows.1.0` |
| 49 | 34 | dose table (card) | 65-75 cm | 65-75 cm | 6 ml | match | module_hfw_07.csv `0ce1cf72-a25e-5b9c-a28c-2ce667174765|rows.2.0` |
| 50 | 34 | dose table (card) | 76-86 cm | 76-86 cm | 8 ml | match | module_hfw_07.csv `0ce1cf72-a25e-5b9c-a28c-2ce667174765|rows.3.0` |
| 51 | 34 | dose table (card) | 87-97 cm | 87-97 cm | 10 ml | match | module_hfw_07.csv `0ce1cf72-a25e-5b9c-a28c-2ce667174765|rows.4.0` |
| 52 | 34 | dose table (card) | 98-109 cm | 98-109 cm | 12 ml | match | module_hfw_07.csv `0ce1cf72-a25e-5b9c-a28c-2ce667174765|rows.5.0` |
| 53 | 34 | dose table (card) | 110-121 cm | 110-121 cm | 14 ml | match | module_hfw_07.csv `0ce1cf72-a25e-5b9c-a28c-2ce667174765|rows.6.0` |
| 54 | 34 | dose table (card) | 122-129 cm | 122-129 cm | 16 ml | match | module_hfw_07.csv `0ce1cf72-a25e-5b9c-a28c-2ce667174765|rows.7.0` |
| 55 | 34 | dose table (card) | 130-136 cm | 130-136 cm | 19 ml | match | module_hfw_07.csv `0ce1cf72-a25e-5b9c-a28c-2ce667174765|rows.8.0` |
| 56 | 34 | dose table (card) | 137- 140 cm | 137- 140 cm | 25 ml | match | module_hfw_07.csv `0ce1cf72-a25e-5b9c-a28c-2ce667174765|rows.9.0` |
| 57 | 34 | dose table (card) | 19 ml | 130-136 cm | 19 ml | match | module_hfw_07.csv `0ce1cf72-a25e-5b9c-a28c-2ce667174765|rows.8.1` |
| 58 | 34 | dose table (card) | 25 ml | 137- 140 cm | 25 ml | match | module_hfw_07.csv `0ce1cf72-a25e-5b9c-a28c-2ce667174765|rows.9.1` |
| 59 | 35 | photo code | AZM/25/1 with a 6 written over the 5, and 0041/021/2/2/c | wall: AZM/25/1 (6 pasted over the 5) / 0041/021/2/2/c | match | alt_text.csv `73069cc3-dd15-5179-a74b-a49a5b0b2027|alt` |
| 60 | 36 | code format | 26 for 2026 | The year given (26 for 2026) | match | module_hfw_08.csv `bd15a8f4-d41c-5b0a-a75c-50148ea5769e|items.1` |
| 61 | 36 | code format | 1 or 2 or 3 or 4 or 5 or 6 | The round in numbers: 1 or 2 or 3 or 4 or 5 or 6 | match | module_hfw_08.csv `bd15a8f4-d41c-5b0a-a75c-50148ea5769e|items.2` |
| 62 | 36 | code format | CDD team code (4 digits) | The CDD team code (4 digits) | match | module_hfw_08.csv `bd15a8f4-d41c-5b0a-a75c-50148ea5769e|items.3` |
| 63 | 36 | code | AZM/26/3/56708/021/3/3/C | AZM/26/3/56708/021/3/3/C. | match | module_hfw_08.csv `e78f9dd6-89b2-53cc-b7ac-dbc79f027746|rows.0.1` |
| 64 | 36 | code | AZM/26/3/56708/021/3/1/R | AZM/26/3/56708/021/3/1/R. | match | module_hfw_08.csv `e78f9dd6-89b2-53cc-b7ac-dbc79f027746|rows.1.1` |
| 65 | 36 | code | AZM/26/3/56708/021/3/3/R/C | AZM/26/3/56708/021/3/3/R/C. | match | module_hfw_08.csv `e78f9dd6-89b2-53cc-b7ac-dbc79f027746|rows.2.1` |
| 66 | 36 | code | AZM/26/3/56708/021/0/0/E | AZM/26/3/56708/021/0/0/E. | match | module_hfw_08.csv `e78f9dd6-89b2-53cc-b7ac-dbc79f027746|rows.3.1` |
| 67 | 42 | age bands | 1–11 months and 12–59 months | two age categories: 1–11 months and 12–59 months | match | module_hfw_09.csv `9e865f42-a4ca-5347-a468-34bf3d7d2d4d|items.0` |
| 68 | 42 | age bands | 6–11 months and 12–59 months | Integrated campaigns: 6 –11 months and 12–59 months | match | module_hfw_09.csv `b961c927-a09b-556b-8314-0e698dceedf9|items.0` |
| 69 | 42 | frequency | including mop-up | Call-in data must be submitted daily throughout the implementation period including mop-up | match | module_hfw_09.csv `9e865f42-a4ca-5347-a468-34bf3d7d2d4d|items.4` |
| 70 | 44 | reconstitution | exactly 15 ml of water | reconstituted with exactly 15 ml of water | match | module_hfw_10.csv `ec696382-4a26-56e5-8151-cc71481e3006|items.1` |
| 71 | 44 | time window | vomiting within 5 minutes | Any redosing due to vomiting within 5 minutes must be properly captured in the app | match | module_hfw_10.csv `ec696382-4a26-56e5-8151-cc71481e3006|items.3` |
| 72 | 45 | reconciliation | multiplies by 4 | count the number of empty bottles ... and multiply this by 4 | match | module_hfw_10.csv `5da2451e-2014-5369-8f72-cf447d027ff3|items.1` |
| 73 | 45 | time window | within 3 days after implementation | returned to the LGA store within 3 days after implementation | match | module_hfw_10.csv `1fef85a3-8aea-5c5d-959b-83e03cf9f917|items.2` |
| 74 | 50 | ID format | 12-digit alpha-numeric | Write the 12-digit alpha-numeric ID generated from the DIGIT app | match | module_hfw_07.csv `e9d0e816-f23f-5ef9-a24b-388102369aca|items.1` |
| 75 | 50 | form field | Round: 1 or 2 | Round: Write round:1 or 2 in the year of implementation | match | module_hfw_05.csv `09d19889-d864-5e61-992d-0c8351d8f329|items.0`<br>module_hfw_07.csv `c3899f49-1aee-5636-9d75-35c1d20883a5|items.2` |
| 76 | 50 | form field | not more than 11 months | Note: not more than 11 months | match | module_hfw_07.csv `c3899f49-1aee-5636-9d75-35c1d20883a5|items.3` |
| 77 | 50 | form field | date/month/year | Write the date of birth as date/month/year | match | module_hfw_07.csv `e9d0e816-f23f-5ef9-a24b-388102369aca|items.2` |
| 78 | 53 | card life | 2 years | The Child Record Card is expected to last for 2 years | match | module_hfw_05.csv `f11ce263-0d18-5c73-a57c-5fe338c83def|items.2`<br>module_hfw_07.csv `c5d6ed03-2afa-5a55-a48e-28b1ea93687f|text` |
| 79 | 53 | SMC cycles | 1 to 4 | Cycles: indicate the cycle (1-4) / cycles 1 to 4 each | match | module_hfw_07.csv `b6e4ee99-3cd3-5ef8-89d6-7f4d98ef79a0|items.3` |
| 80 | 54 | SMC age | 3 to < 12 months or 12 to 59 months | either age category: 3 to < 12 months or 12 to 59 months | match | module_hfw_07.csv `b6e4ee99-3cd3-5ef8-89d6-7f4d98ef79a0|items.4` |
| 81 | 67 | code | Kaduna-KD, Kebbi-KB, Jigawa-JG, Adamawa-AD, and Gombe-GOM | Kaduna-KD, Kebbi-KB, Jigawa-JG, Adamawa-AD, and Gombe-GOM and SARMAAN II | match | module_hfw_13.csv `802981f5-7be1-5e76-9e0e-b3f196fe2c96|items.1` |
| 82 | 67 | code | KB(SARMAAN II) | Example- KB(SARMAAN II) | match | module_hfw_13.csv `802981f5-7be1-5e76-9e0e-b3f196fe2c96|items.1` |
| 83 | 67 | age range | between 1-59 months | The child must be between 1-59 months | match | module_hfw_13.csv `3aac668c-8aa2-56e9-bbff-213aaff98fcc|items.1` |
| 84 | 68 | form field | e.g. 2ml | Dosage: ... Eg. 2ml | match | module_hfw_13.csv `5c40deab-3c7c-5d2a-9260-5f79fd11e3cf|items.2` |
| 85 | 68 | form field | select one Day | Duration: ... Select one Day | match | module_hfw_13.csv `5c40deab-3c7c-5d2a-9260-5f79fd11e3cf|items.4` |
| 86 | 68 | form field | select Oral | How was the medium administered: Select Oral | match | module_hfw_13.csv `5c40deab-3c7c-5d2a-9260-5f79fd11e3cf|items.2` |
| 87 | 69 | link | https://vigiflow-eforms.who-umc.org/ng/adr | Link: https://vigiflow-eforms.who-umc.org/ng/adr | match | module_hfw_13.csv `ff151582-459d-5f0d-a662-43de3d83bc46|text` |
| 88 | 87 | email | concenrns@malariaconsortium.org | All safeguarding issues should be reported to concenrns@malariaconsortium.org. | match | module_hfw_17.csv `1fe20de4-2085-57ea-b860-4467d9e7bd4b|text` |

## Not verified beyond the first reading

- **p49 second Child Record Card version:** the source is a 403 × 522 px raster. Re-rendering adds no detail, so its small print stays partly legible, and one line is hidden by a cut line. It holds no doses.
- **p20 MUAC tape:** the millimetre dimension labels can't be read at the source resolution. The cm scale and colour bands were verified.
- **p64 NAFDAC screenshot:** a 321 × 310 px raster. The form text was transcribed; the URL and tabs are unreadable.
- **Quiz numbers:** quiz questions reuse the values above. The scenario numbers (11.8 cm, 25 bottles) and the wrong options were made up on purpose and are not in the PDF.
