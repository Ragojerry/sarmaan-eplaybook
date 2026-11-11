import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import { useAuth } from "../services/auth";
import { Module } from "../types/api";
import { LEARNER_ROLES, learnerRoleLabel } from "../learnerRoles";

const STATUS_COLORS: Record<string, string> = {
  DRAFT: "bg-gray-100 text-gray-700",
  PUBLISHED: "bg-green-100 text-green-700",
  ARCHIVED: "bg-yellow-100 text-yellow-700",
};

export default function ContentPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ module_code: "", module_number: "", title: "" });
  const [formError, setFormError] = useState<string | null>(null);
  // "" = every module; "GENERAL" = general modules only; a learner role = what that role sees
  const [audienceFilter, setAudienceFilter] = useState("");

  const canEdit = user?.role === "CONTENT_ADMIN" || user?.role === "SUPER_ADMIN";

  const { data: modules, isLoading } = useQuery<Module[]>({
    queryKey: ["modules"],
    queryFn: async () => (await api.get("/modules")).data,
  });

  const createModule = useMutation({
    mutationFn: async () =>
      (
        await api.post("/modules", {
          module_code: form.module_code,
          module_number: Number(form.module_number),
          title: form.title,
        })
      ).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["modules"] });
      setShowCreate(false);
      setForm({ module_code: "", module_number: "", title: "" });
      setFormError(null);
    },
    onError: (err: any) => setFormError(err.response?.data?.detail ?? "Failed to create module"),
  });

  const shown = (modules ?? []).filter((m) => {
    if (!audienceFilter) return true;
    if (audienceFilter === "GENERAL") return m.audience === "GENERAL";
    return m.audience === "GENERAL" || m.learner_roles.includes(audienceFilter as Module["learner_roles"][number]);
  });

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">Content — Modules</h1>
        {canEdit && (
          <button
            onClick={() => setShowCreate((v) => !v)}
            className="bg-gray-900 text-white text-sm rounded px-4 py-2"
          >
            + New module
          </button>
        )}
      </div>

      {showCreate && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createModule.mutate();
          }}
          className="bg-white border rounded-lg p-4 mb-6 space-y-3 max-w-md"
        >
          {formError && <p className="text-sm text-red-600">{formError}</p>}
          <div>
            <label className="block text-sm font-medium mb-1">Module code (e.g. M7)</label>
            <input
              className="w-full border rounded px-3 py-2"
              value={form.module_code}
              onChange={(e) => setForm({ ...form, module_code: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Module number</label>
            <input
              type="number"
              className="w-full border rounded px-3 py-2"
              value={form.module_number}
              onChange={(e) => setForm({ ...form, module_number: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Title</label>
            <input
              className="w-full border rounded px-3 py-2"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              required
            />
          </div>
          <button
            type="submit"
            disabled={createModule.isPending}
            className="bg-gray-900 text-white text-sm rounded px-4 py-2 disabled:opacity-50"
          >
            {createModule.isPending ? "Creating…" : "Create module"}
          </button>
        </form>
      )}

      {isLoading ? (
        <p className="text-sm text-gray-500">Loading modules…</p>
      ) : !modules || modules.length === 0 ? (
        <p className="text-sm text-gray-500">No modules yet.</p>
      ) : (
        <>
        <div className="mb-3 flex items-center gap-2 text-sm">
          <label htmlFor="audience-filter" className="text-gray-600">Show modules for</label>
          <select
            id="audience-filter"
            className="border rounded px-2 py-1"
            value={audienceFilter}
            onChange={(e) => setAudienceFilter(e.target.value)}
          >
            <option value="">Everyone (all modules)</option>
            <option value="GENERAL">General modules only</option>
            {LEARNER_ROLES.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label} learners
              </option>
            ))}
          </select>
          <span className="text-gray-500">
            {shown.length} of {modules.length}
          </span>
        </div>
        <div className="bg-white border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-gray-500">
              <tr>
                <th className="px-4 py-2">Code</th>
                <th className="px-4 py-2">Title</th>
                <th className="px-4 py-2">Status</th>
                <th className="px-4 py-2">Who sees it</th>
                <th className="px-4 py-2">Order</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((m) => (
                <tr key={m.id} className="border-t hover:bg-gray-50">
                  <td className="px-4 py-2 font-mono">{m.module_code}</td>
                  <td className="px-4 py-2">
                    <Link to={`/content/${m.id}`} className="text-blue-600 hover:underline">
                      {m.title}
                    </Link>
                  </td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-0.5 rounded text-xs ${STATUS_COLORS[m.status]}`}>{m.status}</span>
                  </td>
                  <td className="px-4 py-2 text-xs text-gray-600">
                    {m.audience === "ROLE_SPECIFIC" ? m.learner_roles.map(learnerRoleLabel).join(", ") : "General"}
                    {m.audience_needs_review && (
                      <span className="ml-2 bg-amber-100 text-amber-800 rounded px-1.5 py-0.5">needs review</span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-gray-500">{m.sort_order}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        </>
      )}
    </div>
  );
}
