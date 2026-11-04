import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import { useAuth } from "../services/auth";
import { ReferenceDocument, ReferencePassage, ReferenceStatus } from "../types/api";

const STATUS_COLORS: Record<ReferenceStatus, string> = {
  DRAFT: "bg-gray-100 text-gray-700",
  APPROVED: "bg-green-100 text-green-700",
  ARCHIVED: "bg-yellow-100 text-yellow-700",
};

const MAX_MB = 10; // mirrors the server limit (MAX_REFERENCE_UPLOAD_MB)
const ACCEPT = ".pdf,.docx,.txt,.md,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain,text/markdown";
const APPROVER_ROLES = ["CONTENT_ADMIN", "PROGRAM_REVIEWER", "TECHNICAL_REVIEWER", "SUPER_ADMIN"];

function formatSize(bytes: number) {
  return bytes >= 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

function errorText(err: unknown, fallback: string) {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
}

/**
 * Reference library: documents outside the training modules (guidelines,
 * SOPs, job aids) that the online Ask assistant may quote. Flow: upload →
 * check the extracted text → approve. Only Approved documents are searched,
 * and only when the training modules have no answer.
 */
export default function ReferencesPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const canEdit = user?.role === "CONTENT_ADMIN" || user?.role === "SUPER_ADMIN";
  const canApprove = !!user && APPROVER_ROLES.includes(user.role);

  const [form, setForm] = useState({ title: "", description: "" });
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<{ kind: "error" | "info"; text: string } | null>(null);
  const [previewId, setPreviewId] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  const docs = useQuery<ReferenceDocument[]>({
    queryKey: ["references"],
    queryFn: async () => (await api.get("/references")).data,
  });
  const passages = useQuery<ReferencePassage[]>({
    queryKey: ["references", previewId, "passages"],
    queryFn: async () => (await api.get(`/references/${previewId}/passages`)).data,
    enabled: previewId !== null,
  });

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["references"] });

  const patch = useMutation({
    mutationFn: async (v: { id: string; body: Record<string, unknown> }) =>
      (await api.patch(`/references/${v.id}`, v.body)).data,
    onSuccess: (_d, v) => {
      setMessage(
        v.body.status === "APPROVED"
          ? { kind: "info", text: "Approved. The Ask assistant can now quote this document to users who are online." }
          : null,
      );
      refresh();
    },
    onError: (e) => setMessage({ kind: "error", text: errorText(e, "Could not update the document.") }),
  });

  const remove = useMutation({
    mutationFn: async (id: string) => api.delete(`/references/${id}`),
    onSuccess: (_d, id) => {
      if (previewId === id) setPreviewId(null);
      refresh();
    },
    onError: (e) => setMessage({ kind: "error", text: errorText(e, "Could not delete the document.") }),
  });

  async function upload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    if (file.size > MAX_MB * 1024 * 1024) {
      setMessage({ kind: "error", text: `That file is ${formatSize(file.size)}; the limit is ${MAX_MB} MB.` });
      return;
    }
    const body = new FormData();
    body.append("file", file);
    body.append("title", form.title);
    if (form.description) body.append("description", form.description);
    setUploading(true);
    setMessage(null);
    try {
      const doc: ReferenceDocument = (await api.post("/references", body, { timeout: 0 })).data;
      setForm({ title: "", description: "" });
      setFile(null);
      if (fileInput.current) fileInput.current.value = "";
      setPreviewId(doc.id);
      setMessage({
        kind: "info",
        text: `Uploaded as a draft (${doc.passage_count} passages). Check the extracted text below, then approve it.`,
      });
      refresh();
    } catch (err) {
      setMessage({ kind: "error", text: errorText(err, "Upload failed.") });
    } finally {
      setUploading(false);
    }
  }

  async function download(doc: ReferenceDocument) {
    try {
      const resp = await api.get(`/references/${doc.id}/file`, { responseType: "blob" });
      const url = URL.createObjectURL(resp.data as Blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = doc.filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setMessage({ kind: "error", text: errorText(err, "Download failed.") });
    }
  }

  const preview = docs.data?.find((d) => d.id === previewId);

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-xl font-semibold">Reference library</h1>
        <p className="text-sm text-gray-500 mt-1 max-w-2xl">
          Guidelines, SOPs and job aids beyond the training modules. When a user is online, the Ask assistant can quote
          approved documents, labelled “Reference”, when the training modules have no answer to the question. Reference
          documents are not downloaded to phones.
        </p>
      </div>

      {message && (
        <p className={`text-sm mb-4 ${message.kind === "error" ? "text-red-600" : "text-green-700"}`}>{message.text}</p>
      )}

      {canEdit && (
        <form className="bg-white border rounded-lg p-4 mb-6 space-y-3 text-sm max-w-2xl" onSubmit={upload}>
          <label className="block">
            <span className="text-xs text-gray-500">Title (shown to users as the source)</span>
            <input
              required
              maxLength={255}
              className="mt-1 w-full border rounded px-2 py-1"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
          </label>
          <label className="block">
            <span className="text-xs text-gray-500">Description (optional, admins only)</span>
            <textarea
              className="mt-1 w-full border rounded px-2 py-1"
              rows={2}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </label>
          <label className="block">
            <span className="text-xs text-gray-500">File: PDF, Word (.docx) or text, up to {MAX_MB} MB</span>
            <input
              ref={fileInput}
              required
              type="file"
              accept={ACCEPT}
              className="mt-1 block"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </label>
          <button disabled={uploading || !file} className="bg-gray-900 text-white rounded px-4 py-1.5 disabled:opacity-50">
            {uploading ? "Uploading…" : "Upload as draft"}
          </button>
          <p className="text-xs text-gray-400">
            Scanned PDFs (pictures of pages) have no text to read and will be rejected.
          </p>
        </form>
      )}

      <div className="bg-white border rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs text-gray-500">
            <tr>
              <th className="px-3 py-2">Document</th>
              <th className="px-3 py-2">File</th>
              <th className="px-3 py-2">Passages</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2" />
            </tr>
          </thead>
          <tbody>
            {docs.isLoading && (
              <tr>
                <td colSpan={5} className="px-3 py-4 text-gray-500">
                  Loading…
                </td>
              </tr>
            )}
            {docs.data?.length === 0 && (
              <tr>
                <td colSpan={5} className="px-3 py-4 text-gray-500">
                  No reference documents yet.
                </td>
              </tr>
            )}
            {docs.data?.map((d) => (
              <tr key={d.id} className={`border-t align-top ${previewId === d.id ? "bg-blue-50" : ""}`}>
                <td className="px-3 py-2">
                  <div className="font-medium">{d.title}</div>
                  {d.description && <div className="text-xs text-gray-500 max-w-sm">{d.description}</div>}
                </td>
                <td className="px-3 py-2 text-gray-600 whitespace-nowrap">
                  <button className="underline" onClick={() => download(d)}>
                    {d.filename}
                  </button>
                  <div className="text-xs text-gray-400">{formatSize(d.file_size)}</div>
                </td>
                <td className="px-3 py-2 text-gray-600">{d.passage_count}</td>
                <td className="px-3 py-2">
                  <span className={`text-xs px-1.5 py-0.5 rounded ${STATUS_COLORS[d.status]}`}>{d.status}</span>
                  {d.approved_at && d.status === "APPROVED" && (
                    <div className="text-xs text-gray-400 mt-1">{new Date(d.approved_at).toLocaleDateString()}</div>
                  )}
                </td>
                <td className="px-3 py-2 text-right whitespace-nowrap space-x-3">
                  <button className="text-xs underline text-gray-700" onClick={() => setPreviewId(previewId === d.id ? null : d.id)}>
                    {previewId === d.id ? "Hide text" : "Check text"}
                  </button>
                  {canApprove && d.status !== "APPROVED" && (
                    <button
                      className="text-xs underline text-green-700"
                      onClick={() => patch.mutate({ id: d.id, body: { status: "APPROVED" } })}
                    >
                      Approve
                    </button>
                  )}
                  {canApprove && d.status === "APPROVED" && (
                    <button
                      className="text-xs underline text-amber-700"
                      onClick={() => patch.mutate({ id: d.id, body: { status: "ARCHIVED" } })}
                    >
                      Archive
                    </button>
                  )}
                  {canEdit && d.status !== "APPROVED" && (
                    <button
                      className="text-xs underline text-red-700"
                      onClick={() => {
                        if (window.confirm(`Delete “${d.title}”? This cannot be undone.`)) remove.mutate(d.id);
                      }}
                    >
                      Delete
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {preview && (
        <div className="bg-white border rounded-lg p-4 mt-6">
          <h2 className="font-semibold text-sm">Extracted text: {preview.title}</h2>
          <p className="text-xs text-gray-500 mb-3">
            This is exactly what the assistant searches and quotes. If words are missing or jumbled (common with
            multi-column PDFs), fix the source file and upload it again before approving.
          </p>
          {passages.isLoading && <p className="text-sm text-gray-500">Loading…</p>}
          <div className="space-y-3 max-h-[32rem] overflow-y-auto">
            {passages.data?.map((p) => (
              <div key={p.position} className="text-sm">
                {p.heading && <div className="text-xs font-semibold text-gray-500">{p.heading}</div>}
                <p className="text-gray-800 whitespace-pre-wrap">{p.text}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
