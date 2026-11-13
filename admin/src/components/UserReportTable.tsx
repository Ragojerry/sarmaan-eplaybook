import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../services/api";
import { LEARNER_ROLES, learnerRoleLabel } from "../learnerRoles";
import { ReportRow } from "../types/api";

type Kind = "text" | "choice" | "number" | "date";
type Col = { key: string; label: string; kind: Kind; options?: { value: string; label: string }[] };

const RESULT = [
  { value: "PASSED", label: "Passed" },
  { value: "NOT_PASSED", label: "Not passed" },
  { value: "-", label: "No result" },
];

/** Every column of the by-user table, with the kind of filter it gets. */
const COLS: Col[] = [
  { key: "full_name", label: "Name", kind: "text" },
  { key: "username", label: "Username", kind: "text" },
  {
    key: "status",
    label: "Status",
    kind: "choice",
    options: [
      { value: "ACTIVE", label: "Active" },
      { value: "INACTIVE", label: "Deactivated" },
      { value: "SUSPENDED", label: "Suspended" },
    ],
  },
  { key: "learner_role", label: "Learner role (cadre)", kind: "choice", options: [...LEARNER_ROLES, { value: "-", label: "None" }] },
  { key: "team_code", label: "Team", kind: "text" },
  { key: "session", label: "Session", kind: "text" },
  { key: "training_attempt", label: "Attempt", kind: "choice" },
  { key: "state", label: "State", kind: "text" },
  { key: "lga", label: "LGA", kind: "text" },
  { key: "ward", label: "Ward", kind: "text" },
  { key: "facility", label: "Facility", kind: "text" },
  { key: "modules_completed", label: "Done", kind: "number" },
  { key: "completion_rate", label: "Completion %", kind: "number" },
  { key: "module_quizzes_passed", label: "Module quizzes passed", kind: "number" },
  { key: "quizzes_passed", label: "Quizzes passed", kind: "number" },
  { key: "avg_best_quiz_score", label: "Avg quiz %", kind: "number" },
  { key: "seconds_spent_total", label: "Seconds in modules", kind: "number" },
  { key: "general_pre_points", label: "Pre-test score", kind: "number" },
  { key: "general_pre_percent", label: "Pre-test %", kind: "number" },
  { key: "general_pre_pass_mark", label: "Pre pass mark %", kind: "number" },
  { key: "general_pre_passed", label: "Pre-test result", kind: "choice", options: RESULT },
  { key: "general_post_points", label: "Post-test score", kind: "number" },
  { key: "general_post_percent", label: "Post-test %", kind: "number" },
  { key: "general_post_pass_mark", label: "Post pass mark %", kind: "number" },
  { key: "general_post_passed", label: "Post-test result", kind: "choice", options: RESULT },
  { key: "general_change_points", label: "Improvement (points)", kind: "number" },
  { key: "general_change_percent", label: "Improvement (% points)", kind: "number" },
  { key: "devices_active", label: "Active devices", kind: "number" },
  { key: "devices_total", label: "All devices", kind: "number" },
  { key: "device_last_seen", label: "Device last seen", kind: "date" },
  { key: "training_events", label: "Training", kind: "number" },
  { key: "video_events", label: "Video", kind: "number" },
  { key: "questions_asked", label: "Q&A", kind: "number" },
  { key: "technical_events", label: "Technical", kind: "number" },
  { key: "last_activity", label: "Last activity", kind: "date" },
  { key: "last_login", label: "Last login", kind: "date" },
  { key: "deactivated_at", label: "Deactivated on", kind: "date" },
];

type Filters = Record<string, string>; // query parameter -> value (q./in./min./max./from./to.<column>)

function label(c: Col, v: string) {
  return c.options?.find((o) => o.value === v)?.label ?? v;
}

function display(key: string, v: string | number | null | undefined) {
  if (v === null || v === undefined || v === "") return "—";
  if (["last_activity", "last_login", "device_last_seen", "deactivated_at"].includes(key) && typeof v === "string")
    return new Date(v).toLocaleDateString();
  if (key === "learner_role") return learnerRoleLabel(String(v));
  if (key === "status") return v === "INACTIVE" ? "Deactivated" : v === "ACTIVE" ? "Active" : String(v);
  if (key === "general_pre_passed" || key === "general_post_passed") return v === "PASSED" ? "✓ Passed" : "✗ Not passed";
  return String(v);
}

function chipText(param: string, value: string) {
  const [kind, key] = [param.slice(0, param.indexOf(".")), param.slice(param.indexOf(".") + 1)];
  const c = COLS.find((x) => x.key === key);
  const name = c?.label ?? key;
  if (kind === "q") return `${name} contains “${value}”`;
  if (kind === "in") return `${name}: ${c ? label(c, value) : value}`;
  if (kind === "min") return `${name} ≥ ${value}`;
  if (kind === "max") return `${name} ≤ ${value}`;
  if (kind === "from") return `${name} from ${value}`;
  return `${name} to ${value}`;
}

