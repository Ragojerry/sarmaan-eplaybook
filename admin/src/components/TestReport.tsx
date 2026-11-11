import { Fragment, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../services/api";
import { learnerRoleLabel } from "../learnerRoles";
import { GeneralReportRow, TestReportRow } from "../types/api";

const STATUS_LABELS: Record<string, string> = {
  LOCKED: "Locked",
  READING: "Open",
  COMPLETED: "Completed",
};

const TEST_LABELS: Record<string, string> = {
  MODULE_QUIZ: "Module quiz",
  PRE: "Pre-test",
  POST: "Post-test",
};

type Attempt = {
  module_code: string;
  test_type: "PRE" | "POST" | "MODULE_QUIZ";
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

function minutes(seconds: number) {
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

/** Every attempt one learner made in one module (or the General test), counted or not. */
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
            <td className="pr-4">
              {TEST_LABELS[a.test_type] ?? a.test_type}
              {a.module_code !== "GENERAL" && a.test_type !== "MODULE_QUIZ" ? " (retired per-module test)" : ""}
            </td>
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

function Head({ cols }: { cols: string[] }) {
  return (
    <thead className="bg-gray-50 text-left text-xs text-gray-500">
      <tr>
        {cols.map((h) => (
          <th key={h} className="px-3 py-2 whitespace-nowrap">
            {h}
          </th>
        ))}
      </tr>
    </thead>
  );
}

function Message({ span, text }: { span: number; text: string }) {
  return (
    <tr>
      <td colSpan={span} className="px-3 py-4 text-gray-500">
        {text}
      </td>
    </tr>
  );
}

/** The General pre/post test per learner, and the inline module quiz and time per learner
 * and module. CDD and HFW (and others) can be shown separately. */
export default function TestReport({
  params,
  onDownload,
}: {
  params: Record<string, string | boolean>;
  onDownload: (path: string, filename: string) => void;
}) {
  const [open, setOpen] = useState<string | null>(null);
  const [group, setGroup] = useState<"" | "CDD" | "HFW">("");
  const general = useQuery<GeneralReportRow[]>({
    queryKey: ["general-report", JSON.stringify(params)],
    queryFn: async () => (await api.get("/learning/general-report", { params })).data,
  });
  const report = useQuery<TestReportRow[]>({
    queryKey: ["learning-report", JSON.stringify(params)],
    queryFn: async () => (await api.get("/learning/report", { params })).data,
  });
  const inGroup = (learnerGroup: string) =>
    !group || (group === "CDD" ? learnerGroup === "CDD" : learnerGroup !== "CDD");
  const generalRows = general.data?.filter((r) => inGroup(r.learner_group));
  const moduleRows = report.data?.filter((r) => inGroup(r.learner_group));

  const GENERAL_COLS = ["Name", "Learner role", "Team", "Modules done", "Time in modules", "Pre-test", "Post-test", "Change", "Not counted"];
  const MODULE_COLS = ["Name", "Learner role", "Module", "Status", "Quiz", "Quiz attempts", "Time", "Completed", "Old pre/post (history)"];

  return (
    <>
      <div className="flex flex-wrap items-center gap-3 mb-3">
        <label className="text-sm">
          Learners{" "}
          <select className="border rounded px-2 py-1 text-sm" value={group} onChange={(e) => setGroup(e.target.value as "" | "CDD" | "HFW")}>
            <option value="">All</option>
            <option value="CDD">CDD</option>
            <option value="HFW">HFW &amp; others</option>
          </select>
        </label>
        <button className="border bg-white text-sm rounded px-3 py-1.5" onClick={() => onDownload("/learning/general-report.csv", "general_test.csv")}>
          Export General test CSV
        </button>
        <button className="border bg-white text-sm rounded px-3 py-1.5" onClick={() => onDownload("/learning/report.csv", "module_learning.csv")}>
          Export modules CSV
        </button>
      </div>

      <h3 className="text-sm font-medium mb-1">General test (before and after the training)</h3>
      <p className="text-xs text-gray-500 mb-2">
        The same questions, taken once before any module and once after all of them. Points out of the number of questions; no
        pass mark. Click a row for every attempt.
      </p>
      <div className="bg-white border rounded-lg overflow-x-auto mb-6">
        <table className="w-full text-sm">
          <Head cols={GENERAL_COLS} />
          <tbody>
            {general.isLoading && <Message span={GENERAL_COLS.length} text="Loading…" />}
            {generalRows?.length === 0 && <Message span={GENERAL_COLS.length} text="No learners match these filters." />}
            {generalRows?.map((r) => {
              const key = `${r.user_id}-GENERAL`;
              return (
                <Fragment key={key}>
                  <tr className="border-t cursor-pointer hover:bg-gray-50" onClick={() => setOpen(open === key ? null : key)}>
                    <td className="px-3 py-1.5 whitespace-nowrap">
                      {r.full_name}
                      <div className="text-xs text-gray-500">{r.username}</div>
                    </td>
                    <td className="px-3 py-1.5 whitespace-nowrap">{learnerRoleLabel(r.learner_role)}</td>
                    <td className="px-3 py-1.5">{r.team_code ?? "—"}</td>
                    <td className="px-3 py-1.5">
                      {r.modules_completed} / {r.modules_total}
                    </td>
                    <td className="px-3 py-1.5">{minutes(r.seconds_spent_total)}</td>
                    <td className="px-3 py-1.5 whitespace-nowrap">
                      {r.pre_test_points === null ? "—" : `${r.pre_test_points}/${r.pre_test_total} (${pct(r.pre_test_percent)})`}
                    </td>
                    <td className="px-3 py-1.5 whitespace-nowrap">
                      {r.post_test_points === null ? "—" : `${r.post_test_points}/${r.post_test_total} (${pct(r.post_test_percent)})`}
                    </td>
                    <td className="px-3 py-1.5">{r.change_points === null ? "—" : `${r.change_points > 0 ? "+" : ""}${r.change_points}`}</td>
                    <td className="px-3 py-1.5">{r.attempts_not_counted || "—"}</td>
                  </tr>
                  {open === key && (
                    <tr className="bg-gray-50">
                      <td colSpan={GENERAL_COLS.length} className="px-6 py-2">
                        <Attempts userId={r.user_id} moduleCode="GENERAL" />
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>

      <h3 className="text-sm font-medium mb-1">Modules: quiz and time</h3>
      <p className="text-xs text-gray-500 mb-2">
        A module is completed when its inline True/False quiz is passed (90%: with three statements, all three) and the minimum
        time is reached. The last column shows the retired per-module pre/post tests, kept as history.
      </p>
      <div className="bg-white border rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <Head cols={MODULE_COLS} />
          <tbody>
            {report.isLoading && <Message span={MODULE_COLS.length} text="Loading…" />}
            {moduleRows?.length === 0 && <Message span={MODULE_COLS.length} text="No learners or modules match these filters." />}
            {moduleRows?.map((r) => {
              const key = `${r.user_id}-${r.module_code}`;
              return (
                <Fragment key={key}>
                  <tr className="border-t cursor-pointer hover:bg-gray-50" onClick={() => setOpen(open === key ? null : key)}>
                    <td className="px-3 py-1.5 whitespace-nowrap">
                      {r.full_name}
                      <div className="text-xs text-gray-500">{r.username}</div>
                    </td>
                    <td className="px-3 py-1.5 whitespace-nowrap">{learnerRoleLabel(r.learner_role)}</td>
                    <td className="px-3 py-1.5 whitespace-nowrap">
                      {r.module_code}
                      <span className="text-xs text-gray-400"> · {r.curriculum}</span>
                    </td>
                    <td className="px-3 py-1.5 whitespace-nowrap">{STATUS_LABELS[r.status] ?? r.status}</td>
                    <td className="px-3 py-1.5 whitespace-nowrap">
                      {r.quiz_statements === 0 ? "no quiz" : r.quiz_passed ? "passed" : r.quiz_attempts ? `not yet (${pct(r.quiz_latest_score)})` : "not taken"}
                    </td>
                    <td className="px-3 py-1.5">{r.quiz_attempts}</td>
                    <td className="px-3 py-1.5 whitespace-nowrap">
                      {minutes(r.seconds_spent)} / {minutes(r.min_seconds)}
                    </td>
                    <td className="px-3 py-1.5 whitespace-nowrap">{r.completed_at ? new Date(r.completed_at).toLocaleDateString() : "—"}</td>
                    <td className="px-3 py-1.5 whitespace-nowrap text-xs text-gray-500">
                      {r.pre_test_score === null && r.post_test_best_score === null
                        ? "—"
                        : `pre ${pct(r.pre_test_score)} · best post ${pct(r.post_test_best_score)}`}
                    </td>
                  </tr>
                  {open === key && (
                    <tr className="bg-gray-50">
                      <td colSpan={MODULE_COLS.length} className="px-6 py-2">
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
