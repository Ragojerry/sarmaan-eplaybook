import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import { ManagedUser, TrainingSession } from "../types/api";

const STATUS_STYLE: Record<string, string> = {
  UPCOMING: "bg-blue-100 text-blue-700",
  ONGOING: "bg-green-100 text-green-700",
  ENDED: "bg-gray-100 text-gray-500",
};

function errorText(err: unknown, fallback: string) {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join("; ") || fallback;
  return fallback;
}

const empty = { name: "", description: "", start_date: "", end_date: "" };

/** Training sessions: cohorts with start and end dates. Several can run at once; each person is in one. */
export default function SessionsPage() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState(empty);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  const sessions = useQuery<TrainingSession[]>({ queryKey: ["sessions"], queryFn: async () => (await api.get("/sessions")).data });
  const cdds = useQuery<ManagedUser[]>({
    queryKey: ["users", "cdd-all"],
    queryFn: async () => (await api.get("/users", { params: { role: "CDD" } })).data,
  });
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["sessions"] });
    queryClient.invalidateQueries({ queryKey: ["users"] });
  };
  const fail = (e: unknown) => setMessage({ ok: false, text: errorText(e, "Something went wrong.") });

  const save = useMutation({
    mutationFn: async () => {
      const body = { ...form, description: form.description.trim() || null, name: form.name.trim() };
      return editingId ? (await api.patch(`/sessions/${editingId}`, body)).data : (await api.post("/sessions", body)).data;
    },
    onSuccess: (d) => {
      setMessage({ ok: true, text: editingId ? "Session updated." : "Session created. Now add people to it." });
      setShowForm(false);
      setEditingId(null);
      setForm(empty);
      if (!editingId) setSelected(d.id);
      refresh();
    },
    onError: fail,
  });
  const remove = useMutation({
    mutationFn: async (id: string) => api.delete(`/sessions/${id}`),
    onSuccess: () => {
      setSelected(null);
      setMessage(null);
      refresh();
    },
    onError: fail,
  });
  const assign = useMutation({
    mutationFn: async (v: { id: string; ids: string[]; action: "assign" | "unassign" }) =>
      (await api.post(`/sessions/${v.id}/${v.action}`, { user_ids: v.ids })).data,
    onSuccess: (d) => {
      const moved = d.moved_from_other_session ? ` (${d.moved_from_other_session} moved from another session)` : "";
      setMessage({ ok: true, text: d.assigned !== undefined ? `Added ${d.assigned}${moved}.` : `Removed ${d.unassigned}.` });
      setPicked(new Set());
      refresh();
    },
    onError: fail,
  });

  const current = sessions.data?.find((s) => s.id === selected);
  const members = cdds.data?.filter((u) => u.training_session_id === selected) ?? [];
  const others = (cdds.data ?? [])
    .filter((u) => u.training_session_id !== selected)
    .filter((u) => `${u.first_name} ${u.last_name} ${u.username} ${u.team_code ?? ""}`.toLowerCase().includes(search.toLowerCase()));
  const input = "border rounded px-2 py-1.5 text-sm";

  return (
    <div className="p-6 max-w-5xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-semibold">Training sessions</h1>
          <p className="text-sm text-gray-500">Sessions can overlap. Each person belongs to one, and every report can be limited to a single session.</p>
        </div>
        <button
          className="bg-gray-900 text-white text-sm rounded px-4 py-2"
          onClick={() => {
            setEditingId(null);
            setForm(empty);
            setShowForm((v) => !v);
          }}
        >
          + New session
        </button>
      </div>

      {message && <p className={`text-sm mb-3 ${message.ok ? "text-green-700" : "text-red-600"}`}>{message.text}</p>}

      {showForm && (
        <form
          className="bg-white border rounded-lg p-4 mb-5 grid grid-cols-2 gap-3 text-sm"
          onSubmit={(e) => {
            e.preventDefault();
            save.mutate();
          }}
        >
          <label className="col-span-2 block">
            <span className="text-xs text-gray-500">Session name</span>
            <input required className={`${input} w-full`} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </label>
          <label className="block">
            <span className="text-xs text-gray-500">Start date</span>
            <input required type="date" className={`${input} w-full`} value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
          </label>
          <label className="block">
            <span className="text-xs text-gray-500">End date</span>
            <input required type="date" min={form.start_date} className={`${input} w-full`} value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} />
          </label>
          <label className="col-span-2 block">
            <span className="text-xs text-gray-500">Notes (optional)</span>
            <textarea rows={2} className={`${input} w-full`} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </label>
          <div className="col-span-2 flex gap-2">
            <button disabled={save.isPending} className="bg-gray-900 text-white rounded px-4 py-1.5 disabled:opacity-50">
              {save.isPending ? "Saving…" : editingId ? "Save changes" : "Create session"}
            </button>
            <button type="button" className="text-gray-500 px-3" onClick={() => setShowForm(false)}>
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="bg-white border rounded-lg overflow-x-auto mb-6">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs text-gray-500">
            <tr>
              <th className="px-3 py-2">Session</th>
              <th className="px-3 py-2">Dates</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">People</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {sessions.data?.length === 0 && (
              <tr>
                <td colSpan={5} className="px-3 py-4 text-gray-500">
                  No sessions yet.
                </td>
              </tr>
            )}
            {sessions.data?.map((s) => (
              <tr key={s.id} className={`border-t ${selected === s.id ? "bg-blue-50" : ""}`}>
                <td className="px-3 py-2">
                  <button className="font-medium underline decoration-dotted" onClick={() => { setSelected(s.id); setPicked(new Set()); setMessage(null); }}>
                    {s.name}
                  </button>
                  {s.description && <div className="text-xs text-gray-500">{s.description}</div>}
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-gray-600">
                  {s.start_date} → {s.end_date}
                </td>
                <td className="px-3 py-2">
                  <span className={`px-2 py-0.5 rounded text-xs ${STATUS_STYLE[s.status]}`}>{s.status}</span>
                </td>
                <td className="px-3 py-2">{s.user_count}</td>
                <td className="px-3 py-2 text-right whitespace-nowrap space-x-3 text-xs">
                  <Link className="underline text-blue-600" to={`/reports?session=${s.id}`}>
                    Report
                  </Link>
                  <button
                    className="underline text-gray-600"
                    onClick={() => {
                      setEditingId(s.id);
                      setForm({ name: s.name, description: s.description ?? "", start_date: s.start_date, end_date: s.end_date });
                      setShowForm(true);
                    }}
                  >
                    Edit
                  </button>
                  <button
                    className="underline text-red-500"
                    onClick={() => window.confirm(`Delete "${s.name}"? Only possible when nobody is in it.`) && remove.mutate(s.id)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {current && (
        <div className="grid md:grid-cols-2 gap-5">
          <div className="bg-white border rounded-lg p-4">
            <h2 className="text-sm font-medium mb-2">In &quot;{current.name}&quot; ({members.length})</h2>
            <ul className="divide-y max-h-80 overflow-y-auto text-sm">
              {members.length === 0 && <li className="py-2 text-gray-500">Nobody yet.</li>}
              {members.map((u) => (
                <li key={u.id} className="py-1.5 flex items-center justify-between">
                  <span>
                    {u.first_name} {u.last_name} <span className="text-xs text-gray-400">{u.username}{u.team_code ? ` · team ${u.team_code}` : ""}</span>
                  </span>
                  <button className="text-xs text-red-500 underline" onClick={() => assign.mutate({ id: current.id, ids: [u.id], action: "unassign" })}>
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          </div>
          <div className="bg-white border rounded-lg p-4">
            <h2 className="text-sm font-medium mb-2">Add people</h2>
            <input className={`${input} w-full mb-2`} placeholder="Search name, username or team" value={search} onChange={(e) => setSearch(e.target.value)} />
            <ul className="divide-y max-h-64 overflow-y-auto text-sm mb-3">
              {others.length === 0 && <li className="py-2 text-gray-500">No one to add.</li>}
              {others.map((u) => (
                <li key={u.id} className="py-1.5">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={picked.has(u.id)}
                      onChange={(e) => {
                        const next = new Set(picked);
                        if (e.target.checked) next.add(u.id);
                        else next.delete(u.id);
                        setPicked(next);
                      }}
                    />
                    <span>
                      {u.first_name} {u.last_name} <span className="text-xs text-gray-400">{u.username}</span>
                      {u.session_name && <span className="text-xs text-amber-600"> · now in {u.session_name}</span>}
                    </span>
                  </label>
                </li>
              ))}
            </ul>
            <button
              disabled={picked.size === 0 || assign.isPending}
              className="bg-gray-900 text-white text-sm rounded px-4 py-1.5 disabled:opacity-50"
              onClick={() => assign.mutate({ id: current.id, ids: [...picked], action: "assign" })}
            >
              Add {picked.size || ""} to this session
            </button>
            <p className="text-xs text-gray-400 mt-2">Someone already in another session is moved here; a person is in only one session.</p>
          </div>
        </div>
      )}
    </div>
  );
}
