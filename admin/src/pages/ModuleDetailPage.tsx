import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "../services/api";
import { useAuth } from "../services/auth";
import AuthenticatedImage from "../components/AuthenticatedImage";
import { Module, ModuleTranslation, ContentSection, Language, ContentType } from "../types/api";

const WORKFLOW_STAGES = ["DRAFT", "PROGRAMME_REVIEW", "LOCALISATION_REVIEW", "TECHNICAL_QA", "PUBLISHED"];

const CONTENT_TYPES: ContentType[] = [
  "TEXT",
  "HEADING",
  "IMAGE",
  "TABLE",
  "CALLOUT",
  "WARNING",
  "JOB_AID",
  "VIDEO",
  "AUDIO",
  "LIST",
];

function WorkflowBar({ status }: { status: string }) {
  if (status === "REJECTED") {
    return <span className="px-3 py-1 rounded bg-red-100 text-red-700 text-sm font-medium">REJECTED</span>;
  }
  const currentIndex = WORKFLOW_STAGES.indexOf(status);
  return (
    <div className="flex items-center gap-2">
      {WORKFLOW_STAGES.map((stage, i) => (
        <div key={stage} className="flex items-center gap-2">
          <span
            className={`px-2 py-1 rounded text-xs font-medium ${
              i < currentIndex
                ? "bg-green-100 text-green-700"
                : i === currentIndex
                ? "bg-blue-100 text-blue-700"
                : "bg-gray-100 text-gray-400"
            }`}
          >
            {stage.replace("_", " ")}
          </span>
          {i < WORKFLOW_STAGES.length - 1 && <span className="text-gray-300">→</span>}
        </div>
      ))}
    </div>
  );
}

