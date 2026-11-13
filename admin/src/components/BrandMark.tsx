import { BRAND } from "../brand/brand";

/** The app logo (on its own white card, never enlarged past the file's pixels) and the
 *  title, which wraps instead of being cut off. `size` is the logo height in pixels. */
export default function BrandMark({
  size = 40,
  subtitle,
  className = "",
  heading = false,
  short = false,
}: {
  size?: number;
  subtitle?: string;
  className?: string;
  /** Render the title as the page heading (h1), e.g. on the sign-in page. */
  heading?: boolean;
  /** The short title, for narrow headers such as the sidebar. */
  short?: boolean;
}) {
  const Title = heading ? "h1" : "div";
  const height = Math.min(size, BRAND.logoHeightPx);
  return (
    <div className={className}>
      <span className="inline-block bg-paper rounded-md px-2 py-1 mb-2">
        <img src={BRAND.logoSrc} alt={BRAND.logoLabel} height={height} width={Math.round((height * BRAND.logoWidthPx) / BRAND.logoHeightPx)} />
      </span>
      <Title className="font-semibold leading-snug break-words">{short ? BRAND.shortTitle : BRAND.title}</Title>
      {subtitle && <div className="text-sm opacity-80">{subtitle}</div>}
    </div>
  );
}
