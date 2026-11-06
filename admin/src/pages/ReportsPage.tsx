import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../services/api";
import { useAuth } from "../services/auth";
import { ReportRow, TrainingSession } from "../types/api";
import AreaPicker, { areaParams, AreaValue } from "../components/AreaPicker";
import BiAccess from "../components/BiAccess";
import TestReport from "../components/TestReport";
import { LEARNER_ROLES } from "../learnerRoles";

type Tab = "session" | "area" | "user" | "module" | "tests" | "bi";
const AREA_LEVELS = ["country", "state", "lga", "ward", "facility"];

const SESSION_COLS: [string, string][] = [
  ["session", "Session"], ["start_date", "Start"], ["end_date", "End"], ["status", "Status"], ["days_remaining", "Days left"],
  ["users", "People"], ["not_started", "Not started"], ["active_users_30d", "Active (30d)"], ["avg_completion_rate", "Avg completion %"],
  ["users_completed_all", "Finished all"], ["completed_all_by_end_date", "Finished by end date"], ["modules_completed", "Modules done"], ["modules_completed_credited", "Of which credited"],
  ["quizzes_passed", "Quizzes passed"], ["avg_best_quiz_score", "Avg quiz %"], ["training_events", "Training"], ["video_events", "Video"],
  ["questions_asked", "Q&A"], ["technical_events", "Technical"],
];
const AREA_COLS: [string, string][] = [
  ["area", "Area"], ["users", "Users"], ["active_users_30d", "Active (30d)"], ["avg_completion_rate", "Avg completion %"],
  ["users_completed_all", "Finished all"], ["modules_completed", "Modules done"], ["modules_completed_credited", "Of which credited"], ["quizzes_passed", "Quizzes passed"],
  ["avg_best_quiz_score", "Avg quiz %"], ["training_events", "Training"], ["video_events", "Video"],
  ["questions_asked", "Q&A"], ["technical_events", "Technical"], ["session_events", "Sessions"],
];
const USER_COLS: [string, string][] = [
  ["full_name", "Name"], ["username", "Username"], ["learner_role", "Learner role"], ["team_code", "Team"], ["session", "Session"], ["training_attempt", "Attempt"], ["state", "State"], ["lga", "LGA"], ["ward", "Ward"],
  ["facility", "Facility"], ["modules_completed", "Done"], ["modules_completed_credited", "Credited"], ["completion_rate", "Completion %"], ["quizzes_passed", "Quizzes passed"],
  ["avg_best_quiz_score", "Avg quiz %"], ["training_events", "Training"], ["video_events", "Video"], ["questions_asked", "Q&A"],
  ["technical_events", "Technical"], ["last_activity", "Last activity"],
];
const MODULE_COLS: [string, string][] = [
  ["module_code", "Module"], ["module_title", "Title"], ["area", "Area"], ["users", "Users"], ["started", "Started"],
  ["completed", "Completed"], ["completed_credited", "Of which credited"], ["completion_rate", "Completion %"], ["quiz_takers", "Quiz takers"], ["quiz_passed", "Quiz passed"],
  ["avg_best_quiz_score", "Avg quiz %"],
];

function cell(key: string, v: string | number | null | undefined) {
  if (v === null || v === undefined || v === "") return "—";
  if (key === "last_activity" && typeof v === "string") return new Date(v).toLocaleDateString();
  return String(v);
}