type Device = {
  id: string;
  os: string | null;
  os_version: string | null;
  model: string | null;
  app_version: string | null;
  first_seen_at: string | null;
  last_seen_at: string | null;
  last_sync_at: string | null;
  active: boolean;
};

function DevicesDialog({ row, onClose }: { row: ReportRow; onClose: () => void }) {
  const q = useQuery<{ active_days: number; devices: Device[] }>({
    queryKey: ["user-devices", row.user_id],
    queryFn: async () => (await api.get(`/reports/users/${row.user_id}/devices`)).data,
  });
  const when = (s: string | null) => (s ? new Date(s).toLocaleString() : "—");
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50" role="dialog" aria-modal="true" aria-label="Devices">
      <div className="bg-paper rounded-lg max-w-4xl w-full p-5 max-h-[80vh] overflow-auto">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h2 className="font-semibold">Devices of {row.full_name}</h2>
            <p className="text-xs text-gray-600">
              Active = signed in or synced within the last {q.data?.active_days ?? 30} days. Devices appear from app 0.1.16 on.
            </p>
          </div>
          <button className="text-sm underline" onClick={onClose}>
            Close
          </button>
        </div>
        {q.isLoading && <p className="text-sm text-gray-600">Loading…</p>}
        {q.data && q.data.devices.length === 0 && <p className="text-sm text-gray-600">No device recorded yet.</p>}
        {q.data && q.data.devices.length > 0 && (
          <table className="w-full text-sm">
            <thead className="text-left text-xs text-gray-500 border-b">
              <tr>
                <th className="px-2 py-1.5">Model</th>
                <th className="px-2 py-1.5">OS</th>
                <th className="px-2 py-1.5">App</th>
                <th className="px-2 py-1.5">First seen</th>
                <th className="px-2 py-1.5">Last seen</th>
                <th className="px-2 py-1.5">Last sync</th>
                <th className="px-2 py-1.5">Status</th>
              </tr>
            </thead>
            <tbody>
              {q.data.devices.map((d) => (
                <tr key={d.id} className="border-b last:border-0">
                  <td className="px-2 py-1.5">{d.model ?? "—"}</td>
                  <td className="px-2 py-1.5">{[d.os, d.os_version].filter(Boolean).join(" ") || "—"}</td>
                  <td className="px-2 py-1.5">{d.app_version ?? "—"}</td>
                  <td className="px-2 py-1.5 whitespace-nowrap">{when(d.first_seen_at)}</td>
                  <td className="px-2 py-1.5 whitespace-nowrap">{when(d.last_seen_at)}</td>
                  <td className="px-2 py-1.5 whitespace-nowrap">{when(d.last_sync_at)}</td>
                  <td className="px-2 py-1.5">{d.active ? "● Active" : "○ Not active"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

/**
 * Reports by user: a filter on every column (text contains, dropdowns, number and
 * date ranges), sorting, active-filter chips and the result count. Filters and sort
 * are sent to the server, so "Export CSV" downloads exactly the rows on screen.
 */
export default function UserReportTable({
  params,
  onDownload,
}: {
  params: Record<string, string | boolean>;
  onDownload: (path: string, extra: Record<string, string>, filename: string) => void;
}) {
  const [draft, setDraft] = useState<Filters>({});
  const [filters, setFilters] = useState<Filters>({});
  const [sort, setSort] = useState<{ key: string; desc: boolean } | null>(null);
  const [devicesOf, setDevicesOf] = useState<ReportRow | null>(null);

  // Typing in a text or number box waits a moment before asking the server.
  useEffect(() => {
    const t = setTimeout(() => setFilters(draft), 350);
    return () => clearTimeout(t);
  }, [draft]);

  const columnParams = useMemo(() => {
    const out: Record<string, string> = {};
    for (const [k, v] of Object.entries(filters)) if (v.trim() !== "") out[k] = v.trim();
    if (sort) {
      out.sort = sort.key;
      out.order = sort.desc ? "desc" : "asc";
    }
    return out;
  }, [filters, sort]);

  const rows = useQuery<ReportRow[]>({
    queryKey: ["rep-user", JSON.stringify(params), JSON.stringify(columnParams)],
    queryFn: async () => (await api.get("/reports/users", { params: { ...params, ...columnParams } })).data,
  });

  const attempts = useMemo(() => {
    const seen = new Set<string>((rows.data ?? []).map((r) => String(r.training_attempt ?? "")).filter(Boolean));
    if (filters["in.training_attempt"]) seen.add(filters["in.training_attempt"]);
    return [...seen].sort((a, b) => Number(a) - Number(b)).map((v) => ({ value: v, label: `Attempt ${v}` }));
  }, [rows.data, filters]);

  const set = (param: string, value: string) => setDraft((d) => ({ ...d, [param]: value }));
  const setNow = (param: string, value: string) => {
    setDraft((d) => ({ ...d, [param]: value }));
    setFilters((f) => ({ ...f, [param]: value }));
  };
  const active = Object.entries(filters).filter(([, v]) => v.trim() !== "");
  const clearAll = () => {
    setDraft({});
    setFilters({});
    setSort(null);
  };
  const toggleSort = (key: string) =>
    setSort((s) => (s?.key !== key ? { key, desc: false } : s.desc ? null : { key, desc: true }));

  const input = "w-full min-w-[5rem] border rounded px-1.5 py-0.5 text-xs font-normal";

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-2 text-sm">
        <button
          className="border bg-white rounded px-3 py-1.5"
          onClick={() => onDownload("/reports/users.csv", columnParams, "user_activity.csv")}
        >
          Export CSV (current filters)
        </button>
        <span className="text-gray-700" aria-live="polite">
          {rows.isLoading ? "Loading…" : `${rows.data?.length ?? 0} user(s)`}
        </span>
        {(active.length > 0 || sort) && (
          <button className="underline text-sm" onClick={clearAll}>
            Clear all filters
          </button>
        )}
      </div>
      {active.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-2" aria-label="Active filters">
          {active.map(([k, v]) => (
            <span key={k} className="inline-flex items-center gap-1 bg-gray-100 border rounded-full px-2 py-0.5 text-xs">
              {chipText(k, v)}
              <button aria-label={`Remove filter: ${chipText(k, v)}`} className="px-1" onClick={() => setNow(k, "")}>
                ×
              </button>
            </span>
          ))}
        </div>
      )}
      {rows.isError && <p className="text-sm text-red-600 mb-2">Could not load the report with these filters.</p>}

      <div className="bg-white border rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs text-gray-500 align-top">
            <tr>
              {COLS.map((c) => (
                <th key={c.key} className="px-2 pt-2 whitespace-nowrap" aria-sort={sort?.key === c.key ? (sort.desc ? "descending" : "ascending") : "none"}>
                  <button className="font-medium hover:underline" onClick={() => toggleSort(c.key)}>
                    {c.label}
                    {sort?.key === c.key ? (sort.desc ? " ▼" : " ▲") : ""}
                  </button>
                </th>
              ))}
            </tr>
            <tr>
              {COLS.map((c) => (
                <th key={c.key} className="px-2 pb-2 pt-1">
                  {c.kind === "text" && (
                    <input className={input} placeholder="Contains…" aria-label={`Filter ${c.label}`} value={draft[`q.${c.key}`] ?? ""} onChange={(e) => set(`q.${c.key}`, e.target.value)} />
                  )}
                  {c.kind === "choice" && (
                    <select className={input} aria-label={`Filter ${c.label}`} value={draft[`in.${c.key}`] ?? ""} onChange={(e) => setNow(`in.${c.key}`, e.target.value)}>
                      <option value="">All</option>
                      {(c.key === "training_attempt" ? attempts : c.options ?? []).map((o) => (
                        <option key={o.value} value={o.value}>
                          {o.label}
                        </option>
                      ))}
                    </select>
                  )}
                  {c.kind === "number" && (
                    <div className="flex gap-1">
                      <input className={input} inputMode="decimal" placeholder="min" aria-label={`${c.label} at least`} value={draft[`min.${c.key}`] ?? ""} onChange={(e) => set(`min.${c.key}`, e.target.value)} />
                      <input className={input} inputMode="decimal" placeholder="max" aria-label={`${c.label} at most`} value={draft[`max.${c.key}`] ?? ""} onChange={(e) => set(`max.${c.key}`, e.target.value)} />
                    </div>
                  )}
                  {c.kind === "date" && (
                    <div className="flex flex-col gap-1">
                      <input type="date" className={input} aria-label={`${c.label} from`} value={draft[`from.${c.key}`] ?? ""} onChange={(e) => setNow(`from.${c.key}`, e.target.value)} />
                      <input type="date" className={input} aria-label={`${c.label} to`} value={draft[`to.${c.key}`] ?? ""} onChange={(e) => setNow(`to.${c.key}`, e.target.value)} />
                    </div>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {!rows.isLoading && rows.data?.length === 0 && (
              <tr>
                <td colSpan={COLS.length} className="px-3 py-4 text-gray-600">
                  Nothing matches these filters.
                </td>
              </tr>
            )}
            {rows.data?.map((r, i) => (
              <tr key={String(r.user_id ?? i)} className={`border-t ${r.status !== "ACTIVE" ? "bg-gray-50 text-gray-600" : ""}`}>
                {COLS.map((c) => (
                  <td key={c.key} className="px-2 py-1.5 whitespace-nowrap">
                    {c.key === "devices_active" ? (
                      <button className="underline" onClick={() => setDevicesOf(r)} aria-label={`Devices of ${r.full_name}`}>
                        {display(c.key, r[c.key] ?? 0)} — list
                      </button>
                    ) : (
                      display(c.key, r[c.key])
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {devicesOf && <DevicesDialog row={devicesOf} onClose={() => setDevicesOf(null)} />}
    </div>
  );
}
