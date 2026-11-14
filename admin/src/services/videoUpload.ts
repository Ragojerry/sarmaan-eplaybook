import axios from "axios";
import { api } from "./api";

/** A video as GET /videos/{id} returns it (the fields the upload screens use). */
export interface UploadedVideo {
  id: string;
  status: string;
  file_size: number | null;
  checksum: string | null;
  version: number;
  has_file: boolean;
}

export async function sha256Hex(file: Blob): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
  return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, "0")).join("");
}

/** Uploads a video file straight to storage (S3 behind CloudFront), so the bytes
 *  never pass through the API: ask for a signed PUT carrying the file's SHA-256
 *  (S3 refuses any other bytes), send the file, then let the server check what S3
 *  holds. Returns null when this server keeps videos on its own disk
 *  (development): the caller then uses the older upload. `onProgress` gets 0-100. */
export async function uploadVideoDirect(
  videoId: string,
  file: File,
  onProgress: (pct: number) => void,
  durationSeconds?: number | null,
  signal?: AbortSignal,
): Promise<UploadedVideo | null> {
  onProgress(0);
  const sha256 = await sha256Hex(file);
  let target: { url: string; method: string; headers: Record<string, string>; key: string };
  try {
    target = (
      await api.post(`/videos/${videoId}/upload-url`, { mime_type: file.type, size_bytes: file.size, sha256, filename: file.name }, { signal })
    ).data;
  } catch (e) {
    if (axios.isAxiosError(e) && e.response?.status === 409) return null;
    throw e;
  }
  // A plain axios call: the signed URL must not get the API's Authorization header.
  await axios.put(target.url, file, {
    headers: target.headers,
    signal,
    timeout: 0,
    onUploadProgress: (p) => onProgress(p.total ? Math.round((99 * p.loaded) / p.total) : 0),
  });
  const done = (
    await api.post(`/videos/${videoId}/upload-complete`, { key: target.key, duration_seconds: durationSeconds ?? null }, { signal })
  ).data as UploadedVideo;
  onProgress(100);
  return done;
}
