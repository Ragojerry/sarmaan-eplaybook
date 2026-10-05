import { useQuery } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { api } from "../services/api";
import { Dashboard } from "../types/api";

/**
 * Every number here comes from GET /analytics/dashboard, which queries real
 * tables (modules, ai_question_log, analytics_events) — never a literal.
 * Per master prompt §49, this must never fall back to hardcoded prototype
 * numbers even when the underlying counts are legitimately zero (e.g. no
 * mobile devices have synced analytics events yet).
 */
export default function DashboardPage() {
  const { data, isLoading, error } = useQuery<Dashboard>({
    queryKey: ["dashboard"],
    queryFn: async () => (await api.get("/analytics/dashboard")).data,
  });

  if (isLoading) return <div className="p-6 text-sm text-gray-500">Loading dashboard…</div>;
  if (error || !data)
    return <div className="p-6 text-sm text-red-600">Could not load dashboard data from the backend.</div>;

  const stats = [
    { label: "Active devices (7d)", value: data.active_devices_7d },
    { label: "Published modules", value: data.published_modules },
    { label: "Draft modules", value: data.draft_modules },
    { label: "Total modules", value: data.total_modules },
    { label: "AI questions (total)", value: data.ai_questions_total },
    { label: "AI questions (unmatched)", value: data.ai_questions_unmatched },
    {
      label: "Update adoption",
      value: data.update_adoption_percent !== null ? `${data.update_adoption_percent}%` : "—",
    },
    { label: "Download failures (7d)", value: data.download_failures_7d },
    { label: "Sync failures (7d)", value: data.sync_failures_7d },
  ];

  return (
    <div className="p-6">
      <h1 className="text-xl font-semibold mb-6">Dashboard</h1>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
        {stats.map((s) => (
          <div key={s.label} className="bg-white rounded-lg border p-4">
            <div className="text-2xl font-semibold">{s.value}</div>
            <div className="text-sm text-gray-500 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-lg border p-4 mb-8">
        <h2 className="text-sm font-medium mb-4">Module engagement (opens vs. completions)</h2>
        {data.module_engagement.length === 0 ? (
          <p className="text-sm text-gray-500">No modules yet.</p>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.module_engagement}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="module_code" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="opens" fill="#0F7A4C" name="Opens" />
              <Bar dataKey="completions" fill="#93c5fd" name="Completions" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="bg-white rounded-lg border p-4">
        <h2 className="text-sm font-medium mb-4">Usage by language</h2>
        {data.language_usage.length === 0 ? (
          <p className="text-sm text-gray-500">
            No language-tagged analytics events yet — this populates once the mobile app is syncing usage data.
          </p>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data.language_usage}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="language_code" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#0F7A4C" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
