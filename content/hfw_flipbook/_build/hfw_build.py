"""Builds every HFW deliverable from the content DSL and runs the completeness checks.

usage (from anywhere):  python -I content/hfw_flipbook/_build/hfw_build.py
Writes into content/hfw_flipbook/. Never hand-edit the generated files; edit the
_build/*.py sources and re-run.
"""
import csv
import io
import json
import math
import os
import re
import sys
import uuid
from collections import Counter, defaultdict

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding="utf-8")
import hfw_content_a  # noqa: E402,F401
import hfw_content_b  # noqa: E402,F401
import hfw_content_c  # noqa: E402,F401
from hfw_dsl import MODULES  # noqa: E402
from hfw_figures import FIGURES, LOGOS  # noqa: E402
from hfw_meta import BAKED, EXCLUDED, FIGURE_PAGES, FURNITURE, HAUSA, PAGE_NOTES, RIGHTS  # noqa: E402
from hfw_modules import ALL_ROLES, APP_MODULES, learning_order  # noqa: E402
from hfw_quiz import Q  # noqa: E402
from hfw_quiz_extra import X  # noqa: E402

work = os.path.join(HERE, "data")
out = os.path.dirname(HERE)
NS = uuid.UUID("5b3d1c9e-7a52-4f0e-9a8e-1f2b3c4d5e6f")
QNS = uuid.UUID("0c1f7a52-3b9e-4d6a-8e21-7f5a9c3b2d10")
problems, warnings = [], []
TEXT_PATHS = {"HEADING": ["text"], "TEXT": ["text"]}
WPM = 80  # plain-language reading speed assumed for field staff


def csv_safe(v):  # same guard as app/content/translation_io.py
    t = "" if v is None else str(v)
    return "'" + t if t[:1] in ("=", "+", "-", "@", "\t", "\r") else t


def flatten(s):
    c, k = s["content"], s["type"]
    if k in TEXT_PATHS:
        return [("text", c["text"])]
    if k == "LIST":
        return [(f"items.{i}", it) for i, it in enumerate(c["items"])]
    if k in ("CALLOUT", "WARNING"):
        return [("heading", c["heading"]), ("text", c["text"])]
    if k == "TABLE":
        return [(f"headers.{i}", h) for i, h in enumerate(c["headers"])] + \
               [(f"rows.{r}.{j}", v) for r, row in enumerate(c["rows"]) for j, v in enumerate(row)]
    if k == "IMAGE":
        return [("caption", c["caption"]), ("alt", c["alt"])]
    raise ValueError(k)


def write_csv(path, header, rows, bom=True):
    buf = io.StringIO()
    w = csv.writer(buf)  # QUOTE_MINIMAL, \r\n: identical to the app exporter
    w.writerow(header)
    w.writerows(rows)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(("﻿" if bom else "") + buf.getvalue())


# ---------------------------------------------------------------- flipbook sections with their stable ids
for m in MODULES:
    for n, s in enumerate(m["sections"], 1):
        s["id"] = str(uuid.uuid5(NS, f"hfw|{m['code']}|{n}"))  # never changes: CSV keys depend on it
        s["orig"] = (m["code"], n)
by_orig = {(m["code"], n): s for m in MODULES for n, s in enumerate(m["sections"], 1)}

# ---------------------------------------------------------------- assemble app modules (membership only)
assigned = Counter()
for am in APP_MODULES:
    am["sections"] = []
    for orig, a, b in am["parts"]:
        for n in range(a, b + 1):
            if (orig, n) not in by_orig:
                problems.append(f"{am['code']}: {orig} section {n} does not exist")
                continue
            am["sections"].append(by_orig[(orig, n)])
            assigned[(orig, n)] += 1
    if am["audience"] == "ROLE_SPECIFIC" and not am["roles"]:
        problems.append(f"{am['code']}: role-specific module with no role")
    if am["audience"] == "GENERAL" and am["roles"]:
        problems.append(f"{am['code']}: GENERAL modules keep learner_roles empty")
    for r in am["roles"]:
        if r not in ALL_ROLES:
            problems.append(f"{am['code']}: unknown role {r}")
