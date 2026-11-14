import { useEffect, useRef, useState } from "react";
import { api } from "../services/api";
import { uploadVideoDirect } from "../services/videoUpload";
import { TrainingVideo } from "../types/api";

export type MediaKind = "AUDIO" | "VIDEO";

export const MEDIA_ACCEPT: Record<MediaKind, string> = {
  AUDIO: ".mp3,.m4a,.wav,audio/mpeg,audio/mp4,audio/wav",
  VIDEO: ".mp4,video/mp4",
};

export function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export interface SectionMediaResult {
  id: string;
  content_type: MediaKind;
  content: Record<string, unknown>;
  video_status: string | null;
}

/** Uploads (or replaces) the file of an AUDIO/VIDEO section. The server checks the
 * real file type and size; `onProgress` gets 0–100. */
export async function uploadSectionMedia(
  sectionId: string,
  file: File,
  onProgress: (pct: number) => void,
  signal?: AbortSignal,
): Promise<SectionMediaResult> {
  if (file.type.startsWith("video/")) {
    // Straight to storage when the server uses S3 (the section's video record first).
    const attached = (await api.post(`/modules/sections/${sectionId}/video`, null, { signal })).data;
    const video = await uploadVideoDirect(attached.video_id, file, onProgress, null, signal);
    if (video !== null)
      return {
        ...attached,
        content: { ...attached.content, filename: file.name, mime_type: file.type, size_bytes: video.file_size },
        video_status: video.status,
      };
  }
  const form = new FormData();
  form.append("file", file);
  const resp = await api.post(`/modules/sections/${sectionId}/media`, form, {
    signal,
    onUploadProgress: (e) => onProgress(e.total ? Math.round((e.loaded / e.total) * 100) : 0),
  });
  return resp.data;
}

export function errorText(e: any, fallback: string): string {
  if (e?.code === "ERR_CANCELED") return "Upload cancelled.";
  if (e?.response?.status === 413 && typeof e.response.data !== "object") return "The file is too large for the server.";
  return e?.response?.data?.detail ?? fallback;
}

export function ProgressBar({ pct }: { pct: number }) {
  return (
    <div className="w-full h-2 bg-gray-200 rounded" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
      <div className="h-2 bg-blue-600 rounded transition-all" style={{ width: `${pct}%` }} />
    </div>
  );
}

/** Audio or video player for a local object URL. */
export function MediaPlayer({ kind, src }: { kind: MediaKind; src: string }) {
  return kind === "AUDIO" ? (
    <audio controls src={src} className="w-full max-w-md" />
  ) : (
    <video controls src={src} className="max-w-md rounded border" />
  );
}

/** File name, size, preview, replace and remove for one AUDIO/VIDEO section. A VIDEO
 *  section can also show an existing video (a general one or one of this module's),
 *  so one upload appears in several places without a second copy. */
