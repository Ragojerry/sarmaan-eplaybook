"""Builds content/cdd_flipbook/content_sections.json, docs/cdd-content-map.md and
docs/cdd-content-review.md from cdd_content_*.py and images_build.json.

Section ids are uuid5 of (module code, section number), so a rebuild gives the same ids.
Fails (exit 1) if a PDF page has no section, an image file is unused or used twice, or
a section points at an image that was not exported.

usage: python -I cdd_build.py      (run cdd_images.py first)
"""
import json
import os
import sys
import uuid
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cdd_content_a  # noqa: E402,F401  (each file registers its modules)
import cdd_content_b  # noqa: E402,F401
import cdd_content_c  # noqa: E402,F401
from cdd_dsl import CHANGES, MODULES, REVIEW  # noqa: E402

OUT = os.path.dirname(HERE)                       # content/cdd_flipbook
DOCS = os.path.join(OUT, "..", "..", "docs")
NS = uuid.UUID("6f1f3c52-7d0b-4c1e-9a55-cdd0f11b0001")
PAGES = 68
ROLES = ["CDD"]

# Pages whose only content is a module/section title; listed so the map explains them.
DECORATION = {
    1: "left sidebar, page-number bubble", 60: "blurred background photo behind the opener (decoration, not loaded)",
}
EXTRACTION_NOTES = {
    55: "tiny boxes at the top and bottom edges are slide-export artifacts, not content",
    56: "tiny boxes at the top and bottom edges are slide-export artifacts, not content",
    57: "tiny boxes at the top and bottom edges are slide-export artifacts, not content",
}

# Third-party, stock or sensitive pictures for the usage-rights check.
RIGHTS = [
    ("cdd_p68_no_bribery.jpg", 68, "News/stock photo of naira banknotes; the image carries the credit 'DAN KITWOOD/GETTY IMAGES' "
     "along its right edge. Licence needed or replace."),
    ("cdd_p68_no_photos_camera.jpg", 68, "Stock-style photo of a man with a camera. Source unknown."),
    ("cdd_p68_no_photos_phone.jpg", 68, "News-style photo of a phone held up over a cracked field. Source unknown."),
    ("cdd_p64_m6_do_dont.jpg", 64, "Photos of identifiable children, including a crying baby being held down and force-fed. "
     "Needs consent/rights confirmation and a judgement on whether the 'wrong' photo is acceptable."),
    ("cdd_p05_m1_opener.jpg", 5, "Shows identifiable children. Has a small four-point sparkle mark in the bottom-right corner, "
     "which is typical of AI-generated images; confirm the source."),
    ("cdd_p09_m2_opener.jpg", 9, "Shows identifiable children; sparkle mark as above (possibly AI-generated); the left half of the "
     "picture is visibly distorted."),
    ("cdd_p21_m3_opener.jpg", 21, "Shows an identifiable child; sparkle mark as above (possibly AI-generated)."),
    ("cdd_p22_referral_photo.jpg", 22, "Same picture as the Module 3 opener, cropped."),
    ("cdd_p60_m5_opener.jpg", 60, "Shows identifiable children; sparkle mark as above (possibly AI-generated)."),
    ("cdd_p19_muac_right_wrong.jpg", 19, "Illustration in a generated style; confirm the source."),
    ("cdd_p20_cdd_taking_muac.jpg", 20, "Photo of a child's arm being measured. Source unknown."),
    ("cdd_p28_m4_opener.jpg", 28, "Photo of an identifiable child and mother."),
    ("cdd_p32_dosing_pole_1.jpg", 32, "Photo with an identifiable child; a camera operator is visible."),
    ("cdd_p32_measuring_dose.jpg", 32, "Photo with identifiable children."),
    ("cdd_p35_giving_azm.jpg", 35, "Photo of an identifiable baby and children."),
    ("cdd_p37_house_marking.jpg", 37, "Possibly AI-generated (the text on the wall was edited: see the house-marking item)."),
    ("cdd_p54_cohort_icon.jpg", 54, "Icon in a stock style (looks like a stock vector). Source unknown."),
]


def build():
    images = {r["file"]: r for r in json.load(open(os.path.join(OUT, "images_build.json"), encoding="utf-8"))}
    errors, used = [], defaultdict(list)
    for m in MODULES:
        m["audience"], m["learner_roles"] = "ROLE_SPECIFIC", ROLES
        pdf_n = 0
        for n, s in enumerate(m["sections"], 1):
            # PDF sections keep the ids they had before the quiz statements were added (counted
            # without the statements); a statement has the fixed id the quiz build gave it.
            if s.get("fixed_id"):
                s["id"] = s.pop("fixed_id")
            else:
                pdf_n += 1
                s["id"] = str(uuid.uuid5(NS, f"{m['module_code']}/{pdf_n}"))
            s["section_number"] = n
            if s["content_type"] == "IMAGE":
                f = s["content"]["image_file"]
                used[f].append(f"{m['module_code']} #{n}")
                if f not in images:
                    errors.append(f"{m['module_code']} #{n}: image {f} was not exported")
                if not s["content"]["caption"].strip() or not s["content"]["alt"].strip():
                    errors.append(f"{m['module_code']} #{n}: image without caption or alt text")
    for f in images:
        if f not in used:
            errors.append(f"exported image not used: {f}")
        elif len(used[f]) > 1:
            errors.append(f"image used twice: {f} ({used[f]})")
    covered = {p for m in MODULES for s in m["sections"] for p in s["pdf_pages"]}
    missing = [p for p in range(1, PAGES + 1) if p not in covered]
    if missing:
        errors.append(f"PDF pages with no section: {missing}")
    return images, used, errors


