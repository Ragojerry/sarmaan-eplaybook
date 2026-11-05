import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import { useAuth } from "../services/auth";
import { LEARNER_ROLES, learnerRoleLabel, portalRoleLabel } from "../learnerRoles";
import { LearningReview } from "../types/api";

function errorText(err: unknown, fallback: string) {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
}

/**
 * Everything about learner roles and pre/post tests that needs a person to
 * decide: modules whose audience nobody has confirmed, accounts whose learner
 * role is unknown. It also shows the automatic approval of 100% pre-tests.
 */
export default function LearningReviewPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const role = user?.role ?? "";
  const isSuper = role === "SUPER_ADMIN";
  const canClassify = isSuper || role === "CONTENT_ADMIN";
  const [message, setMessage] = useState<{ kind: "error" | "info"; text: string } | null>(null);
  const [roleChoice, setRoleChoice] = useState<Record<string, string>>({});

  const review = useQuery<LearningReview>({
    queryKey: ["learning-review"],
    queryFn: async () => (await api.get("/learning/review")).data,
  });
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["learning-review"] });

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
            <h2 className="font-medium mb-1">100% pre-tests: automatic approval</h2>
            <p className="text-xs text-gray-500">
              A learner who scores 100% on a pre-test cannot score higher on the post-test. A post-test of at least{" "}
              <strong>{review.data.auto_approve_percent}%</strong> completes the module for them at once, with no approval step.
              The threshold is the server setting <code>POST_TEST_AUTO_APPROVE_PERCENT</code>.
            </p>
          </section>
        </>
      )}
    </div>
  );
}
