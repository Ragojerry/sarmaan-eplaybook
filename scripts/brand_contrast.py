"""
WCAG 2.1 contrast for every text/background (and control/background) pair the
app and the admin portal use, computed from brand/tokens.json.

    python scripts/brand_contrast.py            # print the table, exit 1 if any pair fails
    python scripts/brand_contrast.py --write    # also write docs/brand/contrast_report.md

Thresholds: text 4.5:1; large text (>= 18.66 px bold or 24 px regular) and
controls/icons/borders that must be seen (WCAG 1.4.11) 3:1. "decor" pairs
(dividers, card outlines) are listed for completeness and have no threshold.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from brand_sync import BRAND, ROOT, resolved_colours  # noqa: E402

THRESHOLD = {"text": 4.5, "large": 3.0, "control": 3.0, "decor": 0.0}

# (foreground, background, where, kind) — semantic token names from tokens.json
PAIRS = [
    # The pairs named in the palette brief of 2026-11-12.
    ("textOnPrimary", "primary", "White text on logo teal: app bars, primary buttons", "text"),
    ("navInactive", "navBar", "Inactive bottom navigation items (#D9E8E7 on deep forest)", "text"),
    ("text", "background", "Body text on the 15% teal page", "text"),
    ("textMuted", "background", "Secondary text on the page", "text"),
    ("onAccent", "accent", "Dark text on the pale teal accent: hero label, Continue button", "text"),
    ("textOnPrimary", "primary", "White number on the logo teal badge of the next module", "text"),
    # Everything else the app and the admin portal use.
    ("navActive", "navBar", "Active bottom navigation item (white on deep forest)", "text"),
    ("textOnPrimary", "forest", "White text on Forest Green: splash top, header, hero card, admin sidebar", "text"),
    ("onPrimaryMuted", "forest", "Secondary text on Forest Green", "text"),
    ("onPrimaryMuted", "primary", "Secondary text on logo teal (hero card bottom, header)", "text"),
    ("textOnPrimary", "midBlend", "White text on the mid-blend (photo fade, button sheen)", "text"),
    ("textOnPrimary", "sheenLight", "White text on the light end of the button sheen", "text"),
    ("textOnPrimary", "deepForest", "Snack bars, admin sidebar bottom, bottom of the splash and Home header", "text"),
    ("onPrimaryMuted", "deepForest", "Secondary text at the bottom of the Home header", "text"),
    ("text", "surface", "Body text on cards", "text"),
    ("textMuted", "surface", "Secondary text on cards", "text"),
    ("text", "surfaceSelected", "Text on the pale teal tint (selected rows, chips, callouts)", "text"),
    ("textMuted", "surfaceSelected", "Secondary text on the pale teal tint, locked modules", "text"),
    ("primaryText", "background", "Teal titles, links and icons on the page", "text"),
    ("primaryText", "surface", "Teal text, outlined buttons on cards", "text"),
    ("primaryText", "surfaceSelected", "Teal text on the pale teal tint", "text"),
    ("controlBorder", "surface", "Text field and checkbox borders", "control"),
    ("primary", "surface", "Focused field border, selected radio/checkbox, next-module outline", "control"),
    ("primary", "surfaceMuted", "Dashed outline of a locked module", "control"),
    ("successText", "surface", "Success text ('Correct.') on cards", "text"),
    ("successText", "background", "Success text on the page", "text"),
    ("text", "successSurface", "Text in success callouts", "text"),
    ("textOnPrimary", "success", "White tick on the Forest Green completed disc", "control"),
    ("warning", "surface", "Warning border and icon on cards", "control"),
    ("warning", "surface", "'Update available' status label on the Updates card", "text"),
    ("warning", "warningSurface", "Warning border and icon on the warning callout", "control"),
    ("warningText", "warningSurface", "Text in warning callouts (ink)", "text"),
    ("errorText", "surface", "Error text on cards", "text"),
    ("errorText", "background", "Error text on the page", "text"),
    ("errorText", "errorSurface", "Text in error and 'Do not' callouts", "text"),
    ("textOnPrimary", "error", "White text on an error fill", "text"),
    ("textOnPrimary", "warning", "White text on a warning fill", "text"),
    ("infoText", "infoSurface", "Text in information callouts", "text"),
    ("progressFill", "progressTrack", "Progress bar fill on its track", "control"),
    ("accent", "forest", "Pale teal progress fill, label and button on the hero card (top); Online dot", "control"),
    ("accent", "primary", "Pale teal progress fill, label and button on the hero card (bottom)", "control"),
    ("text", "surfaceSelected", "Support deck rows: label, contact type and value", "text"),
    ("textMuted", "surfaceSelected", "Support deck rows: availability and languages", "text"),
    ("primaryText", "surfaceSelected", "Support deck rows: contact type icon", "control"),
    ("textMuted", "surface", "Support deck: intro, admin note, copy icon", "text"),
    ("text", "surface", "Tools repository rows: title and description", "text"),
    ("textMuted", "surface", "Tools repository rows: type, service, 'Opens online', copy and share icons", "text"),
    ("primaryText", "surface", "Tools repository rows: type icon", "control"),
    ("primaryText", "surfaceSelected", "Tools card on Home and Modules: icon on its pale tile", "control"),
    ("textDisabled", "surfaceMuted", "Disabled text (exempt from WCAG; same as muted)", "decor"),
    ("divider", "background", "Thin teal card border (rgba(0,104,92,0.18) on the card)", "decor"),
]

# Pairs that were checked and are not used, reported so the choices are visible.
REJECTED = [
    ("warning", "warningSurface", "Warning orange as text on its pale tint (4.48) - text there is ink"),
    ("accent", "surface", "The pale teal accent on cards (so the next module's badge is logo teal instead)"),
    ("textOnPrimary", "accent", "White text on the pale teal accent"),
]


def _lum(hex_colour: str) -> float:
    def ch(c: int) -> float:
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def ratio(a: str, b: str) -> float:
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def report() -> tuple[str, int]:
    tokens = json.loads((BRAND / "tokens.json").read_text(encoding="utf-8"))
    colours = resolved_colours(tokens)
    sem = {k: colours[v] for k, v in tokens["semantic"].items()}
    lines = ["# Contrast report", "",
             "Generated by `scripts/brand_contrast.py` from `brand/tokens.json` (WCAG 2.1 relative luminance).",
             "Text 4.5:1, large text and controls 3:1; decor has no threshold.", "",
             "| Foreground | Background | Ratio | Needs | Result | Used for |", "|---|---|---|---|---|---|"]
    failures = 0
    for fg, bg, where, kind in PAIRS:
        r = ratio(sem[fg], sem[bg])
        need = THRESHOLD[kind]
        ok = r >= need
        failures += not ok
        lines.append(f"| {fg} `{sem[fg]}` | {bg} `{sem[bg]}` | {r:.2f}:1 | {need or '-'}{':1' if need else ''} ({kind}) | "
                     f"{'pass' if ok else '**FAIL**'} | {where} |")
    lines += ["", "## Pairs not used for text", "",
              "| Foreground | Background | Ratio | Instead |", "|---|---|---|---|"]
    for fg, bg, what in REJECTED:
        lines.append(f"| {fg} `{sem[fg]}` | {bg} `{sem[bg]}` | {ratio(sem[fg], sem[bg]):.2f}:1 | {what}: not used for text |")
    return "\n".join(lines) + "\n", failures


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    text, failures = report()
    sys.stdout.reconfigure(encoding="utf-8")
    print(text)
    if a.write:
        out = ROOT / "docs/brand/contrast_report.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print("wrote", out.relative_to(ROOT))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
