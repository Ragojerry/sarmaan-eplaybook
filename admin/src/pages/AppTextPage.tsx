import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import { useAuth } from "../services/auth";
import {
  AppStringItem,
  AppStringLanguageStats,
  AppStringList,
  AppStringProblem,
  ContentReviewStatus,
  Language,
} from "../types/api";

type Show = "all" | "missing" | "draft" | "in_review" | "published" | "needs_update" | "rejected";
const FILTERS: { value: Show; label: string }[] = [
  { value: "all", label: "All" },
  { value: "missing", label: "Missing" },
  { value: "draft", label: "Draft" },
  { value: "in_review", label: "In review" },
  { value: "published", label: "Published" },
  { value: "needs_update", label: "Needs update" },
  { value: "rejected", label: "Rejected" },
];
const IN_REVIEW: ContentReviewStatus[] = ["PROGRAMME_REVIEW", "LOCALISATION_REVIEW", "TECHNICAL_QA"];
// The stage each role moves forward (content governance, unchanged).
const STAGE_OF_ROLE: Record<string, ContentReviewStatus> = {
  CONTENT_ADMIN: "DRAFT",
  PROGRAM_REVIEWER: "PROGRAMME_REVIEW",
  LOCALISATION_REVIEWER: "LOCALISATION_REVIEW",
  TECHNICAL_REVIEWER: "TECHNICAL_QA",
};
const PLACEHOLDER = /\{(\w+)\}/g;

function placeholdersOf(text: string): string[] {
  return Array.from(new Set(Array.from(text.matchAll(PLACEHOLDER), (m) => m[1])));
}

/** Same rules as the server (app/l10n/rules.py), shown while typing. */
function checkDraft(item: AppStringItem, text: string, textOne: string) {
  const errors: string[] = [];
  const warnings: string[] = [];
  const allowed = new Set(item.placeholders);
  if (!text.trim()) errors.push("The translation is empty.");
  if (item.plural && !textOne.trim()) errors.push("Translate the singular form too.");
  for (const [form, value] of [["translation", text], ["singular form", textOne]] as const) {
    const unknown = placeholdersOf(value).filter((p) => !allowed.has(p));
    if (unknown.length) errors.push(`The ${form} uses ${unknown.map((u) => `{${u}}`).join(", ")}, which the English does not have.`);
  }
  const missing = item.placeholders.filter((p) => !placeholdersOf(text).includes(p));
  if (text.trim() && missing.length) warnings.push(`Leaves out ${missing.map((m) => `{${m}}`).join(", ")}.`);
  return { errors, warnings };
}

function detailOf(err: unknown): { message: string; problems: AppStringProblem[] } {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return { message: detail, problems: [] };
  if (detail && typeof detail === "object") {
    const d = detail as { message?: string; problems?: AppStringProblem[]; errors?: string[] };
    if (d.errors) return { message: d.errors.join(" "), problems: [] };
    return { message: d.message ?? "Something went wrong.", problems: d.problems ?? [] };
  }
  return { message: "Something went wrong.", problems: [] };
}

function StatusBadge({ item }: { item: AppStringItem }) {
  if (!item.status) return <span className="text-xs text-gray-400">Not translated (English shows)</span>;
  const tone =
    item.status === "PUBLISHED"
      ? "bg-green-100 text-green-800"
      : item.status === "REJECTED"
        ? "bg-red-100 text-red-700"
        : item.status === "DRAFT"
          ? "bg-gray-100 text-gray-700"
          : "bg-blue-100 text-blue-700";
  return (
    <div className="space-y-1">
      <span className={`inline-block text-xs px-2 py-0.5 rounded ${tone}`}>{item.status.replace(/_/g, " ")}</span>
      {item.status !== "PUBLISHED" && item.published_text && (
        <div className="text-[11px] text-gray-500">Phones still show the last published text</div>
      )}
    </div>
  );
}

/**
 * The mobile app's interface text (buttons, labels, messages) per language.
 * English comes from the app and cannot be edited here. Translations follow the
 * content governance steps; only PUBLISHED text reaches phones, on their next
 * sync, without a new app. Anything untranslated shows in English.
 */
