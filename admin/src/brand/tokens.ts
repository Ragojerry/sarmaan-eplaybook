// Brand colours for places Tailwind classes cannot reach (chart fills). Values come from
// tokens.json, copied from brand/tokens.json by scripts/brand_sync.py.
import tokens from "./tokens.json";

type TintSpec = [string, number];

function tint(hex: string, percent: number): string {
  const ch = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
  return (
    "#" +
    ch
      .map((v) => Math.round(v * (percent / 100) + 255 * (1 - percent / 100)).toString(16).padStart(2, "0"))
      .join("")
      .toUpperCase()
  );
}

const palette: Record<string, string> = { ...tokens.palette };
for (const [name, spec] of Object.entries(tokens.tints as unknown as Record<string, TintSpec>)) {
  palette[name] = tint(palette[spec[0]], spec[1]);
}

export const brandColor = palette;

/** Chart series colours: Forest Green first, then Grass Green 50% to tell a second series apart. */
export const chartSeries = [palette.forestGreen, palette.grassGreen50];
