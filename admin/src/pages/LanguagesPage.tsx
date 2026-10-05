import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import { useAuth } from "../services/auth";
import { Language, LanguageStatus } from "../types/api";

const STATUS_COLORS: Record<LanguageStatus, string> = {
  ACTIVE: "bg-green-100 text-green-700",
  BETA: "bg-yellow-100 text-yellow-700",
  IN_REVIEW: "bg-blue-100 text-blue-700",
  NOT_STARTED: "bg-gray-100 text-gray-500",
};

const STATUS_OPTIONS: LanguageStatus[] = ["NOT_STARTED", "IN_REVIEW", "BETA", "ACTIVE"];

export default function LanguagesPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ code: "", name: "", native_name: "" });
  const [formError, setFormError] = useState<string | null>(null);

  const canManage = user?.role === "CONTENT_ADMIN" || user?.role === "SUPER_ADMIN";
  const canReview = canManage || user?.role === "LOCALISATION_REVIEWER";

  const { data: languages, isLoading, refetch } = useQuery<Language[]>({
    queryKey: ["languages"],
    queryFn: async () => (await api.get("/languages")).data,
  });

  const createLanguage = useMutation({
    mutationFn: async () => (await api.post("/languages", form)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["languages"] });
      setShowCreate(false);
      setForm({ code: "", name: "", native_name: "" });
      setFormError(null);
    },
    onError: (err: any) => setFormError(err.response?.data?.detail ?? "Failed to create language"),
  });

  const updateStatus = useMutation({
    mutationFn: async ({ id, status }: { id: string; status: LanguageStatus }) =>
      (await api.patch(`/languages/${id}`, { status })).data,
    onSuccess: () => refetch(),
  });

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">Languages</h1>
        {canManage && (
          <button
            onClick={() => setShowCreate((v) => !v)}
            className="bg-gray-900 text-white text-sm rounded px-4 py-2"
          >
            + New language
          </button>
        )}
      </div>

      {showCreate && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createLanguage.mutate();
          }}
          className="bg-white border rounded-lg p-4 mb-6 space-y-3 max-w-md"
        >
          {formError && <p className="text-sm text-red-600">{formError}</p>}
          <div>
            <label className="block text-sm font-medium mb-1">Code (e.g. yo)</label>
            <input
              className="w-full border rounded px-3 py-2"
              value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Name (English)</label>
            <input
              className="w-full border rounded px-3 py-2"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Native name</label>
            <input
              className="w-full border rounded px-3 py-2"
              value={form.native_name}
              onChange={(e) => setForm({ ...form, native_name: e.target.value })}
              required
            />
          </div>
          <button
            type="submit"
            disabled={createLanguage.isPending}
            className="bg-gray-900 text-white text-sm rounded px-4 py-2 disabled:opacity-50"
          >
            {createLanguage.isPending ? "Creating…" : "Create language"}
          </button>
        </form>
      )}

      {isLoading ? (
        <p className="text-sm text-gray-500">Loading…</p>
      ) : (
        <div className="bg-white border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-gray-500">
              <tr>
                <th className="px-4 py-2">Code</th>
                <th className="px-4 py-2">Name</th>
                <th className="px-4 py-2">Native name</th>
                <th className="px-4 py-2">Status</th>
                <th className="px-4 py-2">Default</th>
              </tr>
            </thead>
            <tbody>
              {languages?.map((l) => (
                <tr key={l.id} className="border-t">
                  <td className="px-4 py-2 font-mono">{l.code}</td>
                  <td className="px-4 py-2">{l.name}</td>
                  <td className="px-4 py-2">{l.native_name}</td>
                  <td className="px-4 py-2">
                    {canReview ? (
                      <select
                        className={`text-xs rounded px-2 py-1 border-0 ${STATUS_COLORS[l.status]}`}
                        value={l.status}
                        onChange={(e) =>
                          updateStatus.mutate({ id: l.id, status: e.target.value as LanguageStatus })
                        }
                      >
                        {STATUS_OPTIONS.map((s) => (
                          <option key={s} value={s}>
                            {s}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <span className={`px-2 py-0.5 rounded text-xs ${STATUS_COLORS[l.status]}`}>{l.status}</span>
                    )}
                  </td>
                  <td className="px-4 py-2">{l.is_default ? "Yes" : ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
