"""Image metadata for the HFW flipbook: baked text, rights flags, furniture, exclusions, Hausa handling."""

# Pages that show at least one content figure (from the page-by-page read). p22 is the M3
# cover photo repeated (excluded as a duplicate); p64's second figure is the Med Safety logo.
FIGURE_PAGES = [1, 5, 9, 12, 14, 16, 18, 19, 20, 21, 23, 24, 25, 26, 28, 30, 34, 35, 39, 41, 43, 49,
                55, 60, 61, 64, 66, 73, 77, 81, 84, 88]

GS = "Visible AI image-generator sparkle watermark (bottom-right corner)"
BAKED = {
    "m1_p01_01": "AZM (bottle label)",
    "m1_p05_01": "AZM (on vests)",
    "m2_p09_01": "AZM (on the pack, small)",
    "m2_p12_01": "Children 1 to 11 months; Child 1 to 2 months; cannot hold head and neck steady when upright; NOT newborn or less than one month; Child 3 to 4 months; Can hold head and neck steady when upright; Child 5 to 11 months; Can crawl; Can sit without help",
    "m2_p12_02": "Child 12 to 59 months; can stand or walk; CANNOT raise arm and touch opposite ear; CANNOT stand or jump on one foot",
    "m2_p14_02": "Difficulty in swallowing; Severe acute malnutrition; Not eating; Very Sick",
    "m2_p16_01": "Between 1 to 59 months; ELIGIBLE; REFER; When the child is sick; When the child has fever; When the child has allergy to antibiotics or similar medicines or has mild/severe/acute malnutrition; When the child has taken AZM or other similar antibiotics in the last 28 days (4 weeks)",
    "m2_p18_01": "MUAC Range; Status; Classification; Action Required; ≥ 12.5 cm; Well-nourished; Normal; No immediate action; 11.5 - 12.4 cm; At Risk / MAM; Moderate Acute Malnutrition; Immediate referral to health facility for counselling; < 11.5 cm; SAM; Severe Acute Malnutrition; Immediate referral to health facility",
    "m2_p19_01": "MUAC Assessment: Right and Wrong; Good MUAC assessment; Bad MUAC assessment; Left arm; Right arm; Not too tight; Too tight; AZM",
    "m2_p20_02": "cm; scale 6-26; unicef; dimension labels in mm (not readable)",
    "m3_p21_01": "AZM (on vests)",
    "m3_p23_01": "When the child is sick; When the child has danger signs",
    "m3_p23_02": "When the child has fever",
    "m3_p24_01": "Very Sick; Fever; Swelling; Rash",
    "m3_p24_02": "Difficulty in swallowing; Severe acute malnutrition; Not eating; Very Sick; Fever",
    "m3_p25_01": "Do Not give AZM; Fill referral form; Explain referral to caregiver",
    "m3_p26_01": "AZM Referral Form: every field (see the transcription lists in M3)",
    "m4_p30_01": "1-5; Expiry Date; Check expiry date of the medicine; Wash hand; Provide clean water from the household; Reconstitute AZM medicine; Measure out AZM for dispensing",
    "m4_p34_01": "Child Record Card: every field, both dosing tables and the safety message (see the transcription in M4)",
    "m4_p35_01": "AZM/25/1 (a 6 written over the 5); 0041/021/2/2/c",
    "m4_p39_01": "Banner: TRAINING OF HEALTH WORKERS ON SUBMISSION OF CALL-DATA DURING AZITHROMYCIN MDA - GOMBE STATE, NIGERIA; flipchart: CALL-DATA SUBMISSION PROCEDURES (rest garbled/illegible)",
    "m4_p49_01": "Child Record Card, second version: front-page fields (see the transcription in M4); stray [Picture] label",
    "m4_p55_01": "COHORT",
    "m4_p60_01": "malaria consortium; Cohort Tracking Responsibility Flow; Community Drug Distributors; CDDs Supervisors, Health Facility Supervisors, Nat'l, State & LGA Team; State & Country M&E Team; Government & Partners; Administer Treatment; Collect Data; Monitor & Verify Data; Analyze & Compare Cohorts; Policy Decisions; Program Adjustments; Data Collection; Data Reporting; Analysis & Reports; Policy Action; Field Work; Supervision; Data Analysis",
    "m5_p64_01": "NAFDAC ADR eReporting Form; confidentiality notice; I accept the terms & conditions; I'm reporting for myself or a relative; I'm reporting as a health professional; browser tabs and bookmarks (illegible)",
    "m8_p81_01": "GLOBAL (company logo on the truck)",
    "m9_p88_03": "1000 (banknotes); photo credit DAN KITWOOD/GETTY IMAGES",
}

