import { useState, useEffect } from "react";
import { api } from "../services/api";

/**
 * A plain `<img src="...">` can't attach the Authorization header our
 * /media/{id}/file endpoint requires (media is deliberately not public —
 * training content shouldn't be servable to anyone with a guessed URL).
 * This fetches the bytes through the authenticated axios client instead and
 * renders them as a local object URL.
 */
export default function AuthenticatedImage({
  mediaAssetId,
  alt,
  className,
}: {
  mediaAssetId: string;
  alt: string;
  className?: string;
}) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let currentUrl: string | null = null;
    let cancelled = false;

    api
      .get(`/media/${mediaAssetId}/file`, { responseType: "blob" })
      .then((resp) => {
        if (cancelled) return;
        currentUrl = URL.createObjectURL(resp.data);
        setObjectUrl(currentUrl);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });

    return () => {
      cancelled = true;
      if (currentUrl) URL.revokeObjectURL(currentUrl);
    };
  }, [mediaAssetId]);

  if (failed) {
    return <p className="text-xs text-red-500">Image failed to load.</p>;
  }
  if (!objectUrl) {
    return <div className={`bg-gray-100 animate-pulse ${className ?? "w-48 h-32"}`} />;
  }
  return <img src={objectUrl} alt={alt} className={className} />;
}
