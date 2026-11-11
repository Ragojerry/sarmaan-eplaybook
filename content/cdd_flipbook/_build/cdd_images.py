"""Export every content image of the CDD flipbook into content/cdd_flipbook/images and
write images_build.json (file, page, how it was made, size, SHA-256).

Two kinds of source, never resized:
  - "e:<name>"  the embedded raster, extracted byte-for-byte in its own format
                (JPEG stays the original JPEG) at its full resolution;
  - "render"    a composed slide area (several pictures with labels and tick/cross marks
                drawn on top) rendered as one image, so nothing is lost.
Boxes are in PDF points, top-left origin (pages are 842 x 595 pt).

A render can hide page objects that are not part of the figure: the body text that runs
under the picture column ("text"), or template decoration such as the page-number
bubble (a box: every object inside it). Labels inside these figures are rasters, so
hiding text never removes a label. Photographic renders are saved as JPEG quality 92
at full render resolution; diagrams, tables and forms as lossless PNG.

usage: python -I cdd_images.py <pdf> <out dir (content/cdd_flipbook)>
"""
import hashlib
import io
import json
import os
import sys

import pypdfium2 as pdfium
import pypdfium2.raw as raw
from PIL import Image

# stem, pdf page, source, box (pt) for renders, render dpi
FIGURES = [
    ("cdd_p01_cover", 1, "render", (103, 0, 842, 595), 200),
    ("cdd_p05_m1_opener", 5, "e:0", None, None),
    ("cdd_p09_m2_opener", 9, "e:0", None, None),
    ("cdd_p12_age_signs", 12, "render", (82, 124, 784, 518), 250),
    ("cdd_p14_eligible_not_eligible", 14, "render", (110, 168, 734, 486), 250),
    ("cdd_p16_eligibility_summary", 16, "render", (96, 150, 776, 512), 250),
    ("cdd_p18_muac_table", 18, "render", (88, 132, 753, 462), 250),
    ("cdd_p19_muac_right_wrong", 19, "e:0", None, None),
    ("cdd_p20_cdd_taking_muac", 20, "e:0", None, None),
    ("cdd_p20_muac_tape", 20, "e:1", None, None),
    ("cdd_p21_m3_opener", 21, "e:0", None, None),
    ("cdd_p22_referral_photo", 22, "e:20", None, None),
    ("cdd_p23_sick_danger_fever", 23, "render", (600, 155, 828, 490), 250),
    ("cdd_p24_allergy_exclusion_signs", 24, "render", (446, 212, 828, 392), 300),
    ("cdd_p25_referral_steps", 25, "render", (155, 378, 758, 508), 250),
    ("cdd_p26_referral_form", 26, "render", (88, 152, 296, 506), 450),
    ("cdd_p28_m4_opener", 28, "e:0", None, None),
    ("cdd_p30_reconstitution_steps", 30, "render", (98, 352, 772, 496), 250),
    ("cdd_p32_dosing_pole_1", 32, "e:0", None, None),
    ("cdd_p32_dosing_pole_2", 32, "e:1", None, None),
    ("cdd_p32_measuring_dose", 32, "e:2", None, None),
    ("cdd_p35_giving_azm", 35, "e:0", None, None),
    ("cdd_p36_child_record_card", 36, "render", (510, 170, 792, 538), 450),
    ("cdd_p37_house_marking", 37, "render", (491, 142, 820, 497), 250),
    ("cdd_p41_reconciliation_photo", 41, "e:2", None, None),
    ("cdd_p47_child_record_card_front", 47, "e:3", None, None),
    ("cdd_p49_cdd_filling_card", 49, "e:0", None, None),
    ("cdd_p54_cohort_icon", 54, "e:2", None, None),
    ("cdd_p59_cohort_flow", 59, "e:2", None, None),
    ("cdd_p60_m5_opener", 60, "e:1", None, None),
    ("cdd_p64_m6_do_dont", 64, "render", (7, 22, 532, 586), 250),
    ("cdd_p68_no_photos_camera", 68, "render", (109, 144, 429, 324), 250),
    ("cdd_p68_no_photos_phone", 68, "render", (485, 142, 772, 323), 250),
    ("cdd_p68_no_bribery", 68, "render", (310, 335, 579, 487), 250),
]


HIDE = {  # stem -> what to hide before rendering
    "cdd_p23_sick_danger_fever": ["text"],
    "cdd_p24_allergy_exclusion_signs": ["text"],
    "cdd_p64_m6_do_dont": [(410, 520, 520, 575)],  # page-number bubble and decorative dot
}
PHOTO = {"cdd_p37_house_marking", "cdd_p64_m6_do_dont", "cdd_p68_no_photos_camera",
         "cdd_p68_no_photos_phone", "cdd_p68_no_bribery"}