RIGHTS = {
    "m1_p01_01": "Product render of a bottle: confirm source/licence",
    "m1_p05_01": GS + "; identifiable adults and children: confirm source, licence and consent",
    "m2_p09_01": GS + "; identifiable adults and children; heavy compression artefacts in the original: confirm source and consent",
    "m2_p19_01": "Illustration looks AI-generated: confirm source and licence",
    "m2_p20_01": "Looks like a third-party/agency photo of an identifiable child: confirm source, licence and consent",
    "m2_p20_02": "UNICEF mark on the tape drawing: confirm permission to reproduce",
    "m3_p21_01": GS + "; identifiable adults and a child: confirm source and consent",
    "m3_p25_01": "Contains a small photo (suspension poured into a cup): confirm source",
    "m4_p28_01": "Real photo of an identifiable woman and child: confirm consent (same photo reused on p84)",
    "m4_p30_01": "Contains small photos (jug, CDD with family, pouring suspension): confirm source",
    "m4_p35_01": "Photo digitally edited (a 6 pasted over the 5); identifiable woman; code differs from the p36 format: confirm source and consent",
    "m4_p39_01": GS + "; identifiable health workers; garbled signage suggests AI generation: confirm source and consent",
    "m4_p41_01": GS + "; identifiable health worker: confirm source and consent",
    "m4_p43_01": "Real photo, faces mostly not visible: confirm consent",
    "m4_p55_01": "Stock icon style: confirm licence",
    "m4_p60_01": "AI-style infographic carrying the Malaria Consortium logo: confirm source and approval",
    "m5_p61_01": "Illustration looks AI-generated: confirm source and licence",
    "m5_p64_01": "Screenshot shows a personal browser bookmarks bar and inbox count: recapture a clean screenshot",
    "m5_p66_01": "Identifiable child in distress; AI-generated look: confirm source and consent",
    "m6_p73_01": GS + "; identifiable adults and children: confirm source and consent",
    "m7_p77_01": "Real photos of identifiable people: confirm consent",
    "m8_p81_01": GS + " on a real-looking photo (AI-edited); third-party company mark GLOBAL on the truck; identifiable worker: confirm source and consent",
    "m9_p84_01": "Real photos of identifiable children, including a distressed infant: confirm consent",
    "m9_p88_01": "Stock photo: confirm licence",
    "m9_p88_02": "Stock photo: confirm licence",
    "m9_p88_03": "Visible Getty Images credit (Dan Kitwood/Getty Images): licence required, or replace",
}

REDRAW = "Redraw recommended: the labels carry the teaching point; until then the Hausa caption and the translated list under the image carry it"
CAPTION = "Hausa caption is enough: translate the caption (and the list below the image) in Step 7"
NONE_CODE = "No Hausa handling: the text is a code, brand or number"
NONE_BG = "No Hausa handling: background text, not part of the lesson"
FORM = "Keep the English image (the field form is printed in English); Hausa learners use the translated transcription below it"
HAUSA = [
    ("m1_p01_01.png", "none", NONE_CODE), ("m1_p05_01.jpg", "none", NONE_CODE), ("m2_p09_01.jpg", "none", NONE_CODE),
    ("m2_p12_01.png", "redraw", REDRAW), ("m2_p12_02.png", "redraw", REDRAW), ("m2_p14_02.png", "redraw", REDRAW),
    ("m2_p16_01.png", "redraw", REDRAW + " (the full text is also in the transcribed table)"),
    ("m2_p18_01.png", "caption", CAPTION + "; the transcribed MUAC table carries every cell"),
    ("m2_p19_01.jpg", "redraw", REDRAW), ("m2_p20_02.png", "none", NONE_CODE),
    ("m3_p21_01.jpg", "none", NONE_CODE), ("m3_p23_01.png", "caption", CAPTION), ("m3_p23_02.png", "caption", CAPTION),
    ("m3_p24_01.png", "redraw", REDRAW), ("m3_p24_02.png", "redraw", REDRAW), ("m3_p25_01.png", "caption", CAPTION),
    ("m3_p26_01.png", "form", FORM), ("m4_p30_01.png", "redraw", REDRAW), ("m4_p34_01.png", "form", FORM),
    ("m4_p35_01.jpg", "none", NONE_CODE + " (house-mark code)"), ("m4_p39_01.jpg", "none", NONE_BG),
    ("m4_p49_01.png", "form", FORM), ("m4_p55_01.jpg", "caption", CAPTION),
    ("m4_p60_01.jpg", "redraw", REDRAW + " (dense English diagram)"),
    ("m5_p64_01.png", "form", "Keep the English screenshot (the NAFDAC website is in English); the transcription is translated"),
    ("m8_p81_01.jpg", "none", NONE_BG), ("m9_p88_03.jpg", "none", NONE_CODE + "; the photo credit is a rights issue, not a translation issue"),
]

