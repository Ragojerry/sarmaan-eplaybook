import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import { useAuth } from "../services/auth";
import { FaqEntry, FaqStatus, Module } from "../types/api";

const STATUS_COLORS: Record<FaqStatus, string> = {
  DRAFT: "bg-gray-100 text-gray-700",
  APPROVED: "bg-green-100 text-green-700",
  ARCHIVED: "bg-yellow-100 text-yellow-700",
};
const APPROVER_ROLES = ["CONTENT_ADMIN", "PROGRAM_REVIEWER", "TECHNICAL_REVIEWER", "SUPER_ADMIN"];
const EMPTY = { question: "", alternates: "", answer: "", module_id: "", source_question: "" };

function errorText(err: unknown, fallback: string) {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
}

function sentenceCase(s: string) {
  const t = s.trim();
  return t ? t[0].toUpperCase() + t.slice(1) : t;
}

/**
 * Curated answers: trainers answer the questions learners actually ask (the
 * unanswered ones on the Analytics page link here). Approved answers are
 * checked before the training passages — online at once, and offline once
 * phones have the next release or content sync.
 */
export default function AnswersPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [params, setParams] = useSearchParams();
  const canEdit = user?.role === "CONTENT_ADMIN" || user?.role === "SUPER_ADMIN";
  const canApprove = !!user && APPROVER_ROLES.includes(user.role);

  const [form, setForm] = useState(EMPTY);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [filter, setFilter] = useState<FaqStatus | "">("");
  const [message, setMessage] = useState<{ kind: "error" | "info"; text: string } | null>(null);

  // "Answer this" on the Analytics page opens the form with the question filled in.
  useEffect(() => {
    const asked = params.get("question");
    if (asked && canEdit) {
      setForm({ ...EMPTY, question: sentenceCase(asked), source_question: asked });
      setEditingId(null);
      setShowForm(true);
      setParams({}, { replace: true });
    }
  }, [params, canEdit, setParams]);

  const faqs = useQuery<FaqEntry[]>({
    queryKey: ["faqs", filter],
    queryFn: async () => (await api.get("/faqs", { params: filter ? { status: filter } : {} })).data,
  });
  const modules = useQuery<Module[]>({
    queryKey: ["modules"],
    queryFn: async () => (await api.get("/modules")).data,
  });

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["faqs"] });
  const close = () => {
    setShowForm(false);
    setEditingId(null);
    setForm(EMPTY);
  };

  const save = useMutation({
    mutationFn: async () => {
      const body = {
        question: form.question,
        alternates: form.alternates || null,
        answer: form.answer,
        module_id: form.module_id,
      };
      return editingId
        ? (await api.patch(`/faqs/${editingId}`, body)).data
        : (await api.post("/faqs", { ...body, source_question: form.source_question || null })).data;
    },
    onSuccess: (f: FaqEntry) => {
      setMessage({
        kind: "info",
        text:
          f.status === "DRAFT"
            ? "Saved as a draft. A reviewer must approve it before the assistant uses it."
            : "Saved.",
      });
      close();
      refresh();
    },
    onError: (e) => setMessage({ kind: "error", text: errorText(e, "Could not save the answer.") }),
  });

  const patch = useMutation({
    mutationFn: async (v: { id: string; status: FaqStatus }) =>
      (await api.patch(`/faqs/${v.id}`, { status: v.status })).data,
    onSuccess: (_d, v) => {
      setMessage(
        v.status === "APPROVED"
          ? {
              kind: "info",
              text: "Approved. Users who are online get this answer now; phones offline get it with the next release.",
            }
          : null,
      );
      refresh();
    },
    onError: (e) => setMessage({ kind: "error", text: errorText(e, "Could not update the answer.") }),
  });

  const remove = useMutation({
    mutationFn: async (id: string) => api.delete(`/faqs/${id}`),
    onSuccess: refresh,
    onError: (e) => setMessage({ kind: "error", text: errorText(e, "Could not delete the answer.") }),
  });

  function edit(f: FaqEntry) {
    setForm({
      question: f.question,
      alternates: f.alternates ?? "",
      answer: f.answer,
      module_id: f.module_id,
      source_question: f.source_question ?? "",
    });
    setEditingId(f.id);
    setShowForm(true);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const editingApproved = editingId !== null && faqs.data?.find((f) => f.id === editingId)?.status === "APPROVED";

  return (
    <div className="p-6">
      <div className="flex items-start justify-between mb-6 gap-4">
        <div>
          <h1 className="text-xl font-semibold">Curated answers</h1>
          <p className="text-sm text-gray-500 mt-1 max-w-2xl">
            Answers written by trainers for questions learners ask. The Ask assistant checks approved answers first, on
            the server and on phones. Find unanswered questions on the Analytics page and click “Answer this”.
          </p>
        </div>
        {canEdit && !showForm && (
          <button onClick={() => setShowForm(true)} className="bg-gray-900 text-white text-sm rounded px-4 py-2 shrink-0">
            + New answer
          </button>
        )}
      </div>

      {message && (
        <p className={`text-sm mb-4 ${message.kind === "error" ? "text-red-600" : "text-green-700"}`}>{message.text}</p>
      )}

      {showForm && canEdit && (
        <form
          className="bg-white border rounded-lg p-4 mb-6 space-y-3 text-sm max-w-2xl"
          onSubmit={(e) => {
            e.preventDefault();
            save.mutate();
          }}
        >
          {form.source_question && (
            <p className="text-xs text-gray-500">
              Asked by learners: <span className="italic">“{form.source_question}”</span>
            </p>
          )}
          <label className="block">
            <span className="text-xs text-gray-500">Question</span>
            <input
              required
              minLength={3}
              maxLength={500}
              className="mt-1 w-full border rounded px-2 py-1"
              value={form.question}
              onChange={(e) => setForm({ ...form, question: e.target.value })}
            />
          </label>
          <label className="block">
            <span className="text-xs text-gray-500">
              Other ways people ask it (optional, one per line), e.g. local words for the same thing
            </span>
            <textarea
              className="mt-1 w-full border rounded px-2 py-1"
              rows={3}
              value={form.alternates}
              onChange={(e) => setForm({ ...form, alternates: e.target.value })}
            />
          </label>
          <label className="block">
            <span className="text-xs text-gray-500">Answer (shown to CDDs word for word; keep it short and exact)</span>
            <textarea
              required
              minLength={3}
              maxLength={5000}
              className="mt-1 w-full border rounded px-2 py-1"
              rows={4}
              value={form.answer}
              onChange={(e) => setForm({ ...form, answer: e.target.value })}
            />
          </label>
          <label className="block">
            <span className="text-xs text-gray-500">Module (cited as the source, and shipped with it)</span>
            <select
              required
              className="mt-1 w-full border rounded px-2 py-1"
              value={form.module_id}
              onChange={(e) => setForm({ ...form, module_id: e.target.value })}
            >
              <option value="">Choose a module…</option>
              {modules.data?.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.module_code} · {m.title}
                </option>
              ))}
            </select>
          </label>
          {editingApproved && (
            <p className="text-xs text-amber-700">
              This answer is approved. Saving changes sends it back to Draft until a reviewer approves it again.
            </p>
          )}
          <p className="text-xs text-gray-400">
            Numbers must match exactly: an answer for “8 month old” is never used for “3 month old”. Write one answer per
            age group.
          </p>
          <div className="space-x-2">
            <button disabled={save.isPending} className="bg-gray-900 text-white rounded px-4 py-1.5 disabled:opacity-50">
              {save.isPending ? "Saving…" : editingId ? "Save changes" : "Save as draft"}
            </button>
            <button type="button" onClick={close} className="text-gray-600 underline px-2">
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="mb-3 text-sm">
        <label>
          <span className="text-xs text-gray-500 mr-2">Show</span>
          <select className="border rounded px-2 py-1" value={filter} onChange={(e) => setFilter(e.target.value as FaqStatus | "")}>
            <option value="">All</option>
            <option value="DRAFT">Drafts (to review)</option>
            <option value="APPROVED">Approved</option>
            <option value="ARCHIVED">Archived</option>
          </select>
        </label>
      </div>

      <div className="bg-white border rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs text-gray-500">
            <tr>
              <th className="px-3 py-2">Question</th>
              <th className="px-3 py-2">Answer</th>
              <th className="px-3 py-2">Module</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2" />
            </tr>
          </thead>
          <tbody>
            {faqs.isLoading && (
              <tr>
                <td colSpan={5} className="px-3 py-4 text-gray-500">
                  Loading…
                </td>
              </tr>
            )}
            {faqs.data?.length === 0 && (
              <tr>
                <td colSpan={5} className="px-3 py-4 text-gray-500">
                  No answers here yet.
                </td>
              </tr>
            )}
            {faqs.data?.map((f) => (
              <tr key={f.id} className="border-t align-top">
                <td className="px-3 py-2 max-w-xs">
                  <div className="font-medium">{f.question}</div>
                  {f.alternates && (
                    <div className="text-xs text-gray-500 whitespace-pre-line mt-1">{f.alternates}</div>
                  )}
                </td>
                <td className="px-3 py-2 max-w-md text-gray-700">{f.answer}</td>
                <td className="px-3 py-2 text-gray-600 whitespace-nowrap">{f.module_code}</td>
                <td className="px-3 py-2">
                  <span className={`text-xs px-1.5 py-0.5 rounded ${STATUS_COLORS[f.status]}`}>{f.status}</span>
                </td>
                <td className="px-3 py-2 text-right whitespace-nowrap space-x-3">
                  {canEdit && (
                    <button className="text-xs underline text-gray-700" onClick={() => edit(f)}>
                      Edit
                    </button>
                  )}
                  {canApprove && f.status !== "APPROVED" && (
                    <button
                      className="text-xs underline text-green-700"
                      onClick={() => patch.mutate({ id: f.id, status: "APPROVED" })}
                    >
                      Approve
                    </button>
                  )}
                  {canApprove && f.status === "APPROVED" && (
                    <button
                      className="text-xs underline text-amber-700"
                      onClick={() => patch.mutate({ id: f.id, status: "ARCHIVED" })}
                    >
                      Archive
                    </button>
                  )}
                  {canEdit && f.status !== "APPROVED" && (
                    <button
                      className="text-xs underline text-red-700"
                      onClick={() => {
                        if (window.confirm("Delete this answer? This cannot be undone.")) remove.mutate(f.id);
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
    </div>
  );
}
