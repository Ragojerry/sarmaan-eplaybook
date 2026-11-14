import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import { useAuth } from "../services/auth";
import { ConsentText, Language } from "../types/api";

type Fields = Pick<ConsentText, "title" | "body" | "usage_label" | "button_label">;
const FIELD_KEYS: (keyof Fields)[] = ["title", "body", "usage_label", "button_label"];
const EMPTY: Fields = { title: "", body: "", usage_label: "", button_label: "" };
const LABELS: Record<keyof Fields, { label: string; rows?: number; max: number }> = {
  title: { label: "Title", max: 120 },
  // Includes the full privacy notice; phones fold it with "See more".
  body: { label: "Consent text and privacy notice", rows: 16, max: 40000 },
  usage_label: { label: "Usage statistics checkbox", max: 255 },
  button_label: { label: "Button", max: 60 },
};

function errorText(err: unknown, fallback: string) {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return "Please check the fields: the consent text needs at least 20 characters.";
  return fallback;
}

/**
 * The "Before you start" screen phones show on first launch, before login.
 * English is the source; each language can have its own translation, and a
 * phone without one shows English. Saving goes live at once (phones pick it
 * up the next time they open the language or consent screen online) and is
 * recorded in the audit log.
 */
export default function ConsentPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [language, setLanguage] = useState("en");
  const [form, setForm] = useState<Fields>(EMPTY);
  const [message, setMessage] = useState<{ kind: "error" | "info"; text: string } | null>(null);

  const languages = useQuery<Language[]>({
    queryKey: ["languages"],
    queryFn: async () => (await api.get("/languages")).data,
  });
  const texts = useQuery<ConsentText[]>({
    queryKey: ["consent"],
    queryFn: async () => (await api.get("/consent")).data,
  });

  const isAdmin = user?.role === "CONTENT_ADMIN" || user?.role === "SUPER_ADMIN";
  const canEdit = language === "en" ? isAdmin : isAdmin || user?.role === "LOCALISATION_REVIEWER";
  const english = texts.data?.find((t) => t.language === "en");
  const current = texts.data?.find((t) => t.language === language);

  // Reload the form only when the language or the saved version changes, not
  // on every refetch (the portal refetches when the window regains focus,
  // which would wipe a translator's unsaved typing).
  const loadedVersion = current?.version;
  useEffect(() => {
    setForm(
      current
        ? { title: current.title, body: current.body, usage_label: current.usage_label, button_label: current.button_label }
        : EMPTY,
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [language, loadedVersion, texts.isSuccess]);

  const save = useMutation({
    mutationFn: async () => (await api.put(`/consent/${language}`, form)).data,
    onSuccess: () => {
      setMessage({ kind: "info", text: "Saved. Phones show the new text the next time they open this screen online." });
      queryClient.invalidateQueries({ queryKey: ["consent"] });
    },
    onError: (e) => setMessage({ kind: "error", text: errorText(e, "Could not save the consent text.") }),
  });

  const remove = useMutation({
    mutationFn: async () => api.delete(`/consent/${language}`),
    onSuccess: () => {
      setMessage({ kind: "info", text: "Translation removed. Phones will show the English text." });
      queryClient.invalidateQueries({ queryKey: ["consent"] });
    },
    onError: (e) => setMessage({ kind: "error", text: errorText(e, "Could not remove the translation.") }),
  });

  const status = (code: string) => {
    const t = texts.data?.find((x) => x.language === code);
    if (!t) return code === "en" ? "" : " — not translated";
    return t.outdated ? " — needs update" : ` — v${t.version}`;
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-xl font-semibold">Consent text</h1>
        <p className="text-sm text-gray-500 mt-1 max-w-2xl">
          The “Before you start” screen phones show on first launch, in the language the person chose. Languages without
          a translation show the English text. Every change is versioned and recorded in the audit log.
        </p>
      </div>

      <label className="block mb-4 text-sm">
        <span className="text-xs text-gray-500 mr-2">Language</span>
        <select
          className="border rounded px-2 py-1"
          value={language}
          onChange={(e) => {
            setLanguage(e.target.value);
            setMessage(null);
          }}
        >
          {languages.data?.map((l) => (
            <option key={l.code} value={l.code}>
              {l.name} ({l.native_name}){status(l.code)}
            </option>
          ))}
        </select>
      </label>

      {message && (
        <p className={`text-sm mb-4 ${message.kind === "error" ? "text-red-600" : "text-green-700"}`}>{message.text}</p>
      )}
      {current?.outdated && (
        <p className="text-sm mb-4 text-amber-700">
          The English text has changed since this translation was saved. Compare it with the English text and update it.
        </p>
      )}
      {language !== "en" && !current && (
        <p className="text-sm mb-4 text-gray-600">No translation yet: phones choosing this language show the English text.</p>
      )}

      <div className={`grid gap-6 ${language !== "en" ? "lg:grid-cols-2" : ""}`}>
        {language !== "en" && english && (
          <div className="bg-gray-50 border rounded-lg p-4 text-sm space-y-3">
            <h2 className="text-xs font-medium text-gray-500">English (source, version {english.version})</h2>
            {FIELD_KEYS.map((k) => (
              <div key={k}>
                <div className="text-xs text-gray-500">{LABELS[k].label}</div>
                <p className="whitespace-pre-wrap text-gray-800">{english[k]}</p>
              </div>
            ))}
          </div>
        )}

        <form
          className="bg-white border rounded-lg p-4 space-y-3 text-sm"
          onSubmit={(e) => {
            e.preventDefault();
            save.mutate();
          }}
        >
          {FIELD_KEYS.map((k) => (
            <label key={k} className="block">
              <span className="text-xs text-gray-500">{LABELS[k].label}</span>
              {LABELS[k].rows ? (
                <textarea
                  required
                  minLength={20}
                  maxLength={LABELS[k].max}
                  rows={LABELS[k].rows}
                  disabled={!canEdit}
                  className="mt-1 w-full border rounded px-2 py-1 disabled:bg-gray-50"
                  value={form[k]}
                  onChange={(e) => setForm({ ...form, [k]: e.target.value })}
                />
              ) : (
                <input
                  required
                  maxLength={LABELS[k].max}
                  disabled={!canEdit}
                  className="mt-1 w-full border rounded px-2 py-1 disabled:bg-gray-50"
                  value={form[k]}
                  onChange={(e) => setForm({ ...form, [k]: e.target.value })}
                />
              )}
            </label>
          ))}
          {current && (
            <p className="text-xs text-gray-400">
              Version {current.version}
              {current.updated_at && ` · last saved ${new Date(current.updated_at).toLocaleString()}`}
            </p>
          )}
          {canEdit ? (
            <div className="space-x-3">
              <button disabled={save.isPending} className="bg-gray-900 text-white rounded px-4 py-1.5 disabled:opacity-50">
                {save.isPending ? "Saving…" : language === "en" ? "Save English text" : "Save translation"}
              </button>
              {language !== "en" && current && (
                <button
                  type="button"
                  className="text-xs underline text-red-700"
                  onClick={() => {
                    if (window.confirm("Remove this translation? Phones will show the English text.")) remove.mutate();
                  }}
                >
                  Remove translation
                </button>
              )}
            </div>
          ) : (
            <p className="text-xs text-gray-500">
              {language === "en" ? "Only content admins can change the English text." : "You can view this text but not edit it."}
            </p>
          )}
        </form>
      </div>
    </div>
  );
}