def page_map(images):
    rows = defaultdict(lambda: {"modules": set(), "sections": [], "images": []})
    for m in MODULES:
        for s in m["sections"]:
            for p in s["pdf_pages"]:
                r = rows[p]
                r["modules"].add(m["module_code"])
                label = s["title"] or (s["content"].get("text") if s["content_type"] == "HEADING" else None) or ""
                r["sections"].append(f"#{s['section_number']} {s['content_type']}" + (f" ({label[:50]})" if label else ""))
                if s["content_type"] == "IMAGE":
                    r["images"].append(s["content"]["image_file"])
    out = ["# CDD flipbook: page to content map", "",
           "Source: `content/source/CDD-flipbook.pdf` (68 pages). 'Slide' is the number printed on the page (PDF page - 1).",
           "Built by `content/cdd_flipbook/_build/cdd_build.py`; do not edit by hand.", "",
           "| PDF page | Slide | Module | Sections | Image file(s) | Notes |", "|---|---|---|---|---|---|"]
    for p in range(1, PAGES + 1):
        r = rows[p]
        notes = "; ".join(x for x in (DECORATION.get(p), EXTRACTION_NOTES.get(p)) if x)
        out.append(f"| {p} | {p - 1 if p > 1 else 'cover'} | {', '.join(sorted(r['modules']))} | {'<br>'.join(r['sections'])} | "
                   f"{'<br>'.join(r['images']) or '-'} | {notes} |")
    out += ["", "## Images", "", "| File | PDF page | Pixels | Size | How it was made | SHA-256 |", "|---|---|---|---|---|---|"]
    for f, r in images.items():
        out.append(f"| {f} | {r['page']} | {r['px'][0]}x{r['px'][1]} | {r['bytes'] // 1024} KB | {r['source']} | `{r['sha256'][:16]}…` |")
    return out


def counts_section(images):
    with open(os.path.join(OUT, "pdf_image_census.json"), encoding="utf-8") as f:
        census = json.load(f)
    renders = sum(1 for r in images.values() if r["source"].startswith("slide area"))
    return ["", "## Images found in the PDF versus images loaded", "",
            f"- Raster objects embedded in the PDF: **{census['embedded_total']}** on {census['pages_with_images']} pages.",
            f"- Of these, **{census['content_pictures']}** are pictures (photos, drawings, logos, diagrams, forms). The other "
            f"{census['embedded_total'] - census['content_pictures']} are fragments: headings and labels saved as pictures "
            "(for example 'Contents', 'Section 2'), bullet arrows, tick and cross marks, small pieces of the composed slides "
            "(slide 17's table alone is 190 pieces), the blue sidebar and blurred backgrounds.",
            f"- Images loaded into the app: **{len(images)}**: {len(images) - renders} embedded pictures extracted as they are, "
            f"and {renders} composed slide areas rendered as one image each (the many pictures, labels and tick/cross marks of "
            "one slide stay together, so nothing is lost).",
            "- So the difference is: pictures that belong to one composed slide are loaded as one image, the cover's logos and "
            "bottle are inside the cover image, and decoration is left out. Every picture in the PDF appears in one of the loaded "
            "images (checked by eye against every page)."]


def review_doc():
    out = ["# CDD flipbook: content review", "",
           "For the programme's content experts. Source: `content/source/CDD-flipbook.pdf`. PDF page = slide + 1.",
           "Generated by `content/cdd_flipbook/_build/cdd_build.py` from the corrections and notes recorded in the content files.", "",
           "## 1. Every change made to the source text", "",
           "Only spelling and typing errors were fixed. Wording, numbers, doses, ages and thresholds are as in the PDF.", "",
           "| PDF page | Slide | In the PDF | In the app |", "|---|---|---|---|"]
    for p, a, b in CHANGES:
        out.append(f"| {p} | {p - 1} | {a} | {b} |")
    out += ["", "Not changed (grammar, kept as written): for example 'participants understands', 'Children with fever needs', "
            "'Government and IPs uses', 'a referral forms', 'This include'.", "",
            "## 2. Contradictions and questions for the reviewers (text kept as written)", ""]
    for n, (pages, topic, note) in enumerate(REVIEW, 1):
        pg = ", ".join(f"PDF {p} (slide {p - 1})" for p in pages)
        out.append(f"{n}. **{topic}** ({pg}). {note}")
    out += ["", "## 3. Pictures to check for usage rights and children's photos", "",
            "Loaded as they are. Please confirm the right to use each one, and that the photos of children are acceptable.", "",
            "| File | PDF page | Why it is listed |", "|---|---|---|"]
    for f, p, why in RIGHTS:
        out.append(f"| {f} | {p} | {why} |")
    out += ["", "## 4. Quiz questions", "",
            "None were created (programme decision, 2026-11-10). The CDD modules have no questions, so learners finish each one "
            "with 'Mark as complete'. When experts add questions in the quiz editor, the pre-test/post-test flow and the 90% rule "
            "apply to that module as they do to every other module.", ""]
    return out


def main():
    images, used, errors = build()
    if errors:
        print("\n".join(errors))
        return 1
    with open(os.path.join(OUT, "content_sections.json"), "w", encoding="utf-8") as f:
        json.dump(MODULES, f, ensure_ascii=False, indent=1)
    with open(os.path.join(DOCS, "cdd-content-map.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(page_map(images) + counts_section(images)) + "\n")
    with open(os.path.join(DOCS, "cdd-content-review.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(review_doc()) + "\n")
    n_sec = sum(len(m["sections"]) for m in MODULES)
    print(f"{len(MODULES)} modules, {n_sec} sections, {len(images)} images, {len(CHANGES)} text changes, {len(REVIEW)} review notes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
