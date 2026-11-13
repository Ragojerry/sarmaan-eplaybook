import { readFileSync } from "node:fs";
import { resolve } from "node:path";

/**
 * Brand theme for the admin portal. Every colour comes from the one token file
 * (brand/tokens.json, copied to src/brand/tokens.json by scripts/brand_sync.py).
 *
 * Tailwind's default palette is replaced: the class names already used in the
 * portal (gray, red, green, blue, amber, yellow, teal) now resolve to the palette
 * of 2026-11-12, so no page needs a hard-coded colour. `bg-white` is the card
 * colour and `bg-gray-50` the 15% teal page; `bg-paper` (pure white) is only for
 * the partner logos. Text colours are mapped separately so text always meets 4.5:1
 * (docs/brand/contrast_report.md): no light grey text, and warning text is ink
 * (the warning orange is a border, fill or icon). Prefer the semantic `brand-*`
 * names in new code.
 */
const tokens = JSON.parse(readFileSync(resolve(process.cwd(), "src/brand/tokens.json"), "utf8"));

const tint = (hex, percent) =>
  "#" +
  [1, 3, 5]
    .map((i) => Math.round(parseInt(hex.slice(i, i + 2), 16) * (percent / 100) + 255 * (1 - percent / 100)))
    .map((v) => v.toString(16).padStart(2, "0"))
    .join("")
    .toUpperCase();

const p = Object.fromEntries(Object.entries(tokens.palette).map(([k, v]) => [k, v.toUpperCase()]));
const c = { ...p };
for (const [name, [base, percent]] of Object.entries(tokens.tints)) c[name] = tint(p[base], percent);
for (const [name, blend] of Object.entries(tokens.blends ?? {})) if (!name.startsWith("_")) c[name] = blend.hex.toUpperCase();
const sem = Object.fromEntries(Object.entries(tokens.semantic).map(([k, v]) => [k, c[v]]));
// Light borders for coloured callouts (same mixing rule as the token tints).
const errorRed40 = tint(p.errorRed, 40);
const forest40 = tint(p.forestGreen, 40);
const warningOrange40 = tint(p.warningOrange, 40);

const shades = (s) => ({ 50: s[0], 100: s[1], 200: s[2], 300: s[3], 400: s[4], 500: s[5], 600: s[6], 700: s[7], 800: s[8], 900: s[9], 950: s[9] });

const palette = {
  // 50 the page, 100 pale teal panels, 200-300 the thin teal border; 800-950 (the portal's
  // primary buttons and chips) logo teal with white text (6.70:1).
  gray: shades([c.tealMist, c.paleTeal, c.border, c.border, c.inkMuted, c.inkMuted, c.inkMuted, c.ink, c.teal, c.teal]),
  red: shades([c.errorRed10, c.errorRed10, errorRed40, errorRed40, p.errorRed, p.errorRed, p.errorRed, p.errorRed, p.errorRed, p.errorRed]),
  green: shades([c.forestGreen10, c.forestGreen10, forest40, forest40, p.forestGreen, p.forestGreen, p.forestGreen, p.forestGreen, p.deepForest, p.deepForest]),
  blue: shades([c.paleTeal, c.paleTeal, c.border, c.border, p.teal, p.teal, p.teal, p.teal, p.teal, p.teal]),
  amber: shades([c.warningOrange10, c.warningOrange10, warningOrange40, warningOrange40, p.warningOrange, p.warningOrange, p.warningOrange, p.warningOrange, p.warningOrange, p.warningOrange]),
  teal: shades([c.paleTeal, c.paleTeal, c.border, c.border, p.teal, p.teal, p.teal, p.teal, p.forestGreen, p.forestGreen]),
};
palette.yellow = palette.amber;

// Text: light shades are for dark (forest, teal) backgrounds; mid and dark shades are
// the accessible text colour for that meaning.
const textShades = (light, muted, body, strong) => shades([light, light, light, light, muted, muted, body, body, strong, strong]);
const textPalette = {
  gray: shades([p.white, p.white, p.tealMist, p.tealMist, p.inkMuted, p.inkMuted, p.inkMuted, p.ink, p.ink, p.ink]),
  red: textShades(p.white, sem.errorText, sem.errorText, sem.errorText),
  green: textShades(p.white, sem.successText, sem.successText, p.forestGreen),
  blue: textShades(p.white, p.teal, p.teal, p.teal),
  amber: textShades(p.white, sem.warningText, sem.warningText, sem.warningText),
  teal: textShades(p.white, p.teal, p.teal, p.forestGreen),
};
textPalette.yellow = textPalette.amber;

const base = { transparent: "transparent", current: "currentColor", white: p.card, paper: p.white, black: p.ink };
const textBase = { ...base, white: p.white };
const brand = {
  forest: p.forestGreen,
  "forest-hover": p.deepForest,
  ...Object.fromEntries(Object.entries(sem).map(([k, v]) => [k.replace(/[A-Z]/g, (m) => "-" + m.toLowerCase()), v])),
};

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    colors: { ...base, ...palette, brand },
    textColor: { ...textBase, ...textPalette, brand },
    // Font: the portal's original Tailwind system font stack (decision 2026-11-11).
    extend: {
      borderRadius: Object.fromEntries(Object.entries(tokens.radius).map(([k, v]) => [`brand-${k}`, `${v}px`])),
    },
  },
  plugins: [],
};