def page_images(page):
    return list(page.get_objects(filter=[raw.FPDF_PAGEOBJ_IMAGE], max_depth=8))


def extract_embedded(page, n):
    """The embedded raster in its own encoding. Falls back to a lossless PNG of the
    decoded pixels when the stream cannot be passed through (e.g. it has a soft mask)."""
    obj = page_images(page)[n]
    buf = io.BytesIO()
    try:
        obj.extract(buf)
        data = buf.getvalue()
        fmt = Image.open(io.BytesIO(data)).format
        if fmt in ("JPEG", "PNG"):
            return data, ".jpg" if fmt == "JPEG" else ".png", "embedded original, passed through"
    except Exception:
        pass
    pil = obj.get_bitmap(render=True).to_pil()  # render=True applies the soft mask
    buf = io.BytesIO()
    pil.save(buf, "PNG", optimize=True)
    return buf.getvalue(), ".png", "embedded original, decoded to lossless PNG"


def hide(page, rules):
    h = page.get_size()[1]
    for obj in list(page.get_objects(max_depth=1)):
        left, bottom, right, top = obj.get_bounds()
        for rule in rules:
            if rule == "text" and obj.type == raw.FPDF_PAGEOBJ_TEXT:
                page.remove_obj(obj)
                break
            if isinstance(rule, tuple):
                x0, y0, x1, y1 = rule
                if left >= x0 and right <= x1 and h - top >= y0 and h - bottom <= y1:
                    page.remove_obj(obj)
                    break
    page.gen_content()


def render(page, box, dpi, rules, photo):
    if rules:
        hide(page, rules)
    w, h = page.get_size()
    x0, y0, x1, y1 = box
    img = page.render(scale=dpi / 72, crop=(x0, h - y1, w - x1, y0)).to_pil().convert("RGB")
    buf = io.BytesIO()
    if photo:
        img.save(buf, "JPEG", quality=92, optimize=True)
        return buf.getvalue(), ".jpg", f"slide area rendered at {dpi} dpi, JPEG q92"
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue(), ".png", f"slide area rendered at {dpi} dpi"


def main(pdf_path, out):
    os.makedirs(os.path.join(out, "images"), exist_ok=True)
    for old in os.listdir(os.path.join(out, "images")):  # only files this script made
        if old.startswith("cdd_p"):
            os.remove(os.path.join(out, "images", old))
    records = []
    for stem, page_no, src, box, dpi in FIGURES:
        page = pdfium.PdfDocument(pdf_path)[page_no - 1]  # fresh copy: hiding never leaks into other figures
        if src == "render":
            notes = HIDE.get(stem, [])
            data, ext, how = render(page, box, dpi, notes, stem in PHOTO)
            if notes:
                how += "; hidden first: " + ", ".join("body text" if n == "text" else "page-number bubble" for n in notes)
        else:
            data, ext, how = extract_embedded(page, int(src[2:]))
        path = os.path.join(out, "images", stem + ext)
        with open(path, "wb") as f:
            f.write(data)
        im = Image.open(path)
        im.verify()
        records.append({"file": stem + ext, "page": page_no, "source": how, "px": list(Image.open(path).size),
                        "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        print(stem + ext, records[-1]["px"], len(data) // 1024, "KB", how)
    with open(os.path.join(out, "images_build.json"), "w", encoding="utf-8") as f:
        json.dump(records, f, indent=1)
    with open(os.path.join(out, "pdf_image_census.json"), "w", encoding="utf-8") as f:
        json.dump(census(pdfium.PdfDocument(pdf_path)), f, indent=1)


# Picture-sized rasters that are not pictures: headings saved as images, a blurred background.
NOT_PICTURE = {(2, 0), (3, 0), (39, 0), (60, 0)}


def census(doc):
    """How many rasters the PDF holds, and how many of them are picture-sized (not text strips,
    bullets or slivers of composed slides)."""
    total, pages, pictures = 0, 0, 0
    for i in range(len(doc)):
        objs = page_images(doc[i])
        total += len(objs)
        pages += bool(objs)
        for n, obj in enumerate(objs):
            left, bottom, right, top = obj.get_bounds()
            w, h = right - left, top - bottom
            if w * h >= 2500 and 0.15 < w / max(h, 1) < 7 and (i + 1, n) not in NOT_PICTURE:
                pictures += 1
    return {"embedded_total": total, "pages_with_images": pages, "content_pictures": pictures}


if __name__ == "__main__":
    main(*sys.argv[1:3])
