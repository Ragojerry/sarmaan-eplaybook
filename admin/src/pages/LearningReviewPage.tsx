import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import { useAuth } from "../services/auth";
import { LEARNER_ROLES, learnerRoleLabel, portalRoleLabel } from "../learnerRoles";
import { ApprovedException, LearningReview } from "../types/api";

function errorText(err: unknown, fallback: string) {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
}

/**
 * Everything about learner roles and pre/post tests that needs a person to
 * decide: modules whose audience nobody has confirmed, accounts whose learner
 * role is unknown, and learners who scored 100% on a pre-test (a strictly
 * higher post-test is impossible, so an approved exception lets a post-test of
 * at least 90% complete the module).
 */
export default function LearningReviewPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const role = user?.role ?? "";
  const isSuper = role === "SUPER_ADMIN";
  const canClassify = isSuper || role === "CONTENT_ADMIN";
  const canApprove = isSuper || role === "CONTENT_ADMIN" || role === "PROGRAM_REVIEWER";
  const [message, setMessage] = useState<{ kind: "error" | "info"; text: string } | null>(null);
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [roleChoice, setRoleChoice] = useState<Record<string, string>>({});

  const review = useQuery<LearningReview>({
    queryKey: ["learning-review"],
    queryFn: async () => (await api.get("/learning/review")).data,
  });
  const approved = useQuery<ApprovedException[]>({
    queryKey: ["learning-exceptions"],
    queryFn: async () => (await api.get("/learning/exceptions")).data,
  });
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["learning-review"] });
    queryClient.invalidateQueries({ queryKey: ["learning-exceptions"] });
  };

  const confirmGeneral = useMutation({
    mutationFn: async (id: string) => (await api.patch(`/modules/${id}`, { audience: "GENERAL" })).data,
    onSuccess: () => {
      setMessage({ kind: "info", text: "Confirmed as General: every learner role sees it." });
      refresh();
    },
    onError: (e) => setMessage({ kind: "error", text: errorText(e, "Could not save.") }),
  });

  const setLearnerRole = useMutation({
    mutationFn: async (v: { id: string; value: string }) =>
      (
        await api.patch(
          `/users/${v.id}`,
          v.value ? { learner_role: v.value } : { clear_learner_role: true, learner_role_reviewed: true },
        )
      ).data,
    onSuccess: () => {
      setMessage({ kind: "info", text: "Saved. Their phone downloads the matching modules at its next sync." });
      refresh();
    },
    onError: (e) => setMessage({ kind: "error", text: errorText(e, "Could not save the learner role.") }),
  });

  const approve = useMutation({
    mutationFn: async (v: { user_id: string; module_id: string; reason: string }) => (await api.post("/learning/exceptions", v)).data,
    onSuccess: (d: { module_completed: boolean }) => {
      setMessage({
        kind: "info",
        text: d.module_completed
          ? "Approved. Their post-test already met 90%, so the module is now complete."
          : "Approved. A post-test of 90% or more will now complete the module.",
      });
      refresh();
    },
    onError: (e) => setMessage({ kind: "error", text: errorText(e, "Could not approve.") }),
  });

  const flagged = review.data?.modules.filter((m) => m.needs_review) ?? [];
  const card = "bg-white border rounded-lg p-4 mb-6";

  return (
    <div className="p-6 max-w-5xl">
      <h1 className="text-xl font-semibold">Roles &amp; tests</h1>
      <p className="text-sm text-gray-500 mt-1 mb-4">
        Learners see General modules plus the modules for their learner role. Each module with questions has a pre-test before
        reading and a post-test after; it is completed, and the next module unlocked, when the post-test scores at least 90% and
        higher than the pre-test.
      </p>
      {message && <p className={`text-sm mb-4 ${message.kind === "error" ? "text-red-600" : "text-green-700"}`}>{message.text}</p>}
      {review.isLoading && <p className="text-sm text-gray-500">Loading…</p>}

      {review.data && (
        <>
          <section className={card}>
            <h2 className="font-medium mb-1">Modules: who sees them ({flagged.length} to confirm)</h2>
            <p className="text-xs text-gray-500 mb-3">
              Modules that existed before roles were introduced stay General (everyone keeps access) until someone confirms or changes
              them. Open a module to make it role-specific.
            </p>
            <table className="w-full text-sm">
              <tbody>
                {review.data.modules.map((m) => (
                  <tr key={m.id} className="border-t">
                    <td className="py-1.5 pr-3 font-mono">{m.module_code}</td>
                    <td className="py-1.5 pr-3">
                      <Link to={`/content/${m.id}`} className="text-blue-600 hover:underline">
                        {m.title}
                      </Link>
                      {m.status !== "PUBLISHED" && <span className="text-xs text-gray-400"> · {m.status.toLowerCase()}</span>}
                    </td>
                    <td className="py-1.5 pr-3 text-gray-600">
                      {m.audience === "GENERAL" ? "General" : m.learner_roles.map(learnerRoleLabel).join(", ")}
                    </td>
                    <td className="py-1.5 text-right whitespace-nowrap">
                      {m.needs_review ? (
                        <>
                          <span className="text-xs bg-amber-100 text-amber-800 rounded px-1.5 py-0.5 mr-2">needs review</span>
                          {canClassify && m.audience === "GENERAL" && (
                            <button
                              className="text-xs underline text-green-700"
                              disabled={confirmGeneral.isPending}
                              onClick={() => confirmGeneral.mutate(m.id)}
                            >
                              Confirm General
                            </button>
                          )}
                        </>
                      ) : (
                        <span className="text-xs text-gray-400">confirmed</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className={card}>
            <h2 className="font-medium mb-1">Accounts to check ({review.data.users_needing_review.length})</h2>
            <p className="text-xs text-gray-500 mb-3">
              Existing accounts whose learner role could not be worked out safely. They keep working; until a learner role is set
              they see General modules only.
              {!isSuper && " Only a super admin can change accounts."}
            </p>
            {review.data.users_needing_review.length === 0 ? (
              <p className="text-sm text-gray-500">Nothing to check.</p>
            ) : (
              <table className="w-full text-sm">
                <tbody>
                  {review.data.users_needing_review.map((u) => (
                    <tr key={u.user_id} className="border-t">
                      <td className="py-1.5 pr-3">
                        {u.full_name}
                        <div className="text-xs text-gray-500">
                          {u.username} · {portalRoleLabel(u.role)}
                        </div>
                      </td>
                      <td className="py-1.5 pr-3 text-xs text-gray-600">{u.reason}</td>
                      <td className="py-1.5 text-right whitespace-nowrap">
                        {isSuper && (
                          <>
                            <select
                              className="border rounded px-1.5 py-0.5 text-sm mr-2"
                              value={roleChoice[u.user_id] ?? ""}
                              onChange={(e) => setRoleChoice({ ...roleChoice, [u.user_id]: e.target.value })}
                            >
                              <option value="">{u.role === "CDD" ? "Choose…" : "Not a learner"}</option>
                              {LEARNER_ROLES.map((r) => (
                                <option key={r.value} value={r.value}>
                                  {r.label}
                                </option>
                              ))}
                            </select>
                            <button
                              className="text-xs underline text-green-700"
                              disabled={u.role === "CDD" && !roleChoice[u.user_id]}
                              onClick={() => setLearnerRole.mutate({ id: u.user_id, value: roleChoice[u.user_id] ?? "" })}
                            >
                              Save
                            </button>
                          </>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>

          <section className={card}>
            <h2 className="font-medium mb-1">100% pre-tests waiting for an exception ({review.data.exceptions_waiting.length})</h2>
            <p className="text-xs text-gray-500 mb-3">
              These learners cannot score higher than 100%, so the rule cannot be met. Approving lets a post-test of at least 90%
              complete the module; the 90% pass mark is never waived. Every approval is recorded in the audit log.
              {!canApprove && " Content admins and programme reviewers can approve."}
            </p>
            {review.data.exceptions_waiting.length === 0 ? (
              <p className="text-sm text-gray-500">Nobody is waiting.</p>
            ) : (
              <div className="space-y-3">
                {review.data.exceptions_waiting.map((w) => {
                  const k = `${w.user_id}:${w.module_id}`;
                  const reason = reasons[k] ?? "";
                  return (
                    <div key={k} className="border rounded p-3 text-sm">
                      <div>
                        <strong>{w.full_name}</strong> ({learnerRoleLabel(w.learner_role)}, team {w.team_code ?? "—"}) scored{" "}
                        {w.pre_test_score}% on the {w.module_code} pre-test ({new Date(w.pre_test_taken_at).toLocaleDateString()}).
                      </div>
                      {canApprove && (
                        <div className="flex items-center gap-2 mt-2">
                          <input
                            className="flex-1 border rounded px-2 py-1"
                            placeholder="Reason (e.g. confirmed prior training with the supervisor)"
                            value={reason}
                            onChange={(e) => setReasons({ ...reasons, [k]: e.target.value })}
                          />
                          <button
                            className="bg-gray-900 text-white rounded px-3 py-1 disabled:opacity-50"
                            disabled={reason.trim().length < 5 || approve.isPending}
                            onClick={() => approve.mutate({ user_id: w.user_id, module_id: w.module_id, reason: reason.trim() })}
                          >
                            Approve exception
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </section>
        </>
      )}

      <section className={card}>
        <h2 className="font-medium mb-3">Approved exceptions</h2>
        {approved.data?.length ? (
          <table className="w-full text-sm">
            <tbody>
              {approved.data.map((e, i) => (
                <tr key={i} className="border-t">
                  <td className="py-1.5 pr-3">
                    {e.full_name}
                    <div className="text-xs text-gray-500">{e.username}</div>
                  </td>
                  <td className="py-1.5 pr-3">{e.module_code}</td>
                  <td className="py-1.5 pr-3 text-xs text-gray-600">{e.reason}</td>
                  <td className="py-1.5 text-xs text-gray-500 whitespace-nowrap">
                    {e.approved_by} · {e.approved_at ? new Date(e.approved_at).toLocaleDateString() : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-sm text-gray-500">None yet.</p>
        )}
      </section>
    </div>
  );
}
