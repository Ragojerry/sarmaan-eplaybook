import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import AuthenticatedImage from "../components/AuthenticatedImage";
import { MediaItem, Module, QuestionType, QuestionUsage, QuizQuestionRow, QuizSummaryRow } from "../types/api";

const TYPE_LABELS: Record<QuestionType, string> = {
  MULTIPLE_CHOICE: "Multiple choice",
  TRUE_FALSE: "True or false",
  MULTIPLE_SELECT: "Multiple select",
  MATCHING: "Matching pairs",
  ORDERING: "Ordering / sequencing",
  IMAGE_CHOICE: "Image based",
  NUMERIC: "Numeric answer",
};

const USAGE_LABELS: Record<QuestionUsage, string> = {
  BOTH: "Pre-test and post-test",
  PRE: "Pre-test only",
  POST: "Post-test only",
};

interface Draft {
  type: QuestionType;
  usage: QuestionUsage;
  prompt: string;
  explanation: string;
  options: string[];
  correctIndex: number;
  correctSet: number[];
  trueFalse: boolean;
  pairs: { left: string; right: string }[];
  items: string[];
  numeric: string;
  tolerance: string;
  unit: string;
  mediaId: string;
}

const blank = (type: QuestionType): Draft => ({
  type,
  prompt: "",
  explanation: "",
  options: ["", ""],
  correctIndex: 0,
  correctSet: [],
  trueFalse: true,
  pairs: [
    { left: "", right: "" },
    { left: "", right: "" },
  ],
  items: ["", "", ""],
  numeric: "",
  tolerance: "0",
  unit: "",
  mediaId: "",
  usage: "BOTH",
});

function toDraft(q: QuizQuestionRow): Draft {
  const c = q.content as Record<string, unknown>;
  const d = blank(q.question_type);
  d.prompt = q.prompt;
  d.explanation = q.explanation ?? "";
  d.usage = q.usage ?? "BOTH";
  if (Array.isArray(c.options)) d.options = (c.options as unknown[]).map(String);
  if (typeof c.correct === "number" && q.question_type !== "NUMERIC") d.correctIndex = c.correct;
  if (Array.isArray(c.correct)) d.correctSet = (c.correct as number[]).slice();
  if (typeof c.correct === "boolean") d.trueFalse = c.correct;
  if (Array.isArray(c.pairs)) d.pairs = (c.pairs as { left: string; right: string }[]).map((p) => ({ left: p.left, right: p.right }));
  if (Array.isArray(c.items)) d.items = (c.items as unknown[]).map(String);
  if (q.question_type === "NUMERIC") {
    d.numeric = String(c.correct ?? "");
    d.tolerance = String(c.tolerance ?? 0);
    d.unit = typeof c.unit === "string" ? c.unit : "";
  }
  if (typeof c.media_asset_id === "string") d.mediaId = c.media_asset_id;
  return d;
}

function toContent(d: Draft): Record<string, unknown> {
  switch (d.type) {
    case "MULTIPLE_CHOICE":
      return { options: d.options, correct: d.correctIndex };
    case "IMAGE_CHOICE":
      return { media_asset_id: d.mediaId, options: d.options, correct: d.correctIndex };
    case "TRUE_FALSE":
      return { correct: d.trueFalse };
    case "MULTIPLE_SELECT":
      return { options: d.options, correct: d.correctSet };
    case "MATCHING":
      return { pairs: d.pairs };
    case "ORDERING":
      return { items: d.items };
    case "NUMERIC":
      return { correct: Number(d.numeric), tolerance: Number(d.tolerance || 0), ...(d.unit ? { unit: d.unit } : {}) };
  }
}

