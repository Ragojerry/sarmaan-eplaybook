#!/usr/bin/env bash
# Sets up release signing for the Android build. Run from Git Bash:
#   cd mobile && bash tools/setup_release_signing.sh
# It (1) asks for your keystore location, alias and passwords and writes android/key.properties,
# (2) patches android/app/build.gradle so release builds are signed with that key,
# (3) makes sure key.properties and keystores are ignored by Git.
# Safe to run again. Your passwords are only written to android/key.properties on this computer.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -f android/app/build.gradle.kts ]; then
  GRADLE=android/app/build.gradle.kts; KIND=kts
elif [ -f android/app/build.gradle ]; then
  GRADLE=android/app/build.gradle; KIND=groovy
else
  echo "android/app/build.gradle(.kts) not found. Run this from the mobile folder of the project."
  exit 1
fi
echo "Using $GRADLE ($KIND)"

DEFAULT_KS="$HOME/sarmaan-release.jks"
read -r -p "Keystore file [$DEFAULT_KS]: " KS
KS="${KS:-$DEFAULT_KS}"
[ -f "$KS" ] || { echo "Keystore not found: $KS"; exit 1; }
read -r -p "Key alias [sarmaan]: " ALIAS
ALIAS="${ALIAS:-sarmaan}"
read -r -s -p "Keystore password: " SP; echo
read -r -s -p "Key password (press Enter if same as keystore password): " KP; echo
KP="${KP:-$SP}"

# Verify the passwords and alias BEFORE writing anything
if command -v keytool >/dev/null 2>&1; then
  if ! keytool -list -keystore "$KS" -storepass "$SP" -alias "$ALIAS" >/dev/null 2>&1; then
    echo "keytool could not open the keystore with that alias and password. Nothing was changed."
    exit 1
  fi
  echo "Keystore and alias verified."
else
  echo "(keytool not on PATH; skipping verification)"
fi

# Gradle wants forward slashes (C:/Users/...), even on Windows.
if command -v cygpath >/dev/null 2>&1; then KS_PATH="$(cygpath -m "$KS")"; else KS_PATH="$KS"; fi

umask 077
cat > android/key.properties <<PROPS
storePassword=$SP
keyPassword=$KP
keyAlias=$ALIAS
storeFile=$KS_PATH
PROPS
echo "Wrote android/key.properties"

[ -f "$GRADLE.before-signing.bak" ] || cp "$GRADLE" "$GRADLE.before-signing.bak"
PATCH="$(mktemp)"
cat > "$PATCH" <<'PY'
import re, sys
p = sys.argv[1]
kind = sys.argv[2]
s = open(p, encoding="utf-8").read()
if "keystoreProperties" in s:
    print("build.gradle already patched; leaving it as is")
    sys.exit(0)

if kind == "kts":
    if "keystoreProperties" in s:
        print("build.gradle.kts already patched; leaving it as is")
        sys.exit(0)
    imports = ""
    for imp in ("import java.util.Properties", "import java.io.FileInputStream"):
        if imp not in s:
            imports += imp + "\n"
    s = imports + s
    loader = '''val keystoreProperties = Properties()
val keystorePropertiesFile = rootProject.file("key.properties")
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(FileInputStream(keystorePropertiesFile))
}

'''
    s, n = re.subn(r"(?m)^android\s*\{", lambda m: loader + "android {", s, count=1)
    if n == 0:
        print("Could not find the android { block; edit by hand."); sys.exit(1)
    signing = '''    signingConfigs {
        create("release") {
            if (keystorePropertiesFile.exists()) {
                keyAlias = keystoreProperties["keyAlias"] as String
                keyPassword = keystoreProperties["keyPassword"] as String
                storeFile = file(keystoreProperties["storeFile"] as String)
                storePassword = keystoreProperties["storePassword"] as String
            }
        }
    }

'''
    pick = 'signingConfig = if (keystorePropertiesFile.exists()) signingConfigs.getByName("release") else signingConfigs.getByName("debug")'
    if re.search(r"(?m)^\s*buildTypes\s*\{", s):
        s = re.sub(r"(?m)^(\s*)buildTypes\s*\{", lambda m: signing + m.group(0), s, count=1)
        s, n = re.subn(r"signingConfig\s*=\s*signingConfigs(?:\.getByName\(\"debug\"\)|\.debug)", pick, s, count=1)
        if n == 0:
            s = re.sub(r"(?m)^(\s*)release\s*\{", lambda m: m.group(0) + "\n" + m.group(1) + "    " + pick, s, count=1)
    else:
        # No buildTypes block at all (minimal project): add signing and a release build type.
        block = signing + '''    buildTypes {
        release {
            ''' + pick + '''
        }
    }

'''
        s = re.sub(r"(?m)^android\s*\{[^\n]*\n", lambda m: m.group(0) + block, s, count=1)
    open(p, "w", encoding="utf-8").write(s)
    print("Patched", p)
    sys.exit(0)

loader = '''def keystoreProperties = new Properties()
def keystorePropertiesFile = rootProject.file("key.properties")
if (keystorePropertiesFile.exists()) {
    keystorePropertiesFile.withInputStream { keystoreProperties.load(it) }
}

'''
s = s.replace("android {", loader + "android {", 1)

signing = '''    signingConfigs {
        release {
            if (keystorePropertiesFile.exists()) {
                keyAlias keystoreProperties["keyAlias"]
                keyPassword keystoreProperties["keyPassword"]
                storeFile file(keystoreProperties["storeFile"])
                storePassword keystoreProperties["storePassword"]
            }
        }
    }

'''
s = s.replace("    buildTypes {", signing + "    buildTypes {", 1)

s, n = re.subn(r"signingConfig\s*=?\s*signingConfigs\.debug",
               "signingConfig = keystorePropertiesFile.exists() ? signingConfigs.release : signingConfigs.debug", s, count=1)
if n == 0:
    print("Could not find the release signingConfig line; edit build.gradle by hand (see docs).")
    sys.exit(1)
open(p, "w", encoding="utf-8").write(s)
print("Patched", p)
PY
if command -v python3 >/dev/null 2>&1 && python3 -c "" 2>/dev/null; then PY=python3; else PY=python; fi
"$PY" "$PATCH" "$GRADLE" "$KIND"
rm -f "$PATCH"

MANIFEST=android/app/src/main/AndroidManifest.xml
if [ -f "$MANIFEST" ]; then
  for perm in INTERNET ACCESS_NETWORK_STATE; do
    if ! grep -q "android.permission.$perm" "$MANIFEST"; then
      # release builds only get permissions declared in the MAIN manifest
      sed -i.bak "0,/<application/s//<uses-permission android:name=\"android.permission.$perm\" \/>\n    <application/" "$MANIFEST"
      echo "Added $perm permission to AndroidManifest.xml"
    fi
  done
  rm -f "$MANIFEST.bak"
  echo "App name on the phone (android:label): $(grep -o 'android:label="[^"]*"' "$MANIFEST" | head -1)"
  echo "Package: $(grep -o 'applicationId[ =]*"[^"]*"' $GRADLE | head -1)"
fi

touch .gitignore
for pat in "android/key.properties" "*.jks" "*.keystore"; do
  grep -qxF "$pat" .gitignore || echo "$pat" >> .gitignore
done
echo "Release signing is set up. Build with:"
echo "  flutter build apk --release --dart-define=API_BASE_URL=https://YOUR-API/api"