function Table({ rows, cols, loading }: { rows: ReportRow[] | undefined; cols: [string, string][]; loading: boolean }) {
  return (
    <div className="bg-white border rounded-lg overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-left text-xs text-gray-500">
          <tr>
            {cols.map(([k, label]) => (
              <th key={k} className="px-3 py-2 whitespace-nowrap">
                {label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading && (
            <tr>
              <td colSpan={cols.length} className="px-3 py-4 text-gray-500">
                Loading…
              </td>
            </tr>
          )}
          {!loading && rows?.length === 0 && (
            <tr>
              <td colSpan={cols.length} className="px-3 py-4 text-gray-500">
                Nothing matches these filters.
              </td>
            </tr>
          )}
          {rows?.map((r, i) => (
            <tr key={i} className="border-t">
              {cols.map(([k]) => (
                <td key={k} className="px-3 py-1.5 whitespace-nowrap">
                  {cell(k, r[k])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Card({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-white border rounded-lg px-4 py-3">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-xl font-semibold">{value}</div>
    </div>
  );
}

/** User activity by person, area and module, with CSV export and Power BI access. */
export default function ReportsPage() {
  const { user } = useAuth();
  const isSuper = user?.role === "SUPER_ADMIN";
  const [searchParams] = useSearchParams();
  const [tab, setTab] = useState<Tab>(searchParams.get("session") ? "session" : "area");
  const [sessionId, setSessionId] = useState(searchParams.get("session") ?? "");
  const sessionList = useQuery<TrainingSession[]>({
    queryKey: ["sessions"],
    queryFn: async () => (await api.get("/sessions")).data,
  });
  const [area, setArea] = useState<AreaValue>({});
  const [level, setLevel] = useState("state");
  const [modLevel, setModLevel] = useState("");
  const [dates, setDates] = useState({ date_from: "", date_to: "" });
  const [team, setTeam] = useState("");
  const [allRoles, setAllRoles] = useState(false);
  const [learnerRole, setLearnerRole] = useState("");
  const [error, setError] = useState<string | null>(null);

  const params: Record<string, string | boolean> = {
    ...areaParams(area),
    ...(sessionId ? { session_id: sessionId } : {}),
    ...(dates.date_from ? { date_from: dates.date_from } : {}),
    ...(dates.date_to ? { date_to: dates.date_to } : {}),
    ...(team ? { team_code: team } : {}),
    ...(allRoles ? { all_roles: true } : {}),
    ...(learnerRole ? { learner_role: learnerRole } : {}),
  };
  const key = JSON.stringify(params);

  const summary = useQuery<Record<string, number>>({
    queryKey: ["rep-summary", key],
    queryFn: async () => (await api.get("/reports/summary", { params })).data,
    enabled: tab !== "bi",
  });
  const bySession = useQuery<ReportRow[]>({
    queryKey: ["rep-session", key],
    queryFn: async () => (await api.get("/reports/sessions", { params })).data,
    enabled: tab === "session",
  });
  const byArea = useQuery<ReportRow[]>({
    queryKey: ["rep-area", key, level],
    queryFn: async () => (await api.get("/reports/boundaries", { params: { ...params, level } })).data,
    enabled: tab === "area",
  });
  const byUser = useQuery<ReportRow[]>({
    queryKey: ["rep-user", key],
    queryFn: async () => (await api.get("/reports/users", { params })).data,
    enabled: tab === "user",
  });
  const byModule = useQuery<ReportRow[]>({
    queryKey: ["rep-module", key, modLevel],
    queryFn: async () => (await api.get("/reports/modules", { params: { ...params, ...(modLevel ? { level: modLevel } : {}) } })).data,
    enabled: tab === "module",
  });

  const download = async (path: string, extra: Record<string, string>, filename: string) => {
    try {
      const r = await api.get(path, { params: { ...params, ...extra }, responseType: "blob" });
      const url = URL.createObjectURL(r.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      setError(null);
    } catch {
      setError("Could not download the file.");
    }
  };

  const tabBtn = (t: Tab, label: string) => (
    <button
      onClick={() => setTab(t)}
      className={`px-3 py-1.5 text-sm rounded ${tab === t ? "bg-gray-900 text-white" : "bg-white border text-gray-700"}`}
    >
      {label}
    </button>
  );
  const sel = "border rounded px-2 py-1.5 text-sm";

  return (
    <div className="p-6">
      <h1 className="text-xl font-semibold mb-4">User activity reports</h1>

      <div className="flex flex-wrap gap-2 mb-4">
        {tabBtn("session", "By session")}
        {tabBtn("area", "By area")}
        {tabBtn("user", "By user")}
        {tabBtn("module", "By module")}
        {tabBtn("tests", "Pre/post tests")}
        {isSuper && tabBtn("bi", "Power BI access")}
      </div>

      {tab === "bi" ? (
        <BiAccess />
      ) : (
        <>
          <div className="bg-white border rounded-lg p-4 mb-4 space-y-3">
            <div className="flex flex-wrap items-center gap-3">
              <select className="border rounded px-2 py-1.5 text-sm" value={sessionId} onChange={(e) => setSessionId(e.target.value)}>
                <option value="">All sessions</option>
                {sessionList.data?.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name} ({t.status.toLowerCase()})
                  </option>
                ))}
              </select>
              <AreaPicker value={area} onChange={setArea} />
            </div>
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <label className="text-xs text-gray-500">
                From <input type="date" className={`${sel} ml-1`} value={dates.date_from} onChange={(e) => setDates({ ...dates, date_from: e.target.value })} />
              </label>
              <label className="text-xs text-gray-500">
                To <input type="date" className={`${sel} ml-1`} value={dates.date_to} onChange={(e) => setDates({ ...dates, date_to: e.target.value })} />
              </label>
              <input className={`${sel} w-32`} placeholder="Team code" value={team} onChange={(e) => setTeam(e.target.value.trim())} />
              <select className={sel} value={learnerRole} onChange={(e) => setLearnerRole(e.target.value)}>
                <option value="">All learner roles</option>
                {LEARNER_ROLES.map((r) => (
                  <option key={r.value} value={r.value}>
                    {r.label}
                  </option>
                ))}
              </select>
              <label className="text-xs text-gray-600 flex items-center gap-1">
                <input type="checkbox" checked={allRoles} onChange={(e) => setAllRoles(e.target.checked)} /> include staff (not only CDDs)
              </label>
            </div>
            <p className="text-xs text-gray-400">
              With dates, activity is counted in that period and &quot;completed&quot; means completed in that period.
            </p>
          </div>

          {summary.data && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
              <Card label="Users" value={summary.data.users} />
              <Card label="Avg module completion" value={`${summary.data.avg_completion_rate}%`} />
              <Card label="Finished all modules" value={summary.data.users_completed_all} />
              <Card label="Active in last 30 days" value={summary.data.active_users_30d} />
              <Card label="Not started" value={summary.data.users_not_started} />
              <Card label="Quizzes passed" value={summary.data.quizzes_passed} />
              <Card label="Questions asked" value={summary.data.questions_asked} />
              <Card label="Modules in training" value={summary.data.modules_total} />
            </div>
          )}

          {error && <p className="text-sm text-red-600 mb-2">{error}</p>}

          {tab === "session" && (
            <>
              <div className="mb-3">
                <button className="border bg-white text-sm rounded px-3 py-1.5" onClick={() => download("/reports/sessions.csv", {}, "training_sessions.csv")}>
                  Export CSV
                </button>
              </div>
              <Table rows={bySession.data} cols={SESSION_COLS} loading={bySession.isLoading} />
            </>
          )}
          {tab === "area" && (
            <>
              <div className="flex items-center gap-3 mb-3">
                <label className="text-sm">
                  Group by{" "}
                  <select className={sel} value={level} onChange={(e) => setLevel(e.target.value)}>
                    {AREA_LEVELS.map((l) => (
                      <option key={l} value={l}>
                        {l.toUpperCase() === "LGA" ? "LGA" : l[0].toUpperCase() + l.slice(1)}
                      </option>
                    ))}
                  </select>
                </label>
                <button className="border bg-white text-sm rounded px-3 py-1.5" onClick={() => download("/reports/boundaries.csv", { level }, `activity_by_${level}.csv`)}>
                  Export CSV
                </button>
              </div>
              <Table rows={byArea.data} cols={AREA_COLS} loading={byArea.isLoading} />
            </>
          )}
          {tab === "user" && (
            <>
              <div className="mb-3">
                <button className="border bg-white text-sm rounded px-3 py-1.5" onClick={() => download("/reports/users.csv", {}, "user_activity.csv")}>
                  Export CSV
                </button>
              </div>
              <Table rows={byUser.data} cols={USER_COLS} loading={byUser.isLoading} />
            </>
          )}
          {tab === "tests" && (
            <TestReport params={params} onDownload={() => download("/learning/report.csv", {}, "pre_post_tests.csv")} />
          )}
          {tab === "module" && (
            <>
              <div className="flex items-center gap-3 mb-3">
                <label className="text-sm">
                  Split by area{" "}
                  <select className={sel} value={modLevel} onChange={(e) => setModLevel(e.target.value)}>
                    <option value="">No split</option>
                    <option value="session">Training session</option>
                    {AREA_LEVELS.map((l) => (
                      <option key={l} value={l}>
                        {l.toUpperCase() === "LGA" ? "LGA" : l[0].toUpperCase() + l.slice(1)}
                      </option>
                    ))}
                  </select>
                </label>
                <button
                  className="border bg-white text-sm rounded px-3 py-1.5"
                  onClick={() => download("/reports/modules.csv", modLevel ? { level: modLevel } : {}, "module_completion.csv")}
                >
                  Export CSV
                </button>
              </div>
              <Table rows={byModule.data} cols={MODULE_COLS} loading={byModule.isLoading} />
            </>
          )}
        </>
      )}
    </div>
  );
}
