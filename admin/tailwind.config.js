import { readFileSync } from "node:fs";
import { resolve } from "node:path";

/**
 * Brand theme for the admin portal. Every colour comes from the one token file
 * (brand/tokens.json, copied to src/brand/tokens.json by scripts/brand_sync.py).
 *
 * Tailwind's default palette is replaced: the class names already used in the
 * portal (gray, red, green, blue, amber, yellow, teal) now resolve to brand
 * colours, so no page needs a hard-coded colour. Text colours are mapped
 * separately so text always meets 4.5:1 (docs/brand/contrast_report.md): Red,
 * Orange, Blue and Teal are never text colours; their text shades resolve to
 * Forest Green, while backgrounds and borders keep the indicating colour.
 * Prefer the semantic `brand-*` names in new code.
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
// Derived tints for the admin's shade steps (same mixing rule as the guide's tints).
const forest85 = tint(p.forestGreen, 85);
const lightGrey40 = tint(p.lightGrey, 40);
const red40 = tint(p.red, 40);

const shades = (s) => ({ 50: s[0], 100: s[1], 200: s[2], 300: s[3], 400: s[4], 500: s[5], 600: s[6], 700: s[7], 800: s[8], 900: s[9], 950: s[9] });

const palette = {
  // 800-950 (the portal's dark buttons and chips) are the deep teal of the Teal base (white text 5.09:1).
  gray: shades([c.lightGrey20, lightGrey40, p.lightGrey, p.lightGrey, p.midGrey, c.darkGrey80, p.darkGrey, p.darkGrey, c.tealDeep, c.tealDeep]),
  red: shades([c.red10, c.red10, red40, red40, p.red, p.red, p.red, p.red, p.red, p.red]),
  green: shades([c.grassGreen10, c.grassGreen10, c.grassGreen50, c.grassGreen50, p.grassGreen, p.grassGreen, p.grassGreen, p.grassGreen, p.forestGreen, p.forestGreen]),
  blue: shades([c.blue10, c.blue10, c.blue50, c.blue50, p.blue, p.blue, p.blue, p.blue, p.blue, p.blue]),
  amber: shades([c.orange15, c.orange15, c.orange60, c.orange60, p.orange, p.orange, p.orange, p.orange, p.orange, p.orange]),
  teal: shades([c.forestGreen10, c.forestGreen10, c.teal60, c.teal60, p.teal, p.teal, p.teal, p.forestGreen, p.forestGreen, p.forestGreen]),
};
palette.yellow = palette.amber;

// Text: light shades are for dark (Forest Green) backgrounds; mid and dark shades are
// the accessible text colour for that meaning.
const textShades = (light, muted, body, strong) => shades([light, light, light, light, muted, muted, body, body, strong, strong]);
const textPalette = {
  gray: shades([p.white, p.white, c.lightGrey20, p.lightGrey, c.darkGrey80, c.darkGrey80, p.darkGrey, p.darkGrey, p.forestGreen, p.forestGreen]),
  red: textShades(p.white, sem.errorText, sem.errorText, sem.errorText),
  green: textShades(p.white, sem.successText, sem.successText, p.forestGreen),
  blue: textShades(p.white, sem.infoText, sem.infoText, sem.infoText),
  amber: textShades(p.white, sem.warningText, sem.warningText, sem.warningText),
  teal: textShades(p.white, p.forestGreen, p.forestGreen, p.forestGreen),
};
textPalette.yellow = textPalette.amber;

const base = { transparent: "transparent", current: "currentColor", white: p.white, black: p.forestGreen };
const brand = {
  forest: p.forestGreen,
  "forest-hover": forest85,
  ...Object.fromEntries(Object.entries(sem).map(([k, v]) => [k.replace(/[A-Z]/g, (m) => "-" + m.toLowerCase()), v])),
};

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    colors: { ...base, ...palette, brand },
    textColor: { ...base, ...textPalette, brand },
    // Font: the portal's original Tailwind system font stack (decision 2026-11-11).
    extend: {
      borderRadius: Object.fromEntries(Object.entries(tokens.radius).map(([k, v]) => [`brand-${k}`, `${v}px`])),
    },
  },
  plugins: [],
};
