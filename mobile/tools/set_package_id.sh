#!/usr/bin/env bash
# Changes the Android package ID everywhere it matters.
#   cd mobile && bash tools/set_package_id.sh [new.package.id]
# Default new ID: org.malariaconsortium.sarmaan
# Updates: namespace and applicationId in android/app/build.gradle(.kts), the package line and folder of
# MainActivity, and any `package=` in AndroidManifest.xml. A backup of each changed file is kept in android/.before-id-backup/.
set -euo pipefail
cd "$(dirname "$0")/.."
NEW="${1:-org.malariaconsortium.sarmaan}"

if ! echo "$NEW" | grep -Eq '^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$'; then
  echo "Invalid ID '$NEW'. Use lowercase letters, digits, underscores, at least two parts separated by dots."
  exit 1
fi
if [ -f android/app/build.gradle.kts ]; then GRADLE=android/app/build.gradle.kts
elif [ -f android/app/build.gradle ]; then GRADLE=android/app/build.gradle
else echo "android/app/build.gradle(.kts) not found. Run from the mobile folder."; exit 1; fi

OLD="$(grep -Eo 'applicationId[ =]*"[^"]+"' "$GRADLE" | head -1 | sed -E 's/.*"([^"]+)"/\1/')"
[ -n "$OLD" ] || { echo "Could not read the current applicationId from $GRADLE"; exit 1; }
if [ "$OLD" = "$NEW" ]; then echo "Package ID is already $NEW. Nothing to do."; exit 0; fi
echo "Changing package ID:  $OLD  ->  $NEW"

PATCH="$(mktemp)"
cat > "$PATCH" <<'PY'
import os, re, shutil, sys
old, new, gradle = sys.argv[1], sys.argv[2], sys.argv[3]

def backup(path):
    # keep backups OUTSIDE the source folders so old directories can be removed cleanly
    os.makedirs("android/.before-id-backup", exist_ok=True)
    b = os.path.join("android/.before-id-backup", path.replace("/", "_").replace("\\", "_") + ".bak")
    if not os.path.exists(b):
        shutil.copy2(path, b)

def rewrite(path, fn):
    s = open(path, encoding="utf-8").read()
    t = fn(s)
    if t != s:
        backup(path)
        open(path, "w", encoding="utf-8").write(t)
        print("updated", path)

# 1. gradle: namespace and applicationId
def fix_gradle(s):
    s = re.sub(r'(namespace\s*=?\s*)"%s"' % re.escape(old), r'\1"%s"' % new, s)
    s = re.sub(r'(applicationId\s*=?\s*)"%s"' % re.escape(old), r'\1"%s"' % new, s)
    return s
rewrite(gradle, fix_gradle)

# 2. manifest package attribute (older projects)
manifests = []
for root, _, files in os.walk("android/app/src"):
    for f in files:
        if f == "AndroidManifest.xml":
            manifests.append(os.path.join(root, f))
for m in manifests:
    rewrite(m, lambda s: s.replace('package="%s"' % old, 'package="%s"' % new))

# 3. MainActivity: package line and folder
moved = False
for lang in ("kotlin", "java"):
    base = os.path.join("android/app/src/main", lang)
    if not os.path.isdir(base):
        continue
    for root, _, files in os.walk(base):
        for f in files:
            if not f.endswith((".kt", ".java")):
                continue
            path = os.path.join(root, f)
            s = open(path, encoding="utf-8").read()
            m = re.search(r"(?m)^package\s+([\w.]+)\s*;?\s*$", s)
            if not m or m.group(1) != old:
                continue
            s2 = re.sub(r"(?m)^package\s+[\w.]+", "package " + new, s, count=1)
            s2 = s2.replace(old, new)
            newdir = os.path.join(base, *new.split("."))
            os.makedirs(newdir, exist_ok=True)
            target = os.path.join(newdir, f)
            backup(path)
            open(target, "w", encoding="utf-8").write(s2)
            if os.path.abspath(target) != os.path.abspath(path):
                os.remove(path)
                # remove now-empty old folders up to the language root
                d = os.path.dirname(path)
                while os.path.abspath(d) != os.path.abspath(base) and not os.listdir(d):
                    os.rmdir(d)
                    d = os.path.dirname(d)
            print("moved", path, "->", target)
            moved = True
if not moved:
    print("WARNING: no MainActivity with package", old, "found. If the app crashes at launch, check src/main/kotlin or src/main/java.")

# 4. report leftovers
left = []
for root, _, files in os.walk("android"):
    if any(x in root for x in ("/build", "\\build", ".gradle", ".dart_tool")):
        continue
    for f in files:
        if f.endswith((".bak", ".jar", ".png", ".webp", ".jks", ".class", ".apk")):
            continue
        p = os.path.join(root, f)
        try:
            if old in open(p, encoding="utf-8").read():
                left.append(p)
        except Exception:
            pass
if left:
    print("Still mentions the old ID (check by hand):")
    for p in left:
        print("  ", p)
else:
    print("No other mentions of the old ID under android/.")
PY
if command -v python3 >/dev/null 2>&1 && python3 -c "" 2>/dev/null; then PY=python3; else PY=python; fi
"$PY" "$PATCH" "$OLD" "$NEW" "$GRADLE"
rm -f "$PATCH"

echo
echo "Done. Next:"
echo "  adb uninstall $OLD        # remove the old test build if it is on a phone/emulator"
echo "  flutter clean && flutter pub get"
echo "  flutter build apk --release --dart-define=API_BASE_URL=https://YOUR-ADDRESS/api"
echo "(iOS uses its own bundle ID in ios/Runner.xcodeproj; not changed here.)"
