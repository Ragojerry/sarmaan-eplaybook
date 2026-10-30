import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import { useAuth } from "../services/auth";
import { Module, TrainingVideo, VideoStatus } from "../types/api";

const STATUS_COLORS: Record<VideoStatus, string> = {
  DRAFT: "bg-gray-100 text-gray-700",
  PUBLISHED: "bg-green-100 text-green-700",
  ARCHIVED: "bg-yellow-100 text-yellow-700",
};

const MAX_MB = 500; // mirrors the server limit (MAX_VIDEO_UPLOAD_MB)

function formatSize(bytes: number | null) {
  if (bytes == null) return "—";
  return bytes >= 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

function formatDuration(s: number | null) {
  if (s == null) return "—";
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

/** Reads the clip's real length in the browser so the admin doesn't type it. */
function readDuration(file: File): Promise<number | null> {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const el = document.createElement("video");
    el.preload = "metadata";
    el.onloadedmetadata = () => {
      URL.revokeObjectURL(url);
      resolve(Number.isFinite(el.duration) ? Math.round(el.duration) : null);
    };
    el.onerror = () => {
      URL.revokeObjectURL(url);
      resolve(null);
    };
    el.src = url;
  });
}

function errorText(err: unknown, fallback: string) {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
}

/**
 * Video library management. Flow: create the record → upload the footage →
 * publish. A video cannot be published without footage, and replacing the
 * footage of a published video sends it back to Draft for re-approval.
 * Learners only ever see Published videos.
 */