for key, s in by_orig.items():
    if assigned[key] != 1:
        problems.append(f"section {key} is in {assigned[key]} app modules (must be exactly 1)")


def words(s):
    return sum(len(str(t).split()) for p, t in flatten(s) if p != "alt") + len((s["title"] or "").split())


for am in APP_MODULES:
    w = sum(words(s) for s in am["sections"])
    imgs = sum(1 for s in am["sections"] if s["type"] == "IMAGE")
    tables = sum(1 for s in am["sections"] if s["type"] == "TABLE")
    reading = w / WPM + 0.5 * imgs + 1.0 * tables
    am["words"], am["reading_min"] = w, reading
    am["estimated_minutes"] = int(math.ceil((reading + 10) / 5.0) * 5)  # + pre- and post-test (10 questions each)

# ---------------------------------------------------------------- module CSVs, alt_text.csv, content json
for fn in os.listdir(os.path.join(out, "en")):
    if fn.startswith("module_hfw_") and fn.endswith(".csv"):
        os.remove(os.path.join(out, "en", fn))  # generated files only; rebuilt below
image_use = Counter()
img_section = {}
manifest, alt_rows, content_json = [], [], []
ORDER = {am['code']: i for i, am in enumerate(learning_order(), 1)}
for am in APP_MODULES:
    order = ORDER[am['code']]
    rows = [["MODULE|title", "Module title", csv_safe(am["title"]), ""],
            ["MODULE|description", "Module description", csv_safe(am["description"]), ""]]
    jm = {"module_code": am["code"], "learning_order": order, "title": am["title"], "description": am["description"],
          "audience": am["audience"], "learner_roles": am["roles"],
          "roles_display": ALL_ROLES if am["audience"] == "GENERAL" else am["roles"],
          "estimated_minutes": am["estimated_minutes"], "sections": []}
    for n, s in enumerate(am["sections"], 1):
        sid = s["id"]
        label = f"Section {n} ({s['type']})"
        if s["title"]:
            rows.append([f"{sid}|@title", label + " title", csv_safe(s["title"]), ""])
        for path, text in flatten(s):
            if path == "alt":
                alt_rows.append([f"{sid}|alt", csv_safe(text), ""])  # importer rejects |alt today (open_questions A3)
            else:
                rows.append([f"{sid}|{path}", f"{label} {path}", csv_safe(text), ""])
        img = s["content"].get("image_file", "")
        if img:
            image_use[img] += 1
            img_section[img] = (am["code"], sid, n, s, am)
            if not s["content"]["caption"].strip() or not s["content"]["alt"].strip():
                problems.append(f"{img}: missing caption or alt")
        roles = "ALL (GENERAL)" if am["audience"] == "GENERAL" else ";".join(am["roles"])
        manifest.append([am["code"], am["audience"], roles, sid, n, s["type"], ";".join(map(str, s["pages"])),
                         f"{s['orig'][0]}#{s['orig'][1]}", ";".join(s["tags"]), s["evidence"],
                         "yes" if s["inferred"] else "no", img,
                         "transcribed from image" if s.get("transcribed") else "", s.get("flag") or ""])
        jm["sections"].append({"id": sid, "section_number": n, "content_type": s["type"], "title": s["title"],
                               "pdf_pages": s["pages"], "flipbook_origin": f"{s['orig'][0]}#{s['orig'][1]}",
                               "content": s["content"], "transcribed_from_image": bool(s.get("transcribed"))})
        if s["type"] == "LIST" and len(s["content"]["items"]) > 5:
            problems.append(f"{am['code']} s{n}: list has {len(s['content']['items'])} items")
        if s["type"] != "IMAGE":
            for _, text in flatten(s):
                for sent in re.split(r"(?<=[.?!])\s+", text):
                    if len(sent.split()) >= 20 and not s.get("transcribed") and s["type"] != "TABLE":
                        warnings.append(f"{am['code']} s{n}: {len(sent.split())} words: {sent[:70]}...")
    write_csv(os.path.join(out, "en", f"module_hfw_{am['code'][4:]}.csv"), ["key", "where", "english", "translation"], rows)
    content_json.append(jm)
