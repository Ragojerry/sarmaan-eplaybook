"""Crop/export every figure and logo, resize for the app, and write images_build.json.

usage: python -I hfw_extract.py <pdf> <work dir (hfw)> <out dir (content/hfw_flipbook)>
"""
import io
import json
import os
import sys

import pypdfium2 as pdfium
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hfw_figures import FIGURES, LOGOS, TRIM_RIGHT  # noqa: E402

pdf_path, work, out = sys.argv[1:4]
doc = pdfium.PdfDocument(pdf_path)
embedded = {(p["page"], im["file"]): im for p in json.load(open(os.path.join(work, "embedded.json"))) for im in p["images"]}
PREVIEW_W = 1100
LIMIT = 300 * 1024
os.makedirs(os.path.join(out, "images"), exist_ok=True)
os.makedirs(os.path.join(out, "assets", "logos"), exist_ok=True)


def render_box(page_no, box, dpi, margin):
    page = doc[page_no - 1]
    w, h = page.get_size()
    k = w / PREVIEW_W
    x0, y0, x1, y1 = box
    x0, y0 = max(0, x0 - margin), max(0, y0 - margin)
    x1, y1 = min(PREVIEW_W, x1 + margin), min(h / k, y1 + margin)
    return page.render(scale=dpi / 72, crop=(x0 * k, h - y1 * k, w - x1 * k, y0 * k)).to_pil().convert("RGB")


def bbox_to_preview(page_no, bbox):
    w, _ = doc[page_no - 1].get_size()
    k = PREVIEW_W / w
    return tuple(round(v * k, 1) for v in bbox)


def encode(img, kind):
    """-> (bytes, ext, note). Never recolours; only scales and compresses."""
    note = []
    max_w = 1080 if kind == "photo" else 1600
    if img.width > max_w:
        img = img.resize((max_w, round(img.height * max_w / img.width)), Image.LANCZOS)
        if kind == "photo":
            note.append(f"scaled to {max_w}px wide")
    if kind == "photo":
        for q in (85, 80, 75, 70):
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
            if buf.tell() <= LIMIT:
                break
        if q != 85:
            note.append(f"JPEG quality {q} to fit 300 KB")
        return buf.getvalue(), ".jpg", img.size, note
    # diagrams and forms: PNG; shrink width before giving up on the limit
    floor = 1200 if kind == "form" else 0
    widths = [img.width] + [w for w in (1400, 1200, 1080) if floor <= w < img.width]
    for w in widths:
        im = img if w == img.width else img.resize((w, round(img.height * w / img.width)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "PNG", optimize=True)
        if buf.tell() <= LIMIT:
            if w != img.width:
                note.append(f"scaled to {w}px wide to fit 300 KB")
            elif kind != "photo" and w == 1600:
                note.append("scaled to 1600px wide")
            return buf.getvalue(), ".png", im.size, note
    if kind == "form":
        note.append(f"form kept above 300 KB at {im.width}px: smaller would make the print unreadable")
        return buf.getvalue(), ".png", im.size, note
    # painted illustrations do not compress as PNG; JPEG keeps colours and labels
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85, optimize=True, progressive=True)
    note.append("saved as JPEG q85: painted illustration exceeds 300 KB as PNG")
    return buf.getvalue(), ".jpg", img.size, note


def source_image(page_no, src, box, kind, cover):
    """-> (PIL image, how, preview box used)."""
    if src != "render":
        meta = embedded[(page_no, src)]
        img = Image.open(os.path.join(work, "embedded", src)).convert("RGB")
        bw, bh = meta["bbox"][2] - meta["bbox"][0], meta["bbox"][3] - meta["bbox"][1]
        if abs((img.width / img.height) / (bw / bh) - 1) <= 0.02:
            return img, f"embedded original {src} ({img.width}x{img.height})", bbox_to_preview(page_no, meta["bbox"])
        box = box or bbox_to_preview(page_no, meta["bbox"])
        how_extra = f"; embedded {src} is clipped on the page, so cropped from render"
        native_dpi = img.width / (bw / 72)
    else:
        how_extra = ""
        native_dpi = None
    dpi = 450 if kind == "form" else 200
    if native_dpi:  # re-rendering a low-res raster above 2x its own resolution adds bytes, not detail
        dpi = min(dpi, max(200, round(native_dpi * 2)))
    margin = 0 if cover else 4
    return render_box(page_no, box, dpi, margin), f"render crop at {dpi} dpi{how_extra}", box


records = []
for stem, page_no, module, src, box, kind, itype, heading in FIGURES:
    img, how, used = source_image(page_no, src, box, kind, itype == "cover")
    if stem in TRIM_RIGHT:
        img = img.crop((0, 0, round(img.width * TRIM_RIGHT[stem]), img.height))
        how += f"; right {round((1 - TRIM_RIGHT[stem]) * 100, 1)}% trimmed (page side bar baked into the raster)"
    data, ext, size, note = encode(img, kind)
    path = os.path.join(out, "images", stem + ext)
    with open(path, "wb") as f:
        f.write(data)
    Image.open(path).verify()
    records.append({"file": stem + ext, "page": page_no, "module": module, "heading": heading, "type": itype,
                    "kind": kind, "px": list(size), "bytes": len(data), "source": how, "box": list(used), "note": "; ".join(note)})
    print(stem + ext, size, len(data) // 1024, "KB", how, "|", "; ".join(note))

for name, page_no, src, box in LOGOS:
    if src == "render":
        img = render_box(page_no, box, 300, 2)
    else:
        img = Image.open(os.path.join(work, "embedded", src)).convert("RGBA")
    path = os.path.join(out, "assets", "logos", name + ".png")
    img.save(path, "PNG", optimize=True)
    records.append({"file": "assets/logos/" + name + ".png", "page": page_no, "logo": True, "px": list(img.size),
                    "bytes": os.path.getsize(path), "source": "render crop at 300 dpi" if src == "render" else f"embedded original {src}"})
    print("logo", name, img.size)

json.dump(records, open(os.path.join(work, "images_build.json"), "w"), indent=1)

# completeness overlays: every page that has a figure, with the crop boxes drawn on the preview
os.makedirs(os.path.join(work, "overlay"), exist_ok=True)
by_page = {}
for r in records:
    if not r.get("logo"):
        by_page.setdefault(r["page"], []).append(r["box"])
for p, boxes in by_page.items():
    im = Image.open(os.path.join(work, "preview", f"p{p:02d}.jpg")).convert("RGB")
    d = ImageDraw.Draw(im)
    for i, b in enumerate(boxes, 1):
        d.rectangle(b, outline=(255, 0, 255), width=4)
        d.text((b[0] + 6, b[1] + 4), str(i), fill=(255, 0, 255))
    im.save(os.path.join(work, "overlay", f"p{p:02d}.jpg"), quality=70)
