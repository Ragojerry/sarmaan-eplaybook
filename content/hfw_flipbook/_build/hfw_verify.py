"""Second-pass verification of clinical values, time windows, cut-offs, codes and form fields.

Each CHECK row was compared by eye against a fresh, higher-resolution render of the
PDF page (2026-11-06, 160-600 dpi crops; the first pass used 1100 px previews).
This script then confirms the exact value string is present in the generated CSVs
and records where. Writes content/hfw_flipbook/verification_report.md.
usage: python -I content/hfw_flipbook/_build/hfw_verify.py
"""
import csv
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
sys.stdout.reconfigure(encoding="utf-8")

# (category, page, value as it must appear in the CSV, PDF wording seen on the second pass, result)
M, F = "match", "MISMATCH"
CHECK = [
    ("age range", 7, "1-59", "AZM drug administration is aimed protection children aged 1-59 months", M),
    ("frequency", 8, "every six months (bi-annually)", "AZM is administered every six-months (Bi-annually) to children 1 to 59 months", M),
    ("age range", 11, "between 1 to 59 months", "AZM is given to only healthy children between 1 to 59 months of age", M),
    ("age range", 11, "less than one month or older than 59 months", "Children who are less than one month or older than 59 months are not eligible", M),
    ("age rule", 11, "59 months in round one", "Children who are 59 months old in round one should receive AZM but will not be eligible in the next round", M),
    ("age signs", 11, "From 3 to 11 months", "How to know if an infant is between 3 to 11 months: hold head and neck, crawl, sit without help", M),
    ("age signs", 11, "10 secs", "Can stand on one leg for 10 secs", M),
    ("age signs", 12, "1 to 2 months: cannot hold head and neck steady", "Child 1 to 2 months - cannot hold head and neck steady when upright", M),
    ("age signs", 12, "3 to 4 months: can hold head and neck steady", "Child 3 to 4 months - Can hold head and neck steady when upright", M),
    ("age signs", 12, "5 to 11 months: can crawl and can sit without help", "Child 5 to 11 months - Can crawl / Can sit without help", M),
    ("age signs", 12, "CANNOT raise the arm over the head and touch the opposite ear", "CANNOT raise arm and touch opposite ear", M),
    ("allergy scope", 13, "macrolide antibiotics", "allergic to AZM or other macrolide antibiotics", M),
    ("time window", 15, "28 days (4 weeks)", "in the last 28 days or 4 weeks or one month", M),
    ("time window", 15, "about 3 seconds", "Press gently with your thumb on the top of both feet for about 3 seconds", M),
    ("age range", 15, "60 months and older", "Children from 60 months and older", M),
    ("time window", 15, "in the last one month", "Children who have received AZM or other antibiotics in the last one month", M),
    ("eligibility chart", 16, "mild/severe/acute malnutrition", "When the child has allergy ... or has mild/severe/acute malnutrition: X, refer tick", M),
    ("eligibility chart", 16, "last 28 days (4 weeks)", "taken AZM or other similar antibiotics in the last 28 days (4 weeks): X, no refer tick", M),
    ("MUAC age", 17, "6–59 months", "MAUC/Nutrition Assessment (Children 6–59 months)", M),
    ("MUAC protocol", 17, "Use the left arm", "Measurement protocol: Left arm. Correct midpoint.", M),
    ("MUAC cut-off", 18, "≥ 12.5 cm", "≥12.5 cm | Well-nourished | Normal | No immediate action", M),
    ("MUAC cut-off", 18, "11.5 - 12.4 cm", "11.5 - 12.4 cm | At Risk / MAM | Moderate Acute Malnutrition | Immediate referral to health facility for counselling", M),
    ("MUAC cut-off", 18, "< 11.5 cm", "<11.5 cm | SAM | Severe Acute Malnutrition | Immediate referral to health facility", M),
    ("MUAC action", 18, "Immediate referral to health facility for counselling", "Immediate referral to health facility for counselling", M),
    ("MUAC tape", 20, "red from 6 to 11 cm, yellow at 12 cm, green from 13 to 26 cm", "tape scale: red 6-11, yellow 12, green 13-26 (low-resolution source)", M),
    ("form field", 26, "Round 1, 2, 3, 4, 5 or 6", "AZM [ ] Round 1 ... [ ] Round 6 (TICK) - CDD part", M),
    ("form field", 26, "AZM Round: 1 or 2", "AZM Round: [ ]1 [ ]2 - health facility part", M),
    ("form field", 26, "1 11 month: [as printed] or 12- 59 months", "Age: [ ]1  11 month:  [ ]12- 59 months (no dash visible at 600 dpi)", M),
    ("form field", 26, "NAFDAC E-Reporting Link / Med Safety App was filled", "NAFDAC E-Reporting Link / Med Safety App was Filled YES/NO", M),
    ("reconstitution", 30, "15ml of clean water to obtain 30ml", "reconstituted with 15ml of clean water to obtain 30ml AZM suspension", M),
    ("bottle use", 30, "reach 4 children", "Each bottle of AZM will be used to reach 4 children", M),
    ("group size", 31, "5 eligible children at a time", "Limit AZM administration to 5 eligible children at a time", M),
    ("dose", 31, "1-2 months", "1-2 months will receive 2ml", M),
    ("dose", 31, "2ml", "1-2 months will receive 2ml", M),
    ("dose", 31, "3ml", "3-4 months will receive 3ml", M),
    ("dose", 31, "4ml", "5-11 months will receive 4ml", M),
    ("dosing method", 31, "measure height with the dosing pole", "For children 12-59 months: The dosing pole will be used to measure their height", M),
    ("time window", 31, "vomits within 5 minutes", "If the child vomits within 5 minutes after receiving AZM, ... redosed with the same dose", M),
    ("time window", 31, "30 minutes", "Observe the child for 30 minutes after administration", M),
    ("daily target", 32, "100 children each day, over the 4 days", "reach a total of 100 children each day during the 4 days distribution period", M),
    ("time window", 32, "2 to 3 days", "Partially used AZM medicines remain viable for up to 2 to 3 days", M),
    ("mixing", 33, "15ml of water to obtain 30ml final volume", "Measure and add 15ml of water to obtain 30ml final volume", M),
    ("mixing", 33, "at least 30 secs", "shake well for at least 30 secs", M),
    ("dose table (card)", 34, "1-2 Months", "1-2 Months | 2 ml", M),
    ("dose table (card)", 34, "3-4 Months", "3-4 Months | 3 ml", M),
    ("dose table (card)", 34, "5-11 Months", "5-11 Months | 4 ml", M),
    ("dose table (card)", 34, "50-53 cm", "50-53 cm | 2 ml", M),
    ("dose table (card)", 34, "54-64 cm", "54-64 cm | 4 ml", M),
    ("dose table (card)", 34, "65-75 cm", "65-75 cm | 6 ml", M),
    ("dose table (card)", 34, "76-86 cm", "76-86 cm | 8 ml", M),
    ("dose table (card)", 34, "87-97 cm", "87-97 cm | 10 ml", M),
    ("dose table (card)", 34, "98-109 cm", "98-109 cm | 12 ml", M),
    ("dose table (card)", 34, "110-121 cm", "110-121 cm | 14 ml", M),
    ("dose table (card)", 34, "122-129 cm", "122-129 cm | 16 ml", M),
    ("dose table (card)", 34, "130-136 cm", "130-136 cm | 19 ml", M),
    ("dose table (card)", 34, "137- 140 cm", "137- 140 cm | 25 ml", M),
    ("dose table (card)", 34, "19 ml", "130-136 cm | 19 ml", M),
    ("dose table (card)", 34, "25 ml", "137- 140 cm | 25 ml", M),
    ("photo code", 35, "AZM/25/1 with a 6 written over the 5, and 0041/021/2/2/c", "wall: AZM/25/1 (6 pasted over the 5) / 0041/021/2/2/c", M),
    ("code format", 36, "26 for 2026", "The year given (26 for 2026)", M),
    ("code format", 36, "1 or 2 or 3 or 4 or 5 or 6", "The round in numbers: 1 or 2 or 3 or 4 or 5 or 6", M),
    ("code format", 36, "CDD team code (4 digits)", "The CDD team code (4 digits)", M),
    ("code", 36, "AZM/26/3/56708/021/3/3/C", "AZM/26/3/56708/021/3/3/C.", M),
    ("code", 36, "AZM/26/3/56708/021/3/1/R", "AZM/26/3/56708/021/3/1/R.", M),
    ("code", 36, "AZM/26/3/56708/021/3/3/R/C", "AZM/26/3/56708/021/3/3/R/C.", M),
    ("code", 36, "AZM/26/3/56708/021/0/0/E", "AZM/26/3/56708/021/0/0/E.", M),
    ("age bands", 42, "1–11 months and 12–59 months", "two age categories: 1–11 months and 12–59 months", M),
    ("age bands", 42, "6–11 months and 12–59 months", "Integrated campaigns: 6 –11 months and 12–59 months", M),
    ("frequency", 42, "including mop-up", "Call-in data must be submitted daily throughout the implementation period including mop-up", M),
    ("reconstitution", 44, "exactly 15 ml of water", "reconstituted with exactly 15 ml of water", M),
    ("time window", 44, "vomiting within 5 minutes", "Any redosing due to vomiting within 5 minutes must be properly captured in the app", M),
    ("reconciliation", 45, "multiplies by 4", "count the number of empty bottles ... and multiply this by 4", M),
    ("time window", 45, "within 3 days after implementation", "returned to the LGA store within 3 days after implementation", M),
    ("ID format", 50, "12-digit alpha-numeric", "Write the 12-digit alpha-numeric ID generated from the DIGIT app", M),
    ("form field", 50, "Round: 1 or 2", "Round: Write round:1 or 2 in the year of implementation", M),
    ("form field", 50, "not more than 11 months", "Note: not more than 11 months", M),
    ("form field", 50, "date/month/year", "Write the date of birth as date/month/year", M),
    ("card life", 53, "2 years", "The Child Record Card is expected to last for 2 years", M),
    ("SMC cycles", 53, "1 to 4", "Cycles: indicate the cycle (1-4) / cycles 1 to 4 each", M),
    ("SMC age", 54, "3 to < 12 months or 12 to 59 months", "either age category: 3 to < 12 months or 12 to 59 months", M),
    ("code", 67, "Kaduna-KD, Kebbi-KB, Jigawa-JG, Adamawa-AD, and Gombe-GOM", "Kaduna-KD, Kebbi-KB, Jigawa-JG, Adamawa-AD, and Gombe-GOM and SARMAAN II", M),
    ("code", 67, "KB(SARMAAN II)", "Example- KB(SARMAAN II)", M),
    ("age range", 67, "between 1-59 months", "The child must be between 1-59 months", M),
    ("form field", 68, "e.g. 2ml", "Dosage: ... Eg. 2ml", M),
    ("form field", 68, "select one Day", "Duration: ... Select one Day", M),
    ("form field", 68, "select Oral", "How was the medium administered: Select Oral", M),
    ("link", 69, "https://vigiflow-eforms.who-umc.org/ng/adr", "Link: https://vigiflow-eforms.who-umc.org/ng/adr", M),
    ("email", 87, "concenrns@malariaconsortium.org", "All safeguarding issues should be reported to concenrns@malariaconsortium.org.", M),
]