content_json.sort(key=lambda m: m["learning_order"])
write_csv(os.path.join(out, "alt_text.csv"), ["key", "english", "translation"], alt_rows)
with open(os.path.join(out, "content_sections.json"), "w", encoding="utf-8") as f:
    json.dump(content_json, f, ensure_ascii=False, indent=1)

covered = {p for r in manifest for p in map(int, r[6].split(";"))}
for p in range(1, 89):
    if p not in covered:
        manifest.append(["", "", "", "", "", "PAGE ONLY", str(p), "", "", "", "", "", "", PAGE_NOTES.get(p, "MISSING NOTE")])
        if p not in PAGE_NOTES:
            problems.append(f"page {p} not covered by any section and has no page note")
write_csv(os.path.join(out, "manifest.csv"),
          ["module", "module_audience", "module_roles", "section_id", "section_no", "section_type", "pdf_pages",
           "flipbook_origin", "earlier_section_tag", "tag_evidence", "tag_inferred", "image_file", "transcription",
           "flag_or_note"], manifest)

# ---------------------------------------------------------------- images manifest
build = {r["file"]: r for r in json.load(open(os.path.join(work, "images_build.json")))}
img_rows, per_module, per_page = [], defaultdict(int), Counter()
for stem, page, _flip_module, src, box, kind, itype, heading in FIGURES:
    f = next(k for k in build if k.split(".")[0] == stem and not k.startswith("assets/"))
    b = build[f]
    with Image.open(os.path.join(out, "images", f)) as im:
        im.load()
    per_page[page] += 1
    if image_use[f] != 1:
        problems.append(f"{f} used in {image_use[f]} IMAGE sections (must be exactly 1)")
    if b["bytes"] > 300 * 1024 and kind != "form":
        problems.append(f"{f} is {b['bytes'] // 1024} KB")
    sec = img_section.get(f)
    mod = sec[0] if sec else ""
    per_module[mod] += b["bytes"]
    roles = ("ALL (GENERAL)" if sec[4]["audience"] == "GENERAL" else ";".join(sec[4]["roles"])) if sec else ""
    baked = BAKED.get(stem, "")
    img_rows.append([f, page, mod, heading, itype, f"{b['px'][0]}x{b['px'][1]}", b["bytes"], "yes" if baked else "no",
                     baked, sec[1] if sec else "", roles, b["source"], b["note"], RIGHTS.get(stem, ""), "lesson image"])
for name, page, src, box in LOGOS:
    f = f"assets/logos/{name}.png"
    b = build[f]
    img_rows.append([f, page, "", "Title page partner marks" if page == 1 else "NAFDAC Med Safety App", "logo",
                     f"{b['px'][0]}x{b['px'][1]}", b["bytes"], "yes", "logo wordmark", "", "", b["source"], "",
                     "Partner/third-party mark: use only with permission", "logo (not in lessons)"])
for item in EXCLUDED:
    img_rows.append([item["what"], item["page"], "", "", "excluded", "", "", "", "", "", "", "", "", "",
                     "excluded: " + item["reason"]])
write_csv(os.path.join(out, "images_manifest.csv"),
          ["file", "page", "module", "nearby_heading", "image_type", "pixel_size", "bytes", "text_baked_in",
           "baked_text", "section_id", "module_roles", "source", "processing_note", "rights_or_consent_flag", "status"], img_rows)
write_csv(os.path.join(out, "excluded_page_furniture.csv"), ["item", "pages", "reason"],
          [[f["item"], f["pages"], f["reason"]] for f in FURNITURE])
for f in image_use:
    if f not in {r[0] for r in img_rows}:
        problems.append(f"IMAGE section points at a missing file: {f}")
for p in FIGURE_PAGES:
    if per_page[p] == 0:
        problems.append(f"page {p} shows a figure but has no extracted lesson image")

# ---------------------------------------------------------------- embedded raster index (unchanged logic)
emb = json.load(open(os.path.join(work, "embedded.json")))
fig_boxes = defaultdict(list)
for stem, page, *_ in FIGURES:
    r = next(v for k, v in build.items() if k.split(".")[0] == stem and not k.startswith("assets/"))
    fig_boxes[page].append((r["file"], r["box"]))
logo_boxes = defaultdict(list)
for name, page, src, box in LOGOS:
    if box:
        logo_boxes[page].append((name, box))
