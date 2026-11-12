import config from "../brand/logos.json";

type Logo = { file: string; label: string; widthPx: number; heightPx: number; minWidthDp?: number; clearSpaceRatio?: number };
type Placement = { logos: "order" | string[]; rowHeightDp: number };

/**
 * The partner logos for one placement, as set in src/brand/logos.json (copied from
 * brand/logos.json by scripts/brand_sync.py). Files are shown unmodified from /brand/:
 * same aspect ratio, never larger than their own pixels, IHS never narrower than its
 * minimum width, clear space = the width of the "I" in IHS, always on white.
 */
export default function PartnerLogos({ placement }: { placement: "adminHeader" | "adminFooter" }) {
  const logos = config.logos as Record<string, Logo>;
  const place = (config.placements as Record<string, Placement>)[placement];
  if (!place) return null;
  const keys = place.logos === "order" ? (config.order as string[]) : place.logos;
  const row = place.rowHeightDp;
  const dpr = typeof window === "undefined" ? 1 : window.devicePixelRatio || 1;
  const ihs = logos.ihs;
  const clear = ihs ? (ihs.clearSpaceRatio ?? 0.165) * row * (ihs.widthPx / ihs.heightPx) : row * 0.3;

  return (
    <div className="bg-white flex flex-col items-center" style={{ padding: clear }}>
      <div className="flex flex-wrap items-center justify-center" style={{ gap: clear }}>
        {keys.map((key) => {
          const logo = logos[key];
          if (!logo) return null;
          const maxH = logo.heightPx / dpr; // never upscale the file
          let h = Math.min(row, maxH);
          if (logo.minWidthDp) h = Math.min(Math.max(h, (logo.minWidthDp * logo.heightPx) / logo.widthPx), maxH);
          return (
            <img
              key={key}
              src={`/brand/${logo.file}`}
              alt={logo.label}
              style={{ width: (h * logo.widthPx) / logo.heightPx, height: h, objectFit: "contain" }}
            />
          );
        })}
      </div>
    </div>
  );
}