function summarize(q: QuizQuestionRow): string {
  const c = q.content as Record<string, unknown>;
  const opts = (c.options as string[] | undefined) ?? [];
  switch (q.question_type) {
    case "MULTIPLE_CHOICE":
    case "IMAGE_CHOICE":
      return `Answer: ${opts[c.correct as number] ?? "?"}`;
    case "TRUE_FALSE":
      return `Answer: ${c.correct ? "True" : "False"}`;
    case "MULTIPLE_SELECT":
      return `Answers: ${((c.correct as number[]) ?? []).map((i) => opts[i]).join(" · ")}`;
    case "MATCHING":
      return ((c.pairs as { left: string; right: string }[]) ?? []).map((p) => `${p.left} → ${p.right}`).join(" · ");
    case "ORDERING":
      return `Order: ${((c.items as string[]) ?? []).join(" → ")}`;
    case "NUMERIC":
      return `Answer: ${c.correct}${c.unit ? " " + c.unit : ""}${Number(c.tolerance) ? ` (± ${c.tolerance})` : ""}`;
  }
}

function errorText(err: unknown, fallback: string) {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join("; ") || fallback;
  return fallback;
}

/** Per-module quiz authoring. Learners pass at 90%; changes ship with the next published release. */
export default function QuizEditorPage() {
  const { moduleId } = useParams<{ moduleId: string }>();
  const queryClient = useQueryClient();
  // An archive since 2026-11: the per-module pre/post tests were retired and their
  // questions archived, so nothing is added or changed here (the server refuses it too).
  const canEdit = false;
  const [draft, setDraft] = useState<Draft | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [message, setMessage] = useState<{ kind: "error" | "info"; text: string } | null>(null);

  const module = useQuery<Module>({ queryKey: ["module", moduleId], queryFn: async () => (await api.get(`/modules/${moduleId}`)).data });
  const questions = useQuery<QuizQuestionRow[]>({
    queryKey: ["quiz", moduleId],
    queryFn: async () => (await api.get(`/quiz/modules/${moduleId}/questions`)).data,
  });
  const summary = useQuery<QuizSummaryRow>({
    queryKey: ["quiz-summary", moduleId],
    queryFn: async () => (await api.get(`/quiz/modules/${moduleId}/summary`)).data,
  });
  const media = useQuery<MediaItem[]>({
    queryKey: ["media-images"],
    queryFn: async () => (await api.get("/media", { params: { asset_type: "IMAGE" } })).data,
    enabled: draft?.type === "IMAGE_CHOICE",
  });

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["quiz", moduleId] });
    queryClient.invalidateQueries({ queryKey: ["quiz-summary", moduleId] });
  };

  const save = useMutation({
    mutationFn: async (d: Draft) => {
      const body = { prompt: d.prompt, explanation: d.explanation || null, content: toContent(d), usage: d.usage };
      if (editingId) return (await api.patch(`/quiz/questions/${editingId}`, body)).data;
      return (await api.post(`/quiz/modules/${moduleId}/questions`, { ...body, question_type: d.type })).data;
    },
    onSuccess: () => {
      setDraft(null);
      setEditingId(null);
      setMessage({ kind: "info", text: "Saved. Learners get it in the next published release." });
      refresh();
    },
    onError: (e) => setMessage({ kind: "error", text: errorText(e, "Could not save the question.") }),
  });

  const remove = useMutation({
    mutationFn: async (id: string) => api.delete(`/quiz/questions/${id}`),
    onSuccess: () => refresh(),
    onError: (e) => setMessage({ kind: "error", text: errorText(e, "Could not delete the question.") }),
  });

  async function uploadPicture(file: File) {
    const form = new FormData();
    form.append("file", file);
    try {
      const resp = await api.post("/media/images", form);
      await queryClient.invalidateQueries({ queryKey: ["media-images"] });
      setDraft((d) => (d ? { ...d, mediaId: resp.data.id } : d));
    } catch (e) {
      setMessage({ kind: "error", text: errorText(e, "Could not upload the picture.") });
    }
  }

  const set = (patch: Partial<Draft>) => setDraft((d) => (d ? { ...d, ...patch } : d));
  const field = "mt-1 w-full border rounded px-2 py-1 text-sm";
  const small = "text-xs underline";

  function optionsEditor(d: Draft, multi: boolean) {
    return (
      <div className="space-y-2">
        <span className="text-xs text-gray-500">{multi ? "Options (tick every correct one)" : "Options (select the correct one)"}</span>
        {d.options.map((o, i) => (
          <div key={i} className="flex items-center gap-2">
            {multi ? (
              <input
                type="checkbox"
                checked={d.correctSet.includes(i)}
                onChange={(e) => set({ correctSet: e.target.checked ? [...d.correctSet, i] : d.correctSet.filter((x) => x !== i) })}
              />
            ) : (
              <input type="radio" checked={d.correctIndex === i} onChange={() => set({ correctIndex: i })} />
            )}
            <input
              className="flex-1 border rounded px-2 py-1 text-sm"
              value={o}
              placeholder={`Option ${i + 1}`}
              onChange={(e) => set({ options: d.options.map((x, j) => (j === i ? e.target.value : x)) })}
            />
            {d.options.length > 2 && (
              <button
                type="button"
                className={`${small} text-red-600`}
                onClick={() =>
                  set({
                    options: d.options.filter((_, j) => j !== i),
                    correctIndex: d.correctIndex === i ? 0 : d.correctIndex > i ? d.correctIndex - 1 : d.correctIndex,
                    correctSet: d.correctSet.filter((x) => x !== i).map((x) => (x > i ? x - 1 : x)),
                  })
                }
              >
                Remove
              </button>
            )}
          </div>
        ))}
        {d.options.length < 8 && (
          <button type="button" className={small} onClick={() => set({ options: [...d.options, ""] })}>
            + Add option
          </button>
        )}
      </div>
    );
  }

  function editor(d: Draft) {
    return (
      <form
        className="bg-white border rounded-lg p-4 mb-6 space-y-3 text-sm"
        onSubmit={(e) => {
          e.preventDefault();
          save.mutate(d);
        }}
      >
        <div className="flex items-center gap-3">
          <label className="block">
            <span className="text-xs text-gray-500">Question type</span>
            <select
              disabled={editingId !== null}
              className={field}
              value={d.type}
              onChange={(e) => setDraft(blank(e.target.value as QuestionType))}
            >
              {(Object.keys(TYPE_LABELS) as QuestionType[]).map((t) => (
                <option key={t} value={t}>
                  {TYPE_LABELS[t]}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-xs text-gray-500">Used in</span>
            <select className={field} value={d.usage} onChange={(e) => set({ usage: e.target.value as QuestionUsage })}>
              {(Object.keys(USAGE_LABELS) as QuestionUsage[]).map((u) => (
                <option key={u} value={u}>
                  {USAGE_LABELS[u]}
                </option>
              ))}
            </select>
          </label>
        </div>
        <label className="block">
          <span className="text-xs text-gray-500">Question</span>
          <textarea required rows={2} className={field} value={d.prompt} onChange={(e) => set({ prompt: e.target.value })} />
        </label>

        {d.type === "IMAGE_CHOICE" && (
          <div>
            <span className="text-xs text-gray-500">Picture</span>
            <div className="flex items-start gap-4 mt-1">
              <select className="border rounded px-2 py-1 text-sm" value={d.mediaId} onChange={(e) => set({ mediaId: e.target.value })}>
                <option value="">Choose from the media library…</option>
                {media.data?.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.filename}
                  </option>
                ))}
              </select>
              <label className={`${small} cursor-pointer`}>
                Upload a new picture
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    e.target.value = "";
                    if (f) uploadPicture(f);
                  }}
                />
              </label>
              {d.mediaId && <AuthenticatedImage mediaAssetId={d.mediaId} alt="Selected" className="h-24 rounded border" />}
            </div>
          </div>
        )}

        {(d.type === "MULTIPLE_CHOICE" || d.type === "IMAGE_CHOICE") && optionsEditor(d, false)}
        {d.type === "MULTIPLE_SELECT" && optionsEditor(d, true)}

        {d.type === "TRUE_FALSE" && (
          <div className="flex gap-6">
            <span className="text-xs text-gray-500">The statement is:</span>
            {[true, false].map((v) => (
              <label key={String(v)} className="flex items-center gap-1">
                <input type="radio" checked={d.trueFalse === v} onChange={() => set({ trueFalse: v })} />
                {v ? "True" : "False"}
              </label>
            ))}
          </div>
        )}

        {d.type === "MATCHING" && (
          <div className="space-y-2">
            <span className="text-xs text-gray-500">Pairs (the app shuffles the right-hand side)</span>
            {d.pairs.map((p, i) => (
              <div key={i} className="flex items-center gap-2">
                <input
                  className="flex-1 border rounded px-2 py-1"
                  placeholder="Left"
                  value={p.left}
                  onChange={(e) => set({ pairs: d.pairs.map((x, j) => (j === i ? { ...x, left: e.target.value } : x)) })}
                />
                <span>↔</span>
                <input
                  className="flex-1 border rounded px-2 py-1"
                  placeholder="Right"
                  value={p.right}
                  onChange={(e) => set({ pairs: d.pairs.map((x, j) => (j === i ? { ...x, right: e.target.value } : x)) })}
                />
                {d.pairs.length > 2 && (
                  <button type="button" className={`${small} text-red-600`} onClick={() => set({ pairs: d.pairs.filter((_, j) => j !== i) })}>
                    Remove
                  </button>
                )}
              </div>
            ))}
            {d.pairs.length < 8 && (
              <button type="button" className={small} onClick={() => set({ pairs: [...d.pairs, { left: "", right: "" }] })}>
                + Add pair
              </button>
            )}
          </div>
        )}

        {d.type === "ORDERING" && (
          <div className="space-y-2">
            <span className="text-xs text-gray-500">Items in the CORRECT order (the app shuffles them)</span>
            {d.items.map((it, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="w-5 text-gray-400">{i + 1}.</span>
                <input
                  className="flex-1 border rounded px-2 py-1"
                  value={it}
                  onChange={(e) => set({ items: d.items.map((x, j) => (j === i ? e.target.value : x)) })}
                />
                <button
                  type="button"
                  className={small}
                  disabled={i === 0}
                  onClick={() => set({ items: d.items.map((x, j) => (j === i - 1 ? d.items[i] : j === i ? d.items[i - 1] : x)) })}
                >
                  ↑
                </button>
                <button
                  type="button"
                  className={small}
                  disabled={i === d.items.length - 1}
                  onClick={() => set({ items: d.items.map((x, j) => (j === i + 1 ? d.items[i] : j === i ? d.items[i + 1] : x)) })}
                >
                  ↓
                </button>
                {d.items.length > 3 && (
                  <button type="button" className={`${small} text-red-600`} onClick={() => set({ items: d.items.filter((_, j) => j !== i) })}>
                    Remove
                  </button>
                )}
              </div>
            ))}
            {d.items.length < 8 && (
              <button type="button" className={small} onClick={() => set({ items: [...d.items, ""] })}>
                + Add item
              </button>
            )}
          </div>
        )}

        {d.type === "NUMERIC" && (
          <div className="grid grid-cols-3 gap-3">
            <label className="block">
              <span className="text-xs text-gray-500">Correct number</span>
              <input required type="number" step="any" className={field} value={d.numeric} onChange={(e) => set({ numeric: e.target.value })} />
            </label>
            <label className="block">
              <span className="text-xs text-gray-500">Allowed difference (±)</span>
              <input type="number" step="any" min="0" className={field} value={d.tolerance} onChange={(e) => set({ tolerance: e.target.value })} />
            </label>
            <label className="block">
              <span className="text-xs text-gray-500">Unit (optional, e.g. ml)</span>
              <input maxLength={20} className={field} value={d.unit} onChange={(e) => set({ unit: e.target.value })} />
            </label>
          </div>
        )}

        <label className="block">
          <span className="text-xs text-gray-500">Explanation shown after the quiz (quote the module text)</span>
          <textarea rows={2} className={field} value={d.explanation} onChange={(e) => set({ explanation: e.target.value })} />
        </label>
        <div className="flex gap-3">
          <button disabled={save.isPending} className="bg-gray-900 text-white rounded px-4 py-1.5 disabled:opacity-50">
            {save.isPending ? "Saving…" : editingId ? "Save changes" : "Add question"}
          </button>
          <button
            type="button"
            className="text-gray-600 underline"
            onClick={() => {
              setDraft(null);
              setEditingId(null);
            }}
          >
            Cancel
          </button>
        </div>
      </form>
    );
  }

  return (
    <div className="p-6">
      <Link to={`/content/${moduleId}`} className="text-sm text-gray-500 hover:underline">
        ← Back to module
      </Link>
      <h1 className="text-xl font-semibold mt-2 mb-1">
        Retired pre/post test{module.data ? ` — ${module.data.module_code} ${module.data.title}` : ""}
      </h1>
      <div className="bg-amber-50 border border-amber-200 text-amber-900 text-sm rounded p-3 mb-3">
        The per-module pre-tests and post-tests were retired in November 2026. These questions are archived: kept with their
        old attempts for history, never shown to learners, and read-only here. Learners now take one{" "}
        <Link to="/general-test" className="underline">General test</Link> before and after the training, and each module has
        an inline True/False quiz (TRUE_FALSE sections in the{" "}
        <Link to={`/content/${moduleId}`} className="underline">module editor</Link>).
      </div>
      {summary.data && (
        <p className="text-sm text-gray-500 mb-4">
          {summary.data.questions} active questions ({summary.data.pre_test_questions} in the pre-test,{" "}
          {summary.data.post_test_questions} in the post-test) · {summary.data.pre_test_attempts} pre-test and{" "}
          {summary.data.post_test_attempts} post-test attempts · {summary.data.learners_passed} learners completed.
        </p>
      )}
      {summary.data?.warning && <p className="text-sm text-amber-700 mb-4">{summary.data.warning}</p>}
      {summary.data && summary.data.post_test_questions > 0 && summary.data.post_test_questions < 10 && (
        <p className="text-sm text-amber-700 mb-4">
          With {summary.data.post_test_questions} post-test questions a learner must get every question right to reach 90%. Ten or
          more lets one mistake through.
        </p>
      )}
      {message && <p className={`text-sm mb-4 ${message.kind === "error" ? "text-red-600" : "text-green-700"}`}>{message.text}</p>}

      {canEdit && !draft && (
        <button onClick={() => setDraft(blank("MULTIPLE_CHOICE"))} className="bg-gray-900 text-white text-sm rounded px-4 py-2 mb-6">
          + New question
        </button>
      )}
      {draft && editor(draft)}

      <div className="space-y-2">
        {questions.isLoading && <p className="text-sm text-gray-500">Loading…</p>}
        {questions.data?.length === 0 && <p className="text-sm text-gray-500">No questions yet. This module can be completed without a quiz.</p>}
        {questions.data?.map((q, i) => (
          <div key={q.id} className="bg-white border rounded-lg p-3 flex items-start gap-3">
            <span className="text-gray-400 text-sm w-6">{i + 1}.</span>
            <div className="flex-1 text-sm">
              <span className="text-[10px] uppercase tracking-wide bg-gray-100 text-gray-600 rounded px-1.5 py-0.5">{TYPE_LABELS[q.question_type]}</span>
              {q.usage !== "BOTH" && (
                <span className="ml-2 text-[10px] uppercase tracking-wide bg-blue-50 text-blue-700 rounded px-1.5 py-0.5">
                  {USAGE_LABELS[q.usage]}
                </span>
              )}
              <p className="font-medium mt-1">{q.prompt}</p>
              <p className="text-xs text-gray-500 mt-0.5">{summarize(q)}</p>
              {typeof q.content.media_asset_id === "string" && (
                <AuthenticatedImage mediaAssetId={q.content.media_asset_id} alt="" className="h-20 mt-2 rounded border" />
              )}
            </div>
            {canEdit && (
              <div className="space-x-3 whitespace-nowrap">
                <button
                  className={small}
                  onClick={() => {
                    setEditingId(q.id);
                    setDraft(toDraft(q));
                  }}
                >
                  Edit
                </button>
                <button
                  className={`${small} text-red-600`}
                  onClick={() => {
                    if (window.confirm("Delete this question?")) remove.mutate(q.id);
                  }}
                >
                  Delete
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
