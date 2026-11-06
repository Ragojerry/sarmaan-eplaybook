import { Fragment, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../services/api";
import { learnerRoleLabel } from "../learnerRoles";
import { TestReportRow } from "../types/api";

const STATUS_LABELS: Record<string, string> = {
  LOCKED: "Locked (earlier module not done)",
  PRE_TEST: "Pre-test not taken",
  READING: "Reading",
  POST_TEST: "Post-test not passed yet",
  COMPLETED: "Completed",
};

type Attempt = {
  module_code: string;
  test_type: "PRE" | "POST";
  score_percent: number;
  correct: number;
  total: number;
  valid: boolean;
  invalid_reason: string | null;
  taken_at: string;
};

function pct(v: number | null) {
  return v === null ? "—" : `${v}%`;
}

/** Every attempt one learner made in one module, pre and post, counted or not. */
function Attempts({ userId, moduleCode }: { userId: string; moduleCode: string }) {
  const q = useQuery<Attempt[]>({
    queryKey: ["learner-attempts", userId],
    queryFn: async () => (await api.get(`/learning/attempts/${userId}`)).data,
  });
  const rows = q.data?.filter((a) => a.module_code === moduleCode) ?? [];
  if (q.isLoading) return <p className="text-xs text-gray-500">Loading…</p>;
  if (rows.length === 0) return <p className="text-xs text-gray-500">No attempts yet.</p>;
  return (
    <table className="text-xs">
      <tbody>
        {rows.map((a, i) => (
          <tr key={i} className={a.valid ? "" : "text-gray-400"}>
            <td className="pr-4">{new Date(a.taken_at).toLocaleString()}</td>
            <td className="pr-4">{a.test_type === "PRE" ? "Pre-test" : "Post-test"}</td>
            <td className="pr-4">
              {a.score_percent}% ({a.correct}/{a.total})
            </td>
            <td>{a.valid ? "counted" : `not counted: ${a.invalid_reason}`}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** Pre-test and post-test results per learner and module, kept apart. */
export default function TestReport({
  params,
  onDownload,
}: {
  params: Record<string, string | boolean>;
  onDownload: () => void;
}) {
  const [open, setOpen] = useState<string | null>(null);
  const report = useQuery<TestReportRow[]>({
    queryKey: ["learning-report", JSON.stringify(params)],
    queryFn: async () => (await api.get("/learning/report", { params })).data,
  });
  return (
    <>
      <div className="flex items-center gap-3 mb-3">
        <button className="border bg-white text-sm rounded px-3 py-1.5" onClick={onDownload}>
          Export CSV
        </button>
        <span className="text-xs text-gray-500">
          A module is completed when the post-test scores at least the pass mark and higher than the pre-test; after a 100%
          pre-test, a post-test at the auto-approval threshold completes it automatically. "Credited" completions were given
          because the learner completed the older module with the same content. Click a row for every attempt.
        </span>
      </div>
      <div className="bg-white border rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs text-gray-500">
            <tr>
              {["Name", "Learner role", "Team", "Module", "Status", "Pre-test", "Post-test attempts", "Best post-test", "Latest post-test", "Completed by rule", "Auto-approved", "Completed how", "Not counted"].map((h) => (
                <th key={h} className="px-3 py-2 whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {report.isLoading && (
              <tr>
                <td colSpan={13} className="px-3 py-4 text-gray-500">
                  Loading…
                </td>
              </tr>
            )}
            {report.data?.length === 0 && (
              <tr>
                <td colSpan={13} className="px-3 py-4 text-gray-500">
                  No learners or modules with tests match these filters.
                </td>
              </tr>
            )}
            {report.data?.map((r) => {
              const key = `${r.user_id}-${r.module_code}`;
              return (
                <Fragment key={key}>
                  <tr className="border-t cursor-pointer hover:bg-gray-50" onClick={() => setOpen(open === key ? null : key)}>
                    <td className="px-3 py-1.5 whitespace-nowrap">
                      {r.full_name}
                      <div className="text-xs text-gray-500">{r.username}</div>
                    </td>
                    <td className="px-3 py-1.5 whitespace-nowrap">{learnerRoleLabel(r.learner_role)}</td>
                    <td className="px-3 py-1.5">{r.team_code ?? "—"}</td>
                    <td className="px-3 py-1.5 whitespace-nowrap">{r.module_code}</td>
                    <td className="px-3 py-1.5 whitespace-nowrap">{STATUS_LABELS[r.status] ?? r.status}</td>
                    <td className="px-3 py-1.5 whitespace-nowrap">
                      {pct(r.pre_test_score)}
                      {r.pre_test_correct && <span className="text-xs text-gray-500"> ({r.pre_test_correct})</span>}
                    </td>
                    <td className="px-3 py-1.5">{r.post_test_attempts}</td>
                    <td className="px-3 py-1.5">{pct(r.post_test_best_score)}</td>
                    <td className="px-3 py-1.5">{pct(r.post_test_latest_score)}</td>
                    <td className="px-3 py-1.5">{r.met_both_rules ? "yes" : "no"}</td>
                    <td className="px-3 py-1.5">{r.auto_approved ? "yes (100% pre-test)" : "—"}</td>
                    <td className="px-3 py-1.5 whitespace-nowrap">
                      {r.completion_source === "credited"
                        ? `credited from ${r.credited_from}${r.credited_score !== null ? ` (${r.credited_score}%)` : ""}`
                        : r.completion_source === "earned"
                          ? "earned"
                          : "—"}
                    </td>
                    <td className="px-3 py-1.5">{r.attempts_not_counted || "—"}</td>
                  </tr>
                  {open === key && (
                    <tr className="bg-gray-50">
                      <td colSpan={13} className="px-6 py-2">
                        <Attempts userId={r.user_id} moduleCode={r.module_code} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
