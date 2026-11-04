import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "../services/api";
import { LEARNER_ROLES, learnerRoleLabel } from "../learnerRoles";
import { LearnerRole, Module, ModuleAudience } from "../types/api";

/** Who sees a module on the phone: every learner (General) or only the chosen
 *  learner roles (Role-specific). The server enforces it on every download,
 *  search and quiz; saving also confirms a module flagged "needs review".
 *  A change reaches phones' offline copies with the next published release. */
export default function ModuleAudienceEditor({
  module,
  canEdit,
  onSaved,
}: {
  module: Module;
  canEdit: boolean;
  onSaved: () => void;
}) {
  const [audience, setAudience] = useState<ModuleAudience>(module.audience);
  const [roles, setRoles] = useState<LearnerRole[]>(module.learner_roles ?? []);
  const [error, setError] = useState<string | null>(null);

  const save = useMutation({
    mutationFn: async () =>
      (await api.patch(`/modules/${module.id}`, { audience, learner_roles: audience === "GENERAL" ? [] : roles })).data,
    onSuccess: () => {
      setError(null);
      onSaved();
    },
    onError: (e: any) => setError(e?.response?.data?.detail ?? "Could not save the audience."),
  });

  const summary =
    module.audience === "GENERAL"
      ? "General: every learner role"
      : `Role-specific: ${module.learner_roles.map(learnerRoleLabel).join(", ")}`;

  return (
    <div className="bg-white border rounded-lg p-4 mb-6 max-w-2xl text-sm">
      <div className="flex items-center gap-2 mb-2">
        <h2 className="font-medium">Who sees this module</h2>
        {module.audience_needs_review && (
          <span className="text-xs bg-amber-100 text-amber-800 rounded px-1.5 py-0.5">needs review</span>
        )}
      </div>
      {!canEdit ? (
        <p className="text-gray-700">{summary}</p>
      ) : (
        <form
          className="space-y-3"
          onSubmit={(e) => {
            e.preventDefault();
            save.mutate();
          }}
        >
          <div className="flex gap-6">
            {(
              [
                ["GENERAL", "General (every learner role)"],
                ["ROLE_SPECIFIC", "Role-specific"],
              ] as const
            ).map(([value, label]) => (
              <label key={value} className="flex items-center gap-2">
                <input type="radio" checked={audience === value} onChange={() => setAudience(value)} />
                {label}
              </label>
            ))}
          </div>
          {audience === "ROLE_SPECIFIC" && (
            <div className="flex flex-wrap gap-4 pl-1">
              {LEARNER_ROLES.map((r) => (
                <label key={r.value} className="flex items-center gap-1.5">
                  <input
                    type="checkbox"
                    checked={roles.includes(r.value)}
                    onChange={(e) =>
                      setRoles(e.target.checked ? [...roles, r.value] : roles.filter((x) => x !== r.value))
                    }
                  />
                  {r.label}
                </label>
              ))}
            </div>
          )}
          {error && <p className="text-red-600 text-xs">{error}</p>}
          <div className="flex items-center gap-3">
            <button
              disabled={save.isPending || (audience === "ROLE_SPECIFIC" && roles.length === 0)}
              className="bg-gray-900 text-white rounded px-4 py-1.5 disabled:opacity-50"
            >
              {save.isPending ? "Saving…" : module.audience_needs_review ? "Confirm audience" : "Save audience"}
            </button>
            <span className="text-xs text-gray-500">
              Learners without the role cannot open, search or download it. Offline copies update with the next release.
            </span>
          </div>
        </form>
      )}
    </div>
  );
}
