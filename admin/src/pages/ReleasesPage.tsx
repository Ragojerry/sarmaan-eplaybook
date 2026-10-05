import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import { useAuth } from "../services/auth";
import { ContentRelease, ReleaseStatus } from "../types/api";

const STATUS_COLORS: Record<ReleaseStatus, string> = {
  DRAFT: "bg-gray-100 text-gray-700",
  IN_REVIEW: "bg-blue-100 text-blue-700",
  APPROVED: "bg-yellow-100 text-yellow-700",
  PUBLISHED: "bg-green-100 text-green-700",
  ROLLED_BACK: "bg-red-100 text-red-700",
};

export default function ReleasesPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ release_code: "", version: "", description: "" });
  const [formError, setFormError] = useState<string | null>(null);

  const canCreate = user?.role === "CONTENT_ADMIN" || user?.role === "TECHNICAL_REVIEWER" || user?.role === "SUPER_ADMIN";
  const canPublish = user?.role === "TECHNICAL_REVIEWER" || user?.role === "SUPER_ADMIN";

  const { data: releases, isLoading, refetch } = useQuery<ContentRelease[]>({
    queryKey: ["releases"],
    queryFn: async () => (await api.get("/releases")).data,
  });

  const createRelease = useMutation({
    mutationFn: async () => (await api.post("/releases", form)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["releases"] });
      setShowCreate(false);
      setForm({ release_code: "", version: "", description: "" });
      setFormError(null);
    },
    onError: (err: any) => setFormError(err.response?.data?.detail ?? "Failed to create release"),
  });

  const publish = useMutation({
    mutationFn: async (id: string) => (await api.post(`/releases/${id}/publish`)).data,
    onSuccess: () => refetch(),
  });

  const rollback = useMutation({
    mutationFn: async (id: string) => (await api.post(`/releases/${id}/rollback`)).data,
    onSuccess: () => refetch(),
  });

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">Releases</h1>
        {canCreate && (
          <button
            onClick={() => setShowCreate((v) => !v)}
            className="bg-gray-900 text-white text-sm rounded px-4 py-2"
          >
            + New release
          </button>
        )}
      </div>

      {showCreate && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createRelease.mutate();
          }}
          className="bg-white border rounded-lg p-4 mb-6 space-y-3 max-w-md"
        >
          {formError && <p className="text-sm text-red-600">{formError}</p>}
          <div>
            <label className="block text-sm font-medium mb-1">Release code</label>
            <input
              className="w-full border rounded px-3 py-2"
              placeholder="AZM-MDA-2026.09-R03"
              value={form.release_code}
              onChange={(e) => setForm({ ...form, release_code: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Version</label>
            <input
              className="w-full border rounded px-3 py-2"
              placeholder="1.0.0"
              value={form.version}
              onChange={(e) => setForm({ ...form, version: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Description</label>
            <textarea
              className="w-full border rounded px-3 py-2"
              rows={2}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>
          <button
            type="submit"
            disabled={createRelease.isPending}
            className="bg-gray-900 text-white text-sm rounded px-4 py-2 disabled:opacity-50"
          >
            {createRelease.isPending ? "Creating…" : "Create release"}
          </button>
        </form>
      )}

      {isLoading ? (
        <p className="text-sm text-gray-500">Loading…</p>
      ) : !releases || releases.length === 0 ? (
        <p className="text-sm text-gray-500">No releases yet.</p>
      ) : (
        <div className="bg-white border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-gray-500">
              <tr>
                <th className="px-4 py-2">Release code</th>
                <th className="px-4 py-2">Version</th>
                <th className="px-4 py-2">Status</th>
                <th className="px-4 py-2">Mandatory</th>
                <th className="px-4 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {releases.map((r) => (
                <tr key={r.id} className="border-t">
                  <td className="px-4 py-2 font-mono">{r.release_code}</td>
                  <td className="px-4 py-2">{r.version}</td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-0.5 rounded text-xs ${STATUS_COLORS[r.status]}`}>{r.status}</span>
                  </td>
                  <td className="px-4 py-2">{r.mandatory ? "Yes" : "No"}</td>
                  <td className="px-4 py-2 text-right">
                    {canPublish && r.status !== "PUBLISHED" && r.status !== "ROLLED_BACK" && (
                      <button
                        onClick={() => publish.mutate(r.id)}
                        className="text-xs bg-green-600 text-white rounded px-2 py-1 mr-2"
                      >
                        Publish
                      </button>
                    )}
                    {canPublish && r.status === "PUBLISHED" && (
                      <button
                        onClick={() => rollback.mutate(r.id)}
                        className="text-xs bg-red-600 text-white rounded px-2 py-1"
                      >
                        Rollback
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