export default function ModuleDetailPage() {
  const { moduleId } = useParams<{ moduleId: string }>();
  const { user } = useAuth();
  const [rejectReason, setRejectReason] = useState("");
  const [showReject, setShowReject] = useState<string | null>(null);
  const [newSection, setNewSection] = useState<{ content_type: ContentType; title: string; text: string } | null>(
    null,
  );

  const canEdit = user?.role === "CONTENT_ADMIN" || user?.role === "SUPER_ADMIN";

  const { data: module } = useQuery<Module>({
    queryKey: ["module", moduleId],
    queryFn: async () => (await api.get(`/modules/${moduleId}`)).data,
    enabled: !!moduleId,
  });

  const { data: translations, refetch: refetchTranslations } = useQuery<ModuleTranslation[]>({
    queryKey: ["module-translations", moduleId],
    queryFn: async () => (await api.get(`/modules/${moduleId}/translations`)).data,
    enabled: !!moduleId,
  });

  const { data: sections, refetch: refetchSections } = useQuery<ContentSection[]>({
    queryKey: ["module-sections", moduleId],
    queryFn: async () => (await api.get(`/modules/${moduleId}/sections`)).data,
    enabled: !!moduleId,
  });

  const { data: languages } = useQuery<Language[]>({
    queryKey: ["languages"],
    queryFn: async () => (await api.get("/languages")).data,
  });

  const englishTranslation = translations?.find((t) => {
    const lang = languages?.find((l) => l.id === t.language_id);
    return lang?.code === "en";
  });

  const createEnglishTranslation = useMutation({
    mutationFn: async () => {
      const english = languages?.find((l) => l.code === "en");
      if (!english) throw new Error("English language not found");
      return (
        await api.post(`/modules/${moduleId}/translations`, {
          language_id: english.id,
          title: module?.title ?? "",
        })
      ).data;
    },
    onSuccess: () => refetchTranslations(),
  });

  const submitReview = useMutation({
    mutationFn: async () => (await api.post(`/modules/translations/${englishTranslation!.id}/submit-review`)).data,
    onSuccess: () => refetchTranslations(),
  });

  const approve = useMutation({
    mutationFn: async () => (await api.post(`/modules/translations/${englishTranslation!.id}/approve`)).data,
    onSuccess: () => refetchTranslations(),
  });

  const reject = useMutation({
    mutationFn: async () =>
      (
        await api.post(`/modules/translations/${englishTranslation!.id}/reject`, { reason: rejectReason })
      ).data,
    onSuccess: () => {
      refetchTranslations();
      setShowReject(null);
      setRejectReason("");
    },
  });

  const createSection = useMutation({
    mutationFn: async () => {
      const nextNumber = (sections?.length ?? 0) + 1;
      return (
        await api.post(`/modules/${moduleId}/sections`, {
          section_number: nextNumber,
          sort_order: nextNumber,
          content_type: newSection!.content_type,
          title: newSection!.title || null,
          content: { text: newSection!.text },
        })
      ).data;
    },
    onSuccess: () => {
      refetchSections();
      setNewSection(null);
    },
  });

  const deleteSection = useMutation({
    mutationFn: async (sectionId: string) => api.delete(`/modules/sections/${sectionId}`),
    onSuccess: () => refetchSections(),
  });

  if (!module) return <div className="p-6 text-sm text-gray-500">Loading…</div>;

  return (
    <div className="p-6">
      <Link to="/content" className="text-sm text-gray-500 hover:underline">
        ← Back to modules
      </Link>
      <h1 className="text-xl font-semibold mt-2 mb-1">
        {module.module_code} — {module.title}
      </h1>
      <p className="text-sm text-gray-500 mb-6">Module status: {module.status}</p>

      <div className="bg-white border rounded-lg p-4 mb-6">
        <h2 className="text-sm font-medium mb-3">Content governance workflow (English)</h2>
        {!englishTranslation ? (
          canEdit ? (
            <button
              onClick={() => createEnglishTranslation.mutate()}
              className="bg-gray-900 text-white text-sm rounded px-4 py-2"
            >
              Start English content (creates DRAFT)
            </button>
          ) : (
            <p className="text-sm text-gray-500">No content drafted yet.</p>
          )
        ) : (
          <div className="space-y-4">
            <WorkflowBar status={englishTranslation.status} />
            <div className="flex gap-2">
              {englishTranslation.status === "DRAFT" && canEdit && (
                <button
                  onClick={() => submitReview.mutate()}
                  className="bg-blue-600 text-white text-sm rounded px-3 py-1.5"
                >
                  Submit for review
                </button>
              )}
              {["PROGRAMME_REVIEW", "LOCALISATION_REVIEW", "TECHNICAL_QA"].includes(englishTranslation.status) && (
                <>
                  <button
                    onClick={() => approve.mutate()}
                    className="bg-green-600 text-white text-sm rounded px-3 py-1.5"
                  >
                    Approve → next stage
                  </button>
                  <button
                    onClick={() => setShowReject(englishTranslation.id)}
                    className="bg-red-600 text-white text-sm rounded px-3 py-1.5"
                  >
                    Reject
                  </button>
                </>
              )}
            </div>
            {(approve.isError || submitReview.isError || reject.isError) && (
              <p className="text-sm text-red-600">
                {((approve.error || submitReview.error || reject.error) as any)?.response?.data?.detail ??
                  "Your role cannot perform this action at the current stage."}
              </p>
            )}
            {showReject === englishTranslation.id && (
              <div className="flex gap-2 items-start">
                <input
                  className="border rounded px-3 py-1.5 text-sm flex-1"
                  placeholder="Reason for rejection"
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                />
                <button
                  onClick={() => reject.mutate()}
                  className="bg-red-600 text-white text-sm rounded px-3 py-1.5"
                >
                  Confirm reject
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="bg-white border rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium">Content sections (structured, no raw HTML)</h2>
          {canEdit && (
            <button
              onClick={() => setNewSection({ content_type: "TEXT", title: "", text: "" })}
              className="text-sm text-blue-600 hover:underline"
            >
              + Add section
            </button>
          )}
        </div>

        {newSection && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              createSection.mutate();
            }}
            className="border rounded p-3 mb-3 space-y-2 bg-gray-50"
          >
            <select
              className="border rounded px-2 py-1 text-sm"
              value={newSection.content_type}
              onChange={(e) => setNewSection({ ...newSection, content_type: e.target.value as ContentType })}
            >
              {CONTENT_TYPES.map((ct) => (
                <option key={ct} value={ct}>
                  {ct}
                </option>
              ))}
            </select>
            <input
              className="w-full border rounded px-2 py-1 text-sm"
              placeholder="Section title (optional)"
              value={newSection.title}
              onChange={(e) => setNewSection({ ...newSection, title: e.target.value })}
            />
            <textarea
              className="w-full border rounded px-2 py-1 text-sm"
              placeholder="Content text"
              rows={3}
              value={newSection.text}
              onChange={(e) => setNewSection({ ...newSection, text: e.target.value })}
            />
            <div className="flex gap-2">
              <button type="submit" className="bg-gray-900 text-white text-sm rounded px-3 py-1.5">
                Save section
              </button>
              <button
                type="button"
                onClick={() => setNewSection(null)}
                className="text-sm text-gray-500 px-3 py-1.5"
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {!sections || sections.length === 0 ? (
          <p className="text-sm text-gray-500">No sections yet.</p>
        ) : (
          <ul className="divide-y">
            {sections.map((s) => (
              <li key={s.id} className="py-3 flex items-start justify-between gap-4">
                <div className="flex-1">
                  <span className="text-xs uppercase text-gray-400">{s.content_type}</span>
                  {s.title && <p className="text-sm font-medium">{s.title}</p>}
                  {typeof s.content?.text === "string" && (
                    <p className="text-sm text-gray-600">{s.content.text}</p>
                  )}
                  {typeof s.content?.media_asset_id === "string" && (
                    <div className="mt-2">
                      <AuthenticatedImage
                        mediaAssetId={s.content.media_asset_id}
                        alt={typeof s.content.alt === "string" ? s.content.alt : ""}
                        className="max-w-xs rounded border"
                      />
                      {typeof s.content.caption === "string" && (
                        <p className="text-xs text-gray-400 mt-1">{s.content.caption}</p>
                      )}
                    </div>
                  )}
                  {Array.isArray((s.content as any)?.items) && (
                    <ul className="list-disc list-inside text-sm text-gray-600 mt-1">
                      {(s.content as any).items.map((item: string, i: number) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  )}
                </div>
                {canEdit && (
                  <button
                    onClick={() => deleteSection.mutate(s.id)}
                    className="text-xs text-red-500 hover:underline shrink-0"
                  >
                    Delete
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