furn_hash = {f["hash"]: f["item"] for f in FURNITURE if f.get("hash")}
dup_files = {e["embedded"]: e["reason"] for e in EXCLUDED if e.get("embedded")}
K = 1100 / 842


def inside(bb, box):
    x0, y0, x1, y1 = [v * K for v in bb]
    a = max(1e-6, (x1 - x0) * (y1 - y0))
    return max(0, min(x1, box[2]) - max(x0, box[0])) * max(0, min(y1, box[3]) - max(y0, box[1])) / a


idx_rows, unmapped = [], []
for p in emb:
    for im in p["images"]:
        f, h, bb = im["file"], im.get("hash"), im["bbox"]
        where = None
        if f in dup_files:
            where = "excluded: " + dup_files[f]
        elif h in furn_hash:
            where = "furniture: " + furn_hash[h]
        else:
            for name, box in logo_boxes[p["page"]]:
                if inside(bb, box) > 0.5:
                    where = f"logo: assets/logos/{name}.png"
            if p["page"] == 64 and f == "p64_e01.png":
                where = "logo: assets/logos/nafdac_med_safety_app_icon.png"
            for fn, box in fig_boxes[p["page"]]:
                if where is None and inside(bb, box) > 0.5:
                    where = f"part of {fn}"
            if where is None:
                w_pt, h_pt = bb[2] - bb[0], bb[3] - bb[1]
                if bb[1] > 535 and 380 < bb[0] < 470 and w_pt < 60:
                    where = "furniture: page-number badge"
                elif w_pt <= 16 and h_pt <= 16:
                    where = "furniture: bullet arrow"
                elif w_pt > 400 and h_pt < 15:
                    where = "furniture: header/footer rule or band"
                elif bb[0] < 1 and w_pt < 90:
                    where = "furniture: side bar"
        if where is None:
            unmapped.append((p["page"], f))
            where = "UNMAPPED"
        idx_rows.append([p["page"], f, f"{im['px'][0]}x{im['px'][1]}" if im["px"] else "", ";".join(map(str, bb)), h, where])
write_csv(os.path.join(out, "embedded_raster_index.csv"), ["page", "embedded_file", "px", "bbox_pt", "hash", "mapped_to"], idx_rows, bom=False)
for u in unmapped:
    problems.append(f"embedded raster not accounted for: page {u[0]} {u[1]}")

# ---------------------------------------------------------------- hausa image text
write_csv(os.path.join(out, "hausa_image_text.csv"),
          ["file", "page", "module", "english_text_in_image", "proposal", "proposed_hausa_caption_or_note", "caption_key"],
          [[f, img_section[f][3]["pages"][0], img_section[f][0], BAKED[f.split(".")[0]], prop, note, f"{img_section[f][1]}|caption"]
           for f, prop, note in HAUSA])
for stem, txt in BAKED.items():
    if txt and not any(h[0].split(".")[0] == stem for h in HAUSA):
        problems.append(f"{stem} has baked English text but is missing from hausa_image_text.csv")

# ---------------------------------------------------------------- quizzes: 10 per app module
page_mod = {}
for am in APP_MODULES:
    for s in am["sections"]:
        for p in s["pages"]:
            page_mod.setdefault(p, set()).add(am["code"])
quiz = []
for q in Q:  # (flipbook module, audience, question, options, correct, explanation, page, image)
    mods = page_mod.get(q[6], set())
    if len(mods) != 1:
        problems.append(f"quiz page {q[6]} maps to {mods}: {q[2][:40]}")
        continue
    quiz.append((next(iter(mods)), q[2], q[3], q[4], q[5], q[6], q[7]))
quiz += list(X)
qc = Counter(q[0] for q in quiz)
mod_by_code = {am["code"]: am for am in APP_MODULES}
for am in APP_MODULES:
    if qc[am["code"]] != 10:
        problems.append(f"quiz {am['code']}: {qc[am['code']]} questions (need 10)")