def load():
    rows = []
    for f in sorted(glob.glob(os.path.join(OUT, "en", "*.csv"))) + [os.path.join(OUT, "alt_text.csv"), os.path.join(OUT, "quizzes.csv")]:
        for r in csv.reader(open(f, encoding="utf-8-sig")):
            rows.append((os.path.basename(f), r))
    return rows


def norm(t):
    return t.replace("–", "-").lower()


rows = load()
report, missing = [], []
for cat, page, value, pdf, result in CHECK:
    hits = []
    for fn, r in rows:
        if fn == "quizzes.csv":
            continue
        if any(norm(value) in norm(c) for c in r[1:]):
            hits.append(f"{fn} `{r[0]}`")
    if not hits:
        missing.append((page, value))
    report.append((cat, page, value, pdf, result if hits else "NOT FOUND IN CSV", hits[:2]))

lines = [
    "# Verification report: clinical values, time windows, cut-offs, codes and form fields",
    "",
    "**Method.** Most of the PDF text is drawn as shapes and cannot be extracted, so each value was "
    "checked by eye. This is the **second pass**: every page holding a dose, time window, MUAC cut-off, "
    "code format or form field was rendered again, at 160–600 dpi instead of the 1100 px previews of the first "
    "reading, and each value was compared with the generated CSV text. `_build/hfw_verify.py` then confirms "
    "that the exact string is present in the CSVs and records the key that holds it.",
    "",
    f"**Result.** {len(report)} values checked on {len({r[1] for r in report})} pages. "
    f"Mismatches between the PDF and the CSVs: **{sum(1 for r in report if r[4] == F)}**. "
    f"Values not found in the CSVs: **{len(missing)}**. No CSV value was changed in this pass.",
    "",
    "Values that match the PDF but are still **open clinical or wording questions** (see open_questions.md): "
    "the height-based dose steps (p34), \"4 children per bottle\" against the height doses (p30, p45), "
    "\"mild/severe/acute malnutrition\" (p16), the 3–11 vs 5–11 month crawl/sit band (p11 vs p12), the house-mark "
    "team code (\"4 digits\" vs 56708, p36), the referral-form rounds (1–6 vs 1–2, p26) and age box \"1 11 month:\", "
    "and the email spelling (p87).",
    "",
    "| # | Page | Category | Value in the CSV | PDF wording (second pass) | Result | Where in the CSVs |",
    "|---|---|---|---|---|---|---|",
]
for i, (cat, page, value, pdf, result, hits) in enumerate(report, 1):
    lines.append(f"| {i} | {page} | {cat} | {value} | {pdf} | {result} | {'<br>'.join(hits)} |")
lines += [
    "",
    "## Not verified beyond the first reading",
    "",
    "- **p49 second Child Record Card version:** the source is a 403 × 522 px raster. Re-rendering adds no detail, so its small print stays partly legible, and one line is hidden by a cut line. It holds no doses.",
    "- **p20 MUAC tape:** the millimetre dimension labels can't be read at the source resolution. The cm scale and colour bands were verified.",
    "- **p64 NAFDAC screenshot:** a 321 × 310 px raster. The form text was transcribed; the URL and tabs are unreadable.",
    "- **Quiz numbers:** quiz questions reuse the values above. The scenario numbers (11.8 cm, 25 bottles) and the wrong options were made up on purpose and are not in the PDF.",
]
with open(os.path.join(OUT, "verification_report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print(len(report), "checked; mismatches", sum(1 for r in report if r[4] == F), "; not found", missing)