export default function AppTextPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const role = user?.role ?? "";
  const isSuper = role === "SUPER_ADMIN";
  const canEdit = isSuper || role === "CONTENT_ADMIN" || role === "LOCALISATION_REVIEWER";
  const myStage = STAGE_OF_ROLE[role];

  const [code, setCode] = useState("");
  const [show, setShow] = useState<Show>("all");
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [problems, setProblems] = useState<AppStringProblem[]>([]);

  useEffect(() => {
    const t = setTimeout(() => setQuery(search.trim()), 250);
    return () => clearTimeout(t);
  }, [search]);

  const languages = useQuery<Language[]>({ queryKey: ["languages"], queryFn: async () => (await api.get("/languages")).data });
  const others = (languages.data ?? []).filter((l) => l.code !== "en");
  useEffect(() => {
    if (!code && others.length) setCode(others[0].code);
  }, [code, others]);

  const stats = useQuery<{ total: number; languages: AppStringLanguageStats[] }>({
    queryKey: ["app-strings-stats"],
    queryFn: async () => (await api.get("/app-strings/stats")).data,
  });
  const list = useQuery<AppStringList>({
    queryKey: ["app-strings", code, show, query],
    queryFn: async () => (await api.get("/app-strings", { params: { language: code, show, q: query } })).data,
    enabled: !!code,
  });
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["app-strings"] });
    queryClient.invalidateQueries({ queryKey: ["app-strings-stats"] });
  };
  const fail = (e: unknown) => {
    const d = detailOf(e);
    setMessage({ ok: false, text: d.message });
    setProblems(d.problems);
  };

  const items = list.data?.items ?? [];
  // Bulk: what this person can move on, among the strings shown.
  const movable = useMemo(
    () => items.filter((i) => i.translation_id && i.status && (isSuper ? i.status !== "PUBLISHED" && i.status !== "REJECTED" : i.status === myStage)),
    [items, isSuper, myStage],
  );
  const selfEdited = movable.filter((i) => !isSuper && i.status !== "DRAFT" && i.edited_by_id === user?.id);

  const bulk = useMutation({
    mutationFn: async (action: "submit-review" | "approve") =>
      (await api.post("/app-strings/translations/bulk", { action, ids: movable.map((i) => i.translation_id) })).data,
    onSuccess: (d) => {
      setMessage({ ok: true, text: `${d.moved} string(s) moved to the next stage.` });
      setProblems([]);
      refresh();
    },
    onError: fail,
  });

  const download = async (format: "csv" | "json") => {
    try {
      const r = await api.get("/app-strings/export", { params: { language: code, format }, responseType: "blob" });
      const url = URL.createObjectURL(r.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `app_text_${code}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      fail(e);
    }
  };

  const upload = useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return (await api.post("/app-strings/import", form, { params: { language: code } })).data;
    },
    onSuccess: (d) => {
      const warn = d.warnings?.length ? ` ${d.warnings.length} warning(s) below.` : "";
      setMessage({
        ok: true,
        text: `Imported as DRAFT: ${d.created} new, ${d.updated} changed, ${d.unchanged} unchanged, ${d.skipped_empty} left empty.${warn} Submit them for review next.`,
      });
      setProblems(d.warnings ?? []);
      refresh();
    },
    onError: fail,
  });

  const languageStats = stats.data?.languages.find((l) => l.language === code);

  return (
    <div className="p-6">
      <div className="mb-5">
        <h1 className="text-xl font-semibold">App interface text</h1>
        <p className="text-sm text-gray-500 mt-1 max-w-3xl">
          The buttons, labels and messages of the mobile app. English comes from the app itself. A translation reaches
          phones only when it is PUBLISHED (after programme, localisation and technical review), on their next sync, with
          no new app needed. Anything not translated shows in English.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        {stats.data?.languages.map((l) => (
          <button
            key={l.language}
            onClick={() => setCode(l.language)}
            className={`text-left bg-white border rounded-lg p-3 ${l.language === code ? "border-gray-900" : ""}`}
          >
            <div className="text-sm font-medium">
              {l.name} <span className="text-gray-400">({l.language})</span>
            </div>
            <div className="mt-2 h-1.5 bg-gray-100 rounded">
              <div className="h-1.5 bg-gray-900 rounded" style={{ width: `${l.published_percent}%` }} />
            </div>
            <div className="mt-1 text-xs text-gray-500">
              Translated {l.translated}/{l.total} ({l.translated_percent}%) · Published {l.published}/{l.total} (
              {l.published_percent}%)
            </div>
            {(l.in_review > 0 || l.needs_update > 0) && (
              <div className="text-xs text-gray-500">
                {l.in_review > 0 && `${l.in_review} in review`}
                {l.in_review > 0 && l.needs_update > 0 && " · "}
                {l.needs_update > 0 && <span className="text-amber-700">{l.needs_update} need update</span>}
              </div>
            )}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-3">
        <select className="border rounded px-2 py-1.5 text-sm" value={code} onChange={(e) => setCode(e.target.value)}>
          {others.map((l) => (
            <option key={l.code} value={l.code}>
              {l.name} ({l.code})
            </option>
          ))}
        </select>
        <input
          className="border rounded px-3 py-1.5 text-sm w-64"
          placeholder="Search key, English or translation…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <div className="flex flex-wrap gap-1">
          {FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setShow(f.value)}
              className={`text-xs px-2.5 py-1 rounded border ${show === f.value ? "bg-gray-900 text-white border-gray-900" : "bg-white"}`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-4">
        <button onClick={() => download("csv")} className="border text-sm rounded px-3 py-1.5 bg-white" disabled={!code}>
          Download CSV for translator
        </button>
        <button onClick={() => download("json")} className="border text-sm rounded px-3 py-1.5 bg-white" disabled={!code}>
          Download JSON
        </button>
        {canEdit && (
          <label className="bg-gray-900 text-white text-sm rounded px-3 py-1.5 cursor-pointer">
            {upload.isPending ? "Uploading…" : "Upload translated CSV / JSON"}
            <input
              type="file"
              accept=".csv,.json,text/csv,application/json"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) upload.mutate(f);
                e.target.value = "";
              }}
            />
          </label>
        )}
        {movable.length > 0 && (
          <button
            onClick={() => bulk.mutate(myStage === "DRAFT" || (isSuper && movable.every((i) => i.status === "DRAFT")) ? "submit-review" : "approve")}
            disabled={bulk.isPending || selfEdited.length > 0}
            title={selfEdited.length ? "Some of these were edited by you; another reviewer must approve them." : undefined}
            className="bg-blue-600 text-white text-sm rounded px-3 py-1.5 disabled:opacity-50"
          >
            {myStage === "DRAFT" ? "Submit" : "Approve"} all {movable.length} shown at your stage
          </button>
        )}
        {languageStats && (
          <span className="text-xs text-gray-500 ml-auto">
            {list.data ? `${items.length} of ${list.data.total} strings shown` : ""}
          </span>
        )}
      </div>

      {message && <p className={`text-sm mb-2 ${message.ok ? "text-green-700" : "text-red-600"}`}>{message.text}</p>}
      {problems.length > 0 && (
        <div className="bg-white border rounded-lg mb-4 max-h-64 overflow-auto">
          <table className="w-full text-xs">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th className="px-3 py-1.5">Row</th>
                <th className="px-3 py-1.5">Key</th>
                <th className="px-3 py-1.5">Problem</th>
              </tr>
            </thead>
            <tbody>
              {problems.map((p, i) => (
                <tr key={i} className="border-t">
                  <td className="px-3 py-1.5">{p.row ?? ""}</td>
                  <td className="px-3 py-1.5 font-mono">{p.key}</td>
                  <td className="px-3 py-1.5">{p.problem}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="bg-white border rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs text-gray-500">
            <tr>
              <th className="px-3 py-2 w-56">Key and note</th>
              <th className="px-3 py-2 w-72">English</th>
              <th className="px-3 py-2">Translation</th>
              <th className="px-3 py-2 w-48">Status</th>
            </tr>
          </thead>
          <tbody>
            {list.isLoading && (
              <tr>
                <td className="px-3 py-4 text-gray-500" colSpan={4}>
                  Loading…
                </td>
              </tr>
            )}
            {!list.isLoading && items.length === 0 && (
              <tr>
                <td className="px-3 py-4 text-gray-500" colSpan={4}>
                  No strings match.
                </td>
              </tr>
            )}
            {items.map((item) => (
              <Row
                key={item.key}
                item={item}
                language={code}
                canEdit={canEdit}
                role={role}
                userId={user?.id}
                onDone={(text) => {
                  setMessage(text ? { ok: true, text } : null);
                  setProblems([]);
                  refresh();
                }}
                onError={fail}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Row({
  item,
  language,
  canEdit,
  role,
  userId,
  onDone,
  onError,
}: {
  item: AppStringItem;
  language: string;
  canEdit: boolean;
  role: string;
  userId?: string;
  onDone: (text: string | null) => void;
  onError: (e: unknown) => void;
}) {
  const [text, setText] = useState(item.text ?? "");
  const [textOne, setTextOne] = useState(item.text_one ?? "");
  const [reason, setReason] = useState("");
  // Reload only when the saved value changes, not on every refetch (keeps unsaved typing).
  useEffect(() => {
    setText(item.text ?? "");
    setTextOne(item.text_one ?? "");
  }, [item.text, item.text_one, item.translation_id]);

  const dirty = text !== (item.text ?? "") || textOne !== (item.text_one ?? "");
  const check = checkDraft(item, text, textOne);
  const isSuper = role === "SUPER_ADMIN";
  const canMove = item.status && (isSuper || STAGE_OF_ROLE[role] === item.status);
  const ownEdit = !isSuper && item.status && IN_REVIEW.includes(item.status) && item.edited_by_id === userId;

  const save = useMutation({
    mutationFn: async () =>
      (await api.put(`/app-strings/${item.key}/translations/${language}`, { text, text_one: item.plural ? textOne : null })).data,
    onSuccess: (d) => onDone(d.warnings?.length ? `Saved as DRAFT. Warning: ${d.warnings.join(" ")}` : null),
    onError,
  });
  const step = useMutation({
    mutationFn: async (action: "submit-review" | "approve" | "reject") =>
      (
        await api.post(
          `/app-strings/translations/${item.translation_id}/${action}`,
          action === "reject" ? { reason: reason || "Needs changes" } : undefined,
        )
      ).data,
    onSuccess: () => {
      setReason("");
      onDone(null);
    },
    onError,
  });

  return (
    <tr className="border-t align-top">
      <td className="px-3 py-2">
        <div className="font-mono text-xs break-all">{item.key}</div>
        <div className="text-xs text-gray-500 mt-1">{item.note}</div>
        {item.placeholders.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {item.placeholders.map((p) => (
              <span key={p} className="font-mono text-[11px] bg-gray-100 rounded px-1">{`{${p}}`}</span>
            ))}
          </div>
        )}
      </td>
      <td className="px-3 py-2 text-sm">
        <div>{item.english}</div>
        {item.plural && (
          <div className="text-xs text-gray-500 mt-1">
            Singular: <span className="text-gray-800">{item.english_one}</span>
          </div>
        )}
      </td>
      <td className="px-3 py-2">
        {canEdit ? (
          <div className="space-y-1">
            <textarea
              className="border rounded w-full px-2 py-1 text-sm"
              rows={Math.min(4, Math.max(1, Math.ceil(item.english.length / 60)))}
              value={text}
              placeholder={item.plural ? "Plural form" : "Translation"}
              onChange={(e) => setText(e.target.value)}
            />
            {item.plural && (
              <textarea
                className="border rounded w-full px-2 py-1 text-sm"
                rows={1}
                value={textOne}
                placeholder="Singular form"
                onChange={(e) => setTextOne(e.target.value)}
              />
            )}
            {dirty && check.errors.map((e) => <div key={e} className="text-xs text-red-600">{e}</div>)}
            {dirty && check.warnings.map((w) => <div key={w} className="text-xs text-amber-700">{w}</div>)}
            {dirty && (
              <div className="flex gap-2">
                <button
                  onClick={() => save.mutate()}
                  disabled={save.isPending || check.errors.length > 0}
                  className="bg-gray-900 text-white text-xs rounded px-2.5 py-1 disabled:opacity-50"
                >
                  Save as draft
                </button>
                <button
                  onClick={() => {
                    setText(item.text ?? "");
                    setTextOne(item.text_one ?? "");
                  }}
                  className="border text-xs rounded px-2.5 py-1"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="text-sm">
            {item.text ?? <span className="text-gray-400">—</span>}
            {item.plural && item.text_one && <div className="text-xs text-gray-500 mt-1">Singular: {item.text_one}</div>}
          </div>
        )}
      </td>
      <td className="px-3 py-2 space-y-1">
        <StatusBadge item={item} />
        {item.needs_update && <div className="text-xs text-amber-700">Needs update: the English changed</div>}
        {item.edited_by && (
          <div className="text-[11px] text-gray-500">
            Edited by {item.edited_by}
            {item.edited_at && ` · ${new Date(item.edited_at).toLocaleDateString()}`}
          </div>
        )}
        {canMove && !dirty && item.status === "DRAFT" && (
          <button onClick={() => step.mutate("submit-review")} className="bg-blue-600 text-white text-xs rounded px-2.5 py-1">
            Submit for review
          </button>
        )}
        {canMove && !dirty && item.status && IN_REVIEW.includes(item.status) && (
          ownEdit ? (
            <div className="text-[11px] text-gray-500">You edited this; another reviewer must review it.</div>
          ) : (
            <div className="space-y-1">
              <button onClick={() => step.mutate("approve")} className="bg-green-600 text-white text-xs rounded px-2.5 py-1">
                Approve → next stage
              </button>
              <div className="flex gap-1">
                <input
                  className="border rounded px-2 py-0.5 text-xs w-28"
                  placeholder="Reason"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                />
                <button onClick={() => step.mutate("reject")} className="bg-red-600 text-white text-xs rounded px-2 py-0.5">
                  Reject
                </button>
              </div>
            </div>
          )
        )}
      </td>
    </tr>
  );
}