quiz_rows, seen = [], Counter()
for q in sorted(quiz, key=lambda q: (q[0], q[5])):
    mod, text, opts, correct, expl, page, img = q
    if page not in {p for s in mod_by_code[mod]["sections"] for p in s["pages"]}:
        problems.append(f"quiz {mod}: page {page} is not in the module: {text[:40]}")
    if img and img_section.get(img, ("",))[0] != mod:
        problems.append(f"quiz {mod}: image {img} is not in this module")
    if len(opts) != 4 or correct not in "ABCD":
        problems.append(f"quiz bad options: {text}")
    seen[mod] += 1
    qid = str(uuid.uuid5(QNS, f"{mod}|{text}"))
    am = mod_by_code[mod]
    roles = "ALL (GENERAL)" if am["audience"] == "GENERAL" else ";".join(am["roles"])
    quiz_rows.append([qid, mod, roles, seen[mod], csv_safe(text), *map(csv_safe, opts), correct, csv_safe(expl), page, img])
if len({r[0] for r in quiz_rows}) != len(quiz_rows):
    problems.append("duplicate quiz question ids (same question text twice in a module)")
write_csv(os.path.join(out, "quizzes.csv"),
          ["question_id", "module", "module_roles", "order", "question", "option_a", "option_b", "option_c", "option_d",
           "correct_option", "explanation", "pdf_page", "image_file"], quiz_rows)

# ---------------------------------------------------------------- modules.csv (roles, duration, learning order)
write_csv(os.path.join(out, "modules.csv"),
          ["learning_order", "module_code", "title", "description", "audience", "learner_roles", "roles_display",
           "estimated_minutes", "reading_words", "sections", "images", "image_kb", "quiz_questions", "pdf_pages"],
          [[i, am["code"], am["title"], am["description"], am["audience"], ";".join(am["roles"]),
            "ALL (GENERAL)" if am["audience"] == "GENERAL" else ";".join(am["roles"]), am["estimated_minutes"], am["words"],
            len(am["sections"]), sum(1 for s in am["sections"] if s["type"] == "IMAGE"), round(per_module[am["code"]] / 1024),
            qc[am["code"]], f"{min(p for s in am['sections'] for p in s['pages'])}-{max(p for s in am['sections'] for p in s['pages'])}",
            ]
           for i, am in enumerate(learning_order(), 1)])

# ---------------------------------------------------------------- reopen every CSV like the importer does
alt_keys = {r[0] for r in alt_rows}
for fn in sorted(os.listdir(os.path.join(out, "en"))):
    raw = open(os.path.join(out, "en", fn), "rb").read()
    if not raw.startswith(b"\xef\xbb\xbf") or raw.count(b"\n") != raw.count(b"\r\n"):
        problems.append(f"{fn}: BOM or CRLF wrong")
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    if list(rows[0].keys()) != ["key", "where", "english", "translation"]:
        problems.append(f"{fn}: header differs")
    if any(r["translation"] for r in rows) or any(r["key"].endswith("|alt") for r in rows):
        problems.append(f"{fn}: translation filled or |alt row present")
    if len({r["key"] for r in rows}) != len(rows):
        problems.append(f"{fn}: duplicate keys")
if len(alt_keys) != len(FIGURES):
    problems.append(f"alt_text.csv has {len(alt_keys)} rows, expected {len(FIGURES)}")

summary = {am["code"]: {"title": am["title"], "audience": am["audience"], "roles": am["roles"],
                        "sections": len(am["sections"]), "minutes": am["estimated_minutes"],
                        "image_kb": round(per_module[am["code"]] / 1024), "quiz": qc[am["code"]],
                        "learning_order": ORDER[am["code"]]} for am in APP_MODULES}
json.dump(summary, open(os.path.join(work, "build_summary.json"), "w"), indent=1)
for code, s in summary.items():
    print(s["learning_order"], code, s["audience"][:4], ",".join(s["roles"]) or "-", s["sections"], f"{s['minutes']}min", f"{s['image_kb']}KB", s["quiz"])
print("alt rows:", len(alt_rows), "| quiz:", len(quiz_rows), "| embedded:", len(idx_rows), "unmapped", len(unmapped))
print("WARNINGS:", len(warnings))
for w_ in warnings:
    print(" -", w_)
print("PROBLEMS:", len(problems))
for p_ in problems:
    print(" !", p_)