export default function SectionMediaField({
  sectionId,
  moduleId,
  kind,
  content,
  onChanged,
}: {
  sectionId: string;
  moduleId?: string;
  kind: MediaKind;
  content: Record<string, unknown>;
  onChanged: (content: Record<string, unknown>) => void;
}) {
  const fileId = (kind === "AUDIO" ? content.media_asset_id : content.video_id) as string | undefined;
  const filename = typeof content.filename === "string" ? content.filename : null;
  const size = typeof content.size_bytes === "number" ? content.size_bytes : null;

  const [pct, setPct] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [videoStatus, setVideoStatus] = useState<string | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [choices, setChoices] = useState<TrainingVideo[] | null>(null);
  const abort = useRef<AbortController | null>(null);
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
  }, [previewUrl]);

  useEffect(() => {
    if (kind !== "VIDEO" || !fileId) {
      setVideoUrl(null);
      return setVideoStatus(null);
    }
    api
      .get(`/videos/${fileId}`)
      .then((r) => {
        setVideoStatus(r.data.status);
        setVideoUrl(r.data.url ?? null);
      })
      .catch(() => setVideoStatus(null));
  }, [kind, fileId]);

  const showPreview = (url: string | null) => {
    setPreviewUrl((old) => {
      if (old) URL.revokeObjectURL(old);
      return url;
    });
  };

  const upload = async (file: File) => {
    setError(null);
    setPct(0);
    abort.current = new AbortController();
    try {
      const result = await uploadSectionMedia(sectionId, file, setPct, abort.current.signal);
      showPreview(URL.createObjectURL(file)); // preview straight from the chosen file, no re-download
      setVideoStatus(result.video_status);
      onChanged(result.content);
    } catch (e) {
      setError(errorText(e, "Could not upload the file."));
    } finally {
      setPct(null);
      abort.current = null;
      if (input.current) input.current.value = "";
    }
  };

  const remove = async () => {
    if (!window.confirm("Remove this file from the section? Learners will no longer see it after the next release.")) return;
    setError(null);
    try {
      const resp = await api.delete(`/modules/sections/${sectionId}/media`);
      showPreview(null);
      setVideoStatus(null);
      onChanged(resp.data.content);
    } catch (e) {
      setError(errorText(e, "Could not remove the file."));
    }
  };

  // Videos the section may show: general ones and this module's, with a file, not archived.
  const openChoices = async () => {
    setError(null);
    try {
      const all: TrainingVideo[] = (await api.get("/videos")).data;
      setChoices(all.filter((v) => v.has_file && v.status !== "ARCHIVED" && v.id !== fileId && (!v.module_id || v.module_id === moduleId)));
    } catch (e) {
      setError(errorText(e, "Could not load the videos."));
    }
  };

  const pickExisting = async (videoId: string) => {
    setError(null);
    try {
      const resp = await api.post(`/modules/sections/${sectionId}/video`, { video_id: videoId });
      showPreview(null);
      setChoices(null);
      setVideoStatus(resp.data.video_status);
      onChanged(resp.data.content);
    } catch (e) {
      setError(errorText(e, "Could not use that video."));
    }
  };

  const loadPreview = async () => {
    if (!fileId) return;
    if (kind === "VIDEO" && videoUrl) {
      showPreview(videoUrl); // straight from CloudFront (same site as this portal)
      return;
    }
    setLoadingPreview(true);
    setError(null);
    try {
      const path = kind === "AUDIO" ? `/media/${fileId}/file` : `/videos/${fileId}/file`;
      const resp = await api.get(path, { responseType: "blob" });
      showPreview(URL.createObjectURL(resp.data));
    } catch (e) {
      setError(errorText(e, "Could not load the preview."));
    } finally {
      setLoadingPreview(false);
    }
  };

  const publishVideo = async () => {
    try {
      const resp = await api.patch(`/videos/${fileId}`, { status: "PUBLISHED" });
      setVideoStatus(resp.data.status);
    } catch (e) {
      setError(errorText(e, "Could not publish the video."));
    }
  };

  const uploading = pct !== null;
  const label = kind === "AUDIO" ? "audio" : "video";

  return (
    <div className="border rounded bg-white p-2 space-y-2 text-sm">
      {fileId ? (
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <span className="font-medium">{filename ?? `${label} file`}</span>
          {size !== null && <span className="text-gray-500">{formatBytes(size)}</span>}
          {videoStatus && (
            <span
              className={`text-xs px-2 py-0.5 rounded ${
                videoStatus === "PUBLISHED" ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"
              }`}
            >
              Video {videoStatus.toLowerCase()}
            </span>
          )}
          {videoStatus === "DRAFT" && (
            <button type="button" onClick={publishVideo} className="text-xs text-blue-600 hover:underline">
              Publish video
            </button>
          )}
        </div>
      ) : (
        <p className="text-gray-500">No {label} file yet.</p>
      )}

      {videoStatus === "DRAFT" && (
        <p className="text-xs text-amber-700">Learners only see this video once it is published.</p>
      )}

      {previewUrl ? (
        <MediaPlayer kind={kind} src={previewUrl} />
      ) : (
        fileId && (
          <button type="button" onClick={loadPreview} disabled={loadingPreview} className="text-xs text-blue-600 hover:underline">
            {loadingPreview ? "Loading preview…" : "Load preview"}
          </button>
        )
      )}

      {uploading && (
        <div className="flex items-center gap-2">
          <ProgressBar pct={pct} />
          <span className="text-xs text-gray-500 w-10">{pct}%</span>
          <button type="button" onClick={() => abort.current?.abort()} className="text-xs text-gray-500">
            Cancel
          </button>
        </div>
      )}

      <div className="flex gap-3">
        <input
          ref={input}
          type="file"
          accept={MEDIA_ACCEPT[kind]}
          className="hidden"
          onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])}
        />
        <button
          type="button"
          disabled={uploading}
          onClick={() => input.current?.click()}
          className="text-xs bg-gray-900 text-white rounded px-2 py-1 disabled:opacity-50"
        >
          {fileId ? `Replace ${label}` : `Upload ${label}`}
        </button>
        {kind === "VIDEO" && (
          <button type="button" disabled={uploading} onClick={openChoices} className="text-xs text-blue-600 hover:underline disabled:opacity-50">
            Use an existing video
          </button>
        )}
        {fileId && (
          <button type="button" disabled={uploading} onClick={remove} className="text-xs text-red-500 hover:underline disabled:opacity-50">
            Remove file
          </button>
        )}
      </div>
      {choices && (
        <div className="border rounded p-2 bg-gray-50 space-y-1">
          {choices.length === 0 ? (
            <p className="text-xs text-gray-500">No other general or module videos with a file yet.</p>
          ) : (
            <select
              className="border rounded px-2 py-1 text-sm w-full"
              defaultValue=""
              onChange={(e) => e.target.value && pickExisting(e.target.value)}
            >
              <option value="">Choose a video…</option>
              {choices.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.title} {v.module_id ? "(this module)" : "(general)"} {v.file_size ? `· ${formatBytes(v.file_size)}` : ""}{" "}
                  {v.status === "DRAFT" ? "· draft" : ""}
                </option>
              ))}
            </select>
          )}
          <p className="text-xs text-gray-500">
            The same file is shown here and wherever else it is used: phones download it once. Videos of other modules are not offered,
            because learners who cannot see that module would not get them.
          </p>
          <button type="button" onClick={() => setChoices(null)} className="text-xs text-gray-500 hover:underline">
            Cancel
          </button>
        </div>
      )}
      {kind === "VIDEO" && fileId && (
        <p className="text-xs text-gray-400">Replacing the file changes it everywhere this video is shown.</p>
      )}
      <p className="text-xs text-gray-400">
        {kind === "AUDIO" ? "MP3, M4A or WAV." : "MP4 (H.264)."} The server checks the real file type and the size limit.
      </p>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
