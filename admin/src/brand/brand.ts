import brand from "./brand.json";
import logos from "./logos.json";

type Logo = { file: string; label: string; widthPx: number; heightPx: number };
const logo = (logos.logos as Record<string, Logo>)[brand.logo];

/** The portal's title and logo, from brand/brand.json (copied here by scripts/brand_sync.py).
 *  Read only through components/BrandMark.tsx and the browser tab title (vite.config.ts). */
export const BRAND = {
  title: brand.title,
  /** Short form for narrow headers (approved 2026-11-13): the sidebar. */
  shortTitle: brand.shortTitle,
  logoSrc: `/brand/${logo.file}`,
  logoLabel: logo.label,
  logoWidthPx: logo.widthPx,
  logoHeightPx: logo.heightPx,
};