export default function VideosPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const canEdit = user?.role === "CONTENT_ADMIN" || user?.role === "SUPER_ADMIN";

  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ title: "", description: "", module_id: "", required_offline: false });
  const [message, setMessage] = useState<{ kind: "error" | "info"; text: string } | null>(null);
  const [uploading, setUploading] = useState<{ id: string; pct: number } | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const uploadTarget = useRef<string | null>(null);

  const videos = useQuery<TrainingVideo[]>({
    queryKey: ["videos"],
    queryFn: async () => (await api.get("/videos")).data,
  });
  const modules = useQuery<Module[]>({
    queryKey: ["modules"],
    queryFn: async () => (await api.get("/modules")).data,
  });
  const moduleName = (id: string | null) => {
    const m = modules.data?.find((x) => x.id === id);
    return m ? `${m.module_code} · ${m.title}` : "—";
  };

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["videos"] });

  const create = useMutation({
    mutationFn: async () =>
      (
        await api.post("/videos", {
          title: form.title,
          description: form.description || null,
          module_id: form.module_id || null,
          required_offline: form.required_offline,
        })
      ).data,
    onSuccess: () => {
      setShowCreate(false);
      setForm({ title: "", description: "", module_id: "", required_offline: false });
      setMessage({ kind: "info", text: "Video created as a draft. Now upload the footage." });
      refresh();
    },
    onError: (e) => setMessage({ kind: "error", text: errorText(e, "Could not create the video.") }),
  });

  const patch = useMutation({
    mutationFn: async (v: { id: string; body: Record<string, unknown> }) =>
      (await api.patch(`/videos/${v.id}`, v.body)).data,
    onSuccess: () => {
      setMessage(null);
      refresh();
    },
    onError: (e) => setMessage({ kind: "error", text: errorText(e, "Could not update the video.") }),
  });

  async function onFileChosen(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    const id = uploadTarget.current;
    e.target.value = "";
    if (!file || !id) return;
    if (file.size > MAX_MB * 1024 * 1024) {
      setMessage({ kind: "error", text: `That file is ${formatSize(file.size)}; the limit is ${MAX_MB} MB.` });
      return;
    }
    if (!["video/mp4", "video/webm"].includes(file.type)) {
      setMessage({ kind: "error", text: "Please choose an MP4 (H.264) or WebM video." });
      return;
    }
    const wasPublished = videos.data?.find((v) => v.id === id)?.status === "PUBLISHED";
    const duration = await readDuration(file);
    const body = new FormData();
    body.append("file", file);
    if (duration != null) body.append("duration_seconds", String(duration));
    setUploading({ id, pct: 0 });
    setMessage(null);
    try {
      await api.post(`/videos/${id}/file`, body, {
        timeout: 0,
        onUploadProgress: (p) => setUploading({ id, pct: p.total ? Math.round((100 * p.loaded) / p.total) : 0 }),
      });
      setMessage({
        kind: "info",
        text: wasPublished
          ? "New footage uploaded. The video is back in Draft — publish it again once you have checked it."
          : "Footage uploaded. You can publish the video now.",
      });
      refresh();
    } catch (err) {
      setMessage({ kind: "error", text: errorText(err, "Upload failed.") });
    } finally {
      setUploading(null);
    }
  }

  function pickFile(id: string) {
    uploadTarget.current = id;
    fileInput.current?.click();
  }

  return (
    <div className="p-6">
      <input ref={fileInput} type="file" accept="video/mp4,video/webm" className="hidden" onChange={onFileChosen} />
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">Videos</h1>
        {canEdit && (
          <button onClick={() => setShowCreate((v) => !v)} className="bg-gray-900 text-white text-sm rounded px-4 py-2">
            + New video
          </button>
        )}
      </div>

      {message && (
        <p className={`text-sm mb-4 ${message.kind === "error" ? "text-red-600" : "text-green-700"}`}>{message.text}</p>
      )}

      {showCreate && canEdit && (
        <form
          className="bg-white border rounded-lg p-4 mb-6 space-y-3 text-sm"
          onSubmit={(e) => {
            e.preventDefault();
            create.mutate();
          }}
        >
          <label className="block">
            <span className="text-xs text-gray-500">Title</span>
            <input
              required
              className="mt-1 w-full border rounded px-2 py-1"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
          </label>
          <label className="block">
            <span className="text-xs text-gray-500">Description</span>
            <textarea
              className="mt-1 w-full border rounded px-2 py-1"
              rows={2}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </label>
          <label className="block">
            <span className="text-xs text-gray-500">Module</span>
            <select
              className="mt-1 w-full border rounded px-2 py-1"
              value={form.module_id}
              onChange={(e) => setForm({ ...form, module_id: e.target.value })}
            >
              <option value="">Not linked to a module</option>
              {modules.data?.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.module_code} · {m.title}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.required_offline}
              onChange={(e) => setForm({ ...form, required_offline: e.target.checked })}
            />
            <span>Required offline (every phone should download it)</span>
          </label>
          <button disabled={create.isPending} className="bg-gray-900 text-white rounded px-4 py-1.5 disabled:opacity-50">
            {create.isPending ? "Creating…" : "Create draft"}
          </button>
        </form>
      )}

      <div className="bg-white border rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs text-gray-500">
            <tr>
              <th className="px-3 py-2">Video</th>
              <th className="px-3 py-2">Module</th>
              <th className="px-3 py-2">Footage</th>
              <th className="px-3 py-2">Required offline</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2" />
            </tr>
          </thead>
          <tbody>
            {videos.isLoading && (
              <tr>
                <td colSpan={6} className="px-3 py-4 text-gray-500">
                  Loading…
                </td>
              </tr>
            )}
            {videos.data?.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-4 text-gray-500">
                  No videos yet.
                </td>
              </tr>
            )}
            {videos.data?.map((v) => (
              <tr key={v.id} className="border-t align-top">
                <td className="px-3 py-2">
                  <div className="font-medium">{v.title}</div>
                  {v.description && <div className="text-xs text-gray-500 max-w-sm">{v.description}</div>}
                </td>
                <td className="px-3 py-2 text-gray-600">{moduleName(v.module_id)}</td>
                <td className="px-3 py-2 text-gray-600 whitespace-nowrap">
                  {v.has_file ? (
                    <>
                      {formatSize(v.file_size)} · {formatDuration(v.duration_seconds)}
                    </>
                  ) : (
                    <span className="text-amber-700">No footage yet</span>
                  )}
                  {uploading?.id === v.id && (
                    <div className="mt-1 h-1.5 w-28 bg-gray-200 rounded">
                      <div className="h-1.5 bg-green-600 rounded" style={{ width: `${uploading.pct}%` }} />
                    </div>
                  )}
                </td>
                <td className="px-3 py-2">
                  <input
                    type="checkbox"
                    checked={v.required_offline}
                    disabled={!canEdit}
                    onChange={(e) => patch.mutate({ id: v.id, body: { required_offline: e.target.checked } })}
                  />
                </td>
                <td className="px-3 py-2">
                  <span className={`text-xs px-1.5 py-0.5 rounded ${STATUS_COLORS[v.status]}`}>{v.status}</span>
                </td>
                <td className="px-3 py-2 text-right whitespace-nowrap space-x-3">
                  {canEdit && (
                    <>
                      <button
                        className="text-xs underline text-gray-700 disabled:opacity-40"
                        disabled={uploading !== null}
                        onClick={() => pickFile(v.id)}
                      >
                        {v.has_file ? "Replace footage" : "Upload footage"}
                      </button>
                      {v.status !== "PUBLISHED" && (
                        <button
                          className="text-xs underline text-green-700 disabled:opacity-40"
                          disabled={!v.has_file}
                          title={v.has_file ? "" : "Upload footage first"}
                          onClick={() => patch.mutate({ id: v.id, body: { status: "PUBLISHED" } })}
                        >
                          Publish
                        </button>
                      )}
                      {v.status === "PUBLISHED" && (
                        <button
                          className="text-xs underline text-amber-700"
                          onClick={() => patch.mutate({ id: v.id, body: { status: "ARCHIVED" } })}
                        >
                          Archive
                        </button>
                      )}
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-gray-400 mt-3">
        MP4 (H.264) or WebM, up to {MAX_MB} MB. Learners only see Published videos. Phones that already downloaded a
        video keep their copy.
      </p>
    </div>
  );
}
