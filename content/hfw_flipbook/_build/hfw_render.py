"""Render every page at 200 dpi plus a reading preview, and extract embedded rasters with their positions."""
import json
import os
import sys

import pypdfium2 as pdfium
import pypdfium2.raw as raw

pdf_path, out = sys.argv[1], sys.argv[2]
for d in ("render200", "preview", "embedded"):
    os.makedirs(os.path.join(out, d), exist_ok=True)

doc = pdfium.PdfDocument(pdf_path)
info = []
for i in range(len(doc)):
    pno = i + 1
    page = doc[i]
    w, h = page.get_size()
    page.render(scale=200 / 72).to_pil().save(os.path.join(out, "render200", f"p{pno:02d}.png"))
    page.render(scale=1100 / w).to_pil().convert("RGB").save(
        os.path.join(out, "preview", f"p{pno:02d}.jpg"), quality=80)
    imgs = []
    for n, obj in enumerate(page.get_objects(filter=[raw.FPDF_PAGEOBJ_IMAGE], max_depth=8)):
        left, bottom, right, top = obj.get_bounds()
        try:
            px = obj.get_px_size()
        except Exception:
            px = None
        name = f"p{pno:02d}_e{n:02d}"
        saved = None
        try:
            pil = obj.get_bitmap(render=False).to_pil()
            saved = name + ".png"
            pil.save(os.path.join(out, "embedded", saved))
        except Exception as exc:  # some filters cannot be decoded raw; fall back to rendered
            try:
                pil = obj.get_bitmap(render=True).to_pil()
                saved = name + "_r.png"
                pil.save(os.path.join(out, "embedded", saved))
            except Exception as exc2:
                saved = f"FAILED {exc} / {exc2}"
        imgs.append({
            "n": n, "file": saved, "px": px,
            # bbox in PDF points with top-left origin, to match the renders
            "bbox": [round(left, 1), round(h - top, 1), round(right, 1), round(h - bottom, 1)],
        })
    info.append({"page": pno, "size": [round(w), round(h)], "images": imgs})
    print(pno, len(imgs), flush=True)

with open(os.path.join(out, "embedded.json"), "w") as f:
    json.dump(info, f, indent=1)
