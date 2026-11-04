import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { api } from "../services/api";
import { useAuth } from "../services/auth";
import { QuestionsReport, UsageReport } from "../types/api";

const PERIODS = [7, 30, 90];

function Card({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <div className="bg-white rounded-lg border p-4">
      <div className="text-2xl font-semibold">{value}</div>
      <div className="text-sm text-gray-500 mt-1">{label}</div>
      {hint && <div className="text-xs text-gray-400 mt-1">{hint}</div>}
    </div>
  );
}

function Empty({ children }: { children: string }) {
  return <p className="text-sm text-gray-500">{children}</p>;
}

/**
 * Usage reports (master prompt §49-50) and unanswered-question analysis
 * (§42-43). Every figure is a database query; "0" means nothing was recorded.
 * Event-based figures only cover phones whose users opted in to usage
 * statistics, so the page says so rather than implying full coverage.
 */
export default function AnalyticsPage() {
  const { user } = useAuth();
  const canAnswer = user?.role === "CONTENT_ADMIN" || user?.role === "SUPER_ADMIN";
  const [days, setDays] = useState(30);

  const usage = useQuery<UsageReport>({
    queryKey: ["usage", days],
    queryFn: async () => (await api.get("/analytics/usage", { params: { days } })).data,
  });
  const questions = useQuery<QuestionsReport>({
    queryKey: ["questions", days],
    queryFn: async () => (await api.get("/analytics/questions", { params: { days } })).data,
  });

  const forbidden = (usage.error as { response?: { status?: number } } | null)?.response?.status === 403;
  if (forbidden) return <div className="p-6 text-sm text-red-600">Your role is not permitted to view analytics.</div>;
  if (usage.isLoading) return <div className="p-6 text-sm text-gray-500">Loading analytics…</div>;
  if (usage.error || !usage.data) return <div className="p-6 text-sm text-red-600">Could not load analytics.</div>;

  const u = usage.data;
  const q = questions.data;
  const t = u.technical;

  return (
    <div className="p-6 space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Analytics</h1>
        <div className="flex gap-1 text-sm">
          {PERIODS.map((p) => (
            <button
              key={p}
              onClick={() => setDays(p)}
              className={`px-3 py-1 rounded border ${days === p ? "bg-gray-900 text-white" : "bg-white"}`}
            >
              {p} days
            </button>
          ))}
        </div>
      </div>
      <p className="text-xs text-gray-500 -mt-6">{u.note}</p>

      <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card label="Active devices (24 h)" value={u.devices.active_1d} />
        <Card label="Active devices (7 d)" value={u.devices.active_7d} />
        <Card label="Active devices (30 d)" value={u.devices.active_30d} />
        <Card
          label="On current release"
          value={u.release_adoption_percent !== null ? `${u.release_adoption_percent}%` : "—"}
          hint={u.current_release_code ? `${u.current_release_code} · ${u.current_release_devices} devices` : "No release published"}
        />
      </section>

      <section className="bg-white border rounded-lg p-4">
        <h2 className="text-sm font-medium mb-4">Activity per day (UTC)</h2>
        {u.daily.every((d) => d.events === 0) ? (
          <Empty>No usage events recorded in this period.</Empty>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={u.daily}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tickFormatter={(d: string) => d.slice(5)} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="events" fill="#0F7A4C" name="Events" />
              <Bar dataKey="devices" fill="#93c5fd" name="Devices" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </section>

      <section className="bg-white border rounded-lg p-4 overflow-x-auto">
        <h2 className="text-sm font-medium mb-3">Modules</h2>
        <table className="w-full text-sm">
          <thead className="text-left text-xs text-gray-500">
            <tr>
              <th className="py-1 pr-3">Module</th>
              <th className="py-1 pr-3">Opens</th>
              <th className="py-1 pr-3">Completions</th>
              <th className="py-1 pr-3">CDDs started</th>
              <th className="py-1 pr-3">CDDs completed</th>
            </tr>
          </thead>
          <tbody>
            {u.modules.map((m) => (
              <tr key={m.module_id} className="border-t">
                <td className="py-1.5 pr-3">
                  <span className="font-mono text-xs text-gray-500 mr-2">{m.module_code}</span>
                  {m.title}
                </td>
                <td className="py-1.5 pr-3">{m.opens}</td>
                <td className="py-1.5 pr-3">{m.completions}</td>
                <td className="py-1.5 pr-3">{m.cdds_started}</td>
                <td className="py-1.5 pr-3">{m.cdds_completed}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="text-xs text-gray-400 mt-2">
          Opens/completions are usage events (opt-in devices). CDD columns come from synced learner progress.
        </p>
      </section>

      <section className="bg-white border rounded-lg p-4 overflow-x-auto">
        <h2 className="text-sm font-medium mb-3">Videos</h2>
        {u.videos.length === 0 ? (
          <Empty>No videos yet.</Empty>
        ) : (
          <table className="w-full text-sm">
            <thead className="text-left text-xs text-gray-500">
              <tr>
                <th className="py-1 pr-3">Video</th>
                <th className="py-1 pr-3">Opens</th>
                <th className="py-1 pr-3">Completions</th>
                <th className="py-1 pr-3">Playback failures</th>
              </tr>
            </thead>
            <tbody>
              {u.videos.map((v) => (
                <tr key={v.video_id} className="border-t">
                  <td className="py-1.5 pr-3">{v.title}</td>
                  <td className="py-1.5 pr-3">{v.opens}</td>
                  <td className="py-1.5 pr-3">{v.completions}</td>
                  <td className="py-1.5 pr-3">{v.playback_failures}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card label="Download failures" value={t.download_failures} />
        <Card label="Sync failures" value={t.sync_failures} />
        <Card label="App errors" value={t.app_errors} />
        <Card label="Storage errors" value={t.storage_errors} />
        <Card label="Playback failures" value={t.playback_failures} />
      </section>

      <section className="bg-white border rounded-lg p-4">
        <h2 className="text-sm font-medium mb-3">Release adoption (devices that installed each release)</h2>
        {u.release_adoption.length === 0 ? (
          <Empty>No update installs recorded yet.</Empty>
        ) : (
          <ul className="text-sm space-y-1">
            {u.release_adoption.map((r) => (
              <li key={r.release_code} className="flex justify-between border-t pt-1">
                <span className="font-mono text-xs">{r.release_code}</span>
                <span>{r.devices} devices</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="bg-white border rounded-lg p-4">
        <h2 className="text-sm font-medium mb-1">Questions learners ask</h2>
        {q ? (
          <>
            <p className="text-xs text-gray-500 mb-4">
              {q.total} asked · {q.matched} answered · {q.unmatched} not answered
              {q.answer_rate_percent !== null && ` · ${q.answer_rate_percent}% answer rate`}
            </p>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-xs font-medium text-red-700 mb-2">Not answered — possible content gaps</h3>
                {q.top_unanswered.length === 0 ? (
                  <Empty>None in this period.</Empty>
                ) : (
                  <ul className="text-sm space-y-1">
                    {q.top_unanswered.map((x) => (
                      <li key={x.question} className="flex justify-between gap-3 border-t pt-1">
                        <span>{x.question}</span>
                        <span className="text-gray-500 shrink-0 space-x-2">
                          <span>×{x.count}</span>
                          {canAnswer && (
                            <Link to={`/answers?question=${encodeURIComponent(x.question)}`} className="text-xs text-blue-700 underline">
                              Answer this
                            </Link>
                          )}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <div>
                <h3 className="text-xs font-medium text-gray-700 mb-2">Most asked and answered</h3>
                {q.top_answered.length === 0 ? (
                  <Empty>None in this period.</Empty>
                ) : (
                  <ul className="text-sm space-y-1">
                    {q.top_answered.map((x) => (
                      <li key={x.question} className="flex justify-between gap-3 border-t pt-1">
                        <span>{x.question}</span>
                        <span className="text-gray-500 shrink-0">×{x.count}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </>
        ) : (
          <Empty>Loading…</Empty>
        )}
      </section>
    </div>
  );
}