FURNITURE = [
    {"item": "Teal double side bar (left edge)", "pages": "2-4, 6-8, 10-16, 29-36, 61-64, 74-76, 78-80, 82-88", "reason": "Repeats on most pages; decoration", "hash": None},
    {"item": "Blue/light-blue side bar variant", "pages": "17-27, 55, 57-60", "reason": "Repeats; decoration", "hash": None},
    {"item": "Section-title side panel (raster)", "pages": "43, 47, 55, 60, 65, 70", "reason": "Repeats on section-title pages; decoration", "hash": "88589072d0"},
    {"item": "Teal header band with dot grid (raster)", "pages": "38-42, 44-46, 48-54, 56-59, 66-69, 71-72", "reason": "Repeats on 23 pages; header decoration", "hash": "16e186a26a"},
    {"item": "Blue gradient footer band (raster)", "pages": "38-42, 44-46, 48-54, 56-59, 66-69, 71-72", "reason": "Repeats on 25 pages; footer decoration", "hash": "91f17dfb26"},
    {"item": "Bullet arrow icon (raster)", "pages": "38, 48, 66 and others", "reason": "List bullet; decoration", "hash": "8be87087cb"},
    {"item": "Dotted patterns (side and header)", "pages": "37-72", "reason": "Decoration", "hash": None},
    {"item": "Page-number badge (teal circle)", "pages": "2-88", "reason": "Page furniture; also sits on top of the cover photos", "hash": None},
    {"item": "Title underline rules (grey/black)", "pages": "34, 36, 88", "reason": "Decoration", "hash": None},
    {"item": "Light grey lower-half background", "pages": "38-72", "reason": "Background", "hash": None},
]

EXCLUDED = [
    {"what": "p22 photo (embedded p22_e00)", "page": 22, "module": "M3", "embedded": "p22_e00.png",
     "reason": "duplicate of the M3 cover photo m3_p21_01 (same picture, smaller); not shipped twice"},
    {"what": "p61 blurred photo background (embedded p61_e00)", "page": 61, "module": "M5", "embedded": "p61_e00.png",
     "reason": "blurred decorative background behind the M5 cover panels"},
    {"what": "p73 blurred photo background (embedded p73_e00)", "page": 73, "module": "M6", "embedded": "p73_e00.png",
     "reason": "blurred decorative background behind the M6 cover photo"},
    {"what": "p84 MODULE 9 heading drawn as an image (embedded p84_e00)", "page": 84, "module": "M9", "embedded": "p84_e00.png",
     "reason": "page heading text rendered as a raster, not a figure (the heading is in the module title)"},
    {"what": "p66 empty blue box under the photo (vector)", "page": 66, "module": "M5",
     "reason": "blank rectangle with no content (looks like an unfilled caption box)"},
]

PAGE_NOTES = {
    2: "Contents page (printed 1). Not converted; page numbers on it are 1 too low from M4 onwards.",
    10: "M2 contents and tools (AZM Job Aid). Not converted.",
    22: "M3 contents and tools (AZM Job Aid, AZM Referral Form). Photo is a duplicate of the M3 cover (excluded).",
    29: "M4 contents and tools (AZM Job Aid, Sample AZM POS). Not converted.",
    38: "Call-in data contents and tools (AZM Job Aid). Not converted.",
    48: "Child Record Card steps: contents and tools (AZM Job Aid). Not converted.",
    56: "Cohort tracking contents and tools (AZM Job Aid). Not converted.",
    62: "M5 contents and tools (AZM Job Aid). Not converted.",
    74: "M6 contents and tools (AZM Job Aid). Not converted.",
    78: "M7 contents and tools (AZM Job Aid). Not converted.",
    82: "M8 contents and tools (AZM Job Aid). Not converted.",
    85: "M9 contents and tools (AZM Job Aid). Not converted.",
}
