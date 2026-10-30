import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "../services/api";
import { useAuth } from "../services/auth";
import { Language, ModuleTranslation } from "../types/api";

const STEPS = ["DRAFT", "PROGRAMME_REVIEW", "LOCALISATION_REVIEW", "TECHNICAL_QA", "PUBLISHED"];

/**
 * Translate one module into another language: download the English text as a
 * CSV, send it to a translator, upload the result (it lands as DRAFT), then
 * push it through the normal review steps. Once PUBLISHED, phones set to that
 * language show it on their next sync; untranslated text stays in English.
 */
export default function ModuleTranslationsPanel({ moduleId }: { moduleId: string }) {
  const { user } = useAuth();
  const canImport = user?.role === "CONTENT_ADMIN" || user?.role === "SUPER_ADMIN";
  const [code, setCode] = useState("");
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  const { data: languages } = useQuery<Language[]>({
    queryKey: ["languages"],
    queryFn: async () => (await api.get("/languages")).data,
  });
  const { data: translations, refetch } = useQuery<ModuleTranslation[]>({
    queryKey: ["module-translations", moduleId],
    queryFn: async () => (await api.get(`/modules/${moduleId}/translations`)).data,
  });

  const others = (languages ?? []).filter((l) => l.code !== "en");
  const language = others.find((l) => l.code === code);
  const current = translations?.find((t) => t.language_id === language?.id);

  const fail = (e: any) => setMessage({ ok: false, text: e?.response?.data?.detail ?? "Something went wrong." });

  const download = async () => {
    try {
      const r = await api.get(`/modules/${moduleId}/translations/export.csv`, {
        params: { language: code },
        responseType: "blob",
      });
      const url = URL.createObjectURL(r.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `module_${code}.csv`;
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
      return (await api.post(`/modules/${moduleId}/translations/import`, form, { params: { language: code } })).data;
    },
    onSuccess: (d) => {
      setMessage({ ok: true, text: `Imported ${d.strings} strings as a DRAFT. Now submit it for review.` });
      refetch();
    },
    onError: fail,
  });

  const step = useMutation({
    mutationFn: async (action: "submit-review" | "approve" | "reject") =>
      (
        await api.post(
          `/modules/translations/${current!.id}/${action}`,
          action === "reject" ? { reason: rejectReason || "Needs changes" } : undefined,
        )
      ).data,
    onSuccess: () => {
      setMessage(null);
      setRejectReason("");
      refetch();
    },
    onError: fail,
  });

  return (
    <div className="bg-white border rounded-lg p-4 mb-6">
      <h2 className="text-sm font-medium mb-1">Translations</h2>
      <p className="text-xs text-gray-500 mb-3">
        Add a language on the Languages page first. Phones show a language once its translation of this module is
        PUBLISHED; anything untranslated stays in English.
      </p>
      <select
        className="border rounded px-3 py-1.5 text-sm"
        value={code}
        onChange={(e) => {
          setCode(e.target.value);
          setMessage(null);
        }}
      >
        <option value="">Choose a language…</option>
        {others.map((l) => (
          <option key={l.id} value={l.code}>
            {l.name} ({l.code})
          </option>
        ))}
      </select>

      {language && (
        <div className="mt-4 space-y-3">
          <p className="text-sm">
            Status:{" "}
            <span className="font-medium">{current ? current.status.replace("_", " ") : "No translation yet"}</span>
          </p>
          {current && (
            <div className="flex flex-wrap gap-1 text-xs">
              {STEPS.map((s) => (
                <span
                  key={s}
                  className={`px-2 py-0.5 rounded ${
                    s === current.status ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-400"
                  }`}
                >
                  {s.replace("_", " ")}
                </span>
              ))}
            </div>
          )}
          <div className="flex flex-wrap items-center gap-2">
            <button onClick={download} className="border text-sm rounded px-3 py-1.5">
              Download CSV for translator
            </button>
            {canImport && (
              <label className="bg-gray-900 text-white text-sm rounded px-3 py-1.5 cursor-pointer">
                {upload.isPending ? "Uploading…" : "Upload translated CSV"}
                <input
                  type="file"
                  accept=".csv,text/csv"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) upload.mutate(f);
                    e.target.value = "";
                  }}
                />
              </label>
            )}
          </div>
          {current && current.status === "DRAFT" && canImport && (
            <button onClick={() => step.mutate("submit-review")} className="bg-blue-600 text-white text-sm rounded px-3 py-1.5">
              Submit for review
            </button>
          )}
          {current && ["PROGRAMME_REVIEW", "LOCALISATION_REVIEW", "TECHNICAL_QA"].includes(current.status) && (
            <div className="flex flex-wrap items-center gap-2">
              <button onClick={() => step.mutate("approve")} className="bg-green-600 text-white text-sm rounded px-3 py-1.5">
                Approve → next stage
              </button>
              <input
                className="border rounded px-3 py-1.5 text-sm"
                placeholder="Reason (if rejecting)"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
              />
              <button onClick={() => step.mutate("reject")} className="bg-red-600 text-white text-sm rounded px-3 py-1.5">
                Reject
              </button>
            </div>
          )}
          {message && <p className={`text-sm ${message.ok ? "text-green-700" : "text-red-600"}`}>{message.text}</p>}
        </div>
      )}
    </div>
  );
}
