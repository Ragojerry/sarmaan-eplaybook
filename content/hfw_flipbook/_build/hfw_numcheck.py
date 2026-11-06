import csv, glob, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
out, notes = sys.argv[1], sys.argv[2]
ref = open(notes, encoding="utf-8").read()
norm = lambda t: t.replace("–", "-").replace("—", "-").replace(" ", "").lower()
R = norm(ref)
tok = re.compile(r"[A-Za-z/]*\d[\w/.\-–]*")
missing = {}
files = glob.glob(os.path.join(out, "en", "*.csv")) + [os.path.join(out, "quizzes.csv")]
for f in files:
    for row in csv.reader(open(f, encoding="utf-8-sig")):
        for cell in row[2:]:
            if not cell or re.fullmatch(r"[0-9a-f\-]{36}\|.*", cell):
                continue
            for t in tok.findall(cell):
                t2 = t.rstrip(".,;:)")
                if len(t2) < 1 or re.fullmatch(r"m\d_p\d+_\d+\.\w+", t2):
                    continue
                if norm(t2) not in R:
                    missing.setdefault(t2, set()).add(os.path.basename(f))
for k, v in sorted(missing.items()):
    print(repr(k), sorted(v))
print("tokens not found in transcription:", len(missing))
