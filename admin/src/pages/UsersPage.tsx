import { Fragment, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import { ManagedUser, TrainingSession } from "../types/api";
import AreaPicker, { AreaValue, areaFromUser, deepest } from "../components/AreaPicker";

const ROLES = [
  "CDD",
  "SUPERVISOR",
  "CONTENT_ADMIN",
  "PROGRAM_REVIEWER",
  "LOCALISATION_REVIEWER",
  "TECHNICAL_REVIEWER",
  "READ_ONLY",
  "SUPER_ADMIN",
];

function errorText(err: unknown, fallback: string) {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join("; ") || fallback;
  return fallback;
}

/** Account administration (SUPER_ADMIN). The team code is what a CDD sees on
 *  the phone's Home screen as "CDD TEAM 0041". */
export default function UsersPage() {
  const queryClient = useQueryClient();
  const [teamFilter, setTeamFilter] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [message, setMessage] = useState<{ kind: "error" | "info"; text: string } | null>(null);
  const [editing, setEditing] = useState<{ id: string; value: string } | null>(null);
  const [area, setArea] = useState<AreaValue>({});
  const [sessionId, setSessionId] = useState("");
  const [areaEdit, setAreaEdit] = useState<{ id: string; area: AreaValue; sessionId: string } | null>(null);
  const sessions = useQuery<TrainingSession[]>({
    queryKey: ["sessions"],
    queryFn: async () => (await api.get("/sessions")).data,
  });
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    team_code: "",
    role: "CDD",
  });

  const users = useQuery<ManagedUser[]>({
    queryKey: ["users", teamFilter],
    queryFn: async () => (await api.get("/users", { params: teamFilter ? { team_code: teamFilter } : {} })).data,
  });
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["users"] });

  const create = useMutation({
    mutationFn: async () =>
      (
        await api.post("/users", {
          ...form,
          team_code: form.team_code || null,
          boundary_id: deepest(area),
          training_session_id: sessionId || null,
        })
      ).data,
    onSuccess: () => {
      setShowCreate(false);
      setForm({ username: "", email: "", password: "", first_name: "", last_name: "", team_code: "", role: "CDD" });
      setArea({});
      setSessionId("");
      setMessage({ kind: "info", text: "Account created. Share the password with the user securely." });
      refresh();
    },
    onError: (e) => setMessage({ kind: "error", text: errorText(e, "Could not create the account.") }),
  });

  const patch = useMutation({
    mutationFn: async (v: { id: string; body: Record<string, unknown> }) => (await api.patch(`/users/${v.id}`, v.body)).data,
    onSuccess: () => {
      setEditing(null);
      setAreaEdit(null);
      setMessage(null);
      refresh();
    },
    onError: (e) => setMessage({ kind: "error", text: errorText(e, "Could not update the account.") }),
  });

  const resetTraining = useMutation({
    mutationFn: async (id: string) => (await api.post(`/users/${id}/reset-training`)).data,
    onSuccess: () => {
      setMessage({ kind: "info", text: "Training reset. Their phone will clear the old attempt at its next sync." });
      refresh();
    },
    onError: (e) => setMessage({ kind: "error", text: errorText(e, "Could not reset the training.") }),
  });

  const field = "mt-1 w-full border rounded px-2 py-1";

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">Users</h1>
        <div className="flex items-center gap-3">
          <input
            className="border rounded px-2 py-1.5 text-sm w-36"
            placeholder="Filter by team code"
            value={teamFilter}
            onChange={(e) => setTeamFilter(e.target.value.trim())}
          />
          <button onClick={() => setShowCreate((v) => !v)} className="bg-gray-900 text-white text-sm rounded px-4 py-2">
            + New user
          </button>
        </div>
      </div>

      {message && <p className={`text-sm mb-4 ${message.kind === "error" ? "text-red-600" : "text-green-700"}`}>{message.text}</p>}

      {showCreate && (
        <form
          className="bg-white border rounded-lg p-4 mb-6 grid grid-cols-2 gap-3 text-sm"
          onSubmit={(e) => {
            e.preventDefault();
            create.mutate();
          }}
        >
          {(
            [
              ["first_name", "First name"],
              ["last_name", "Last name"],
              ["username", "Username"],
              ["email", "Email"],
            ] as const
          ).map(([k, label]) => (
            <label key={k} className="block">
              <span className="text-xs text-gray-500">{label}</span>
              <input required className={field} value={form[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })} />
            </label>
          ))}
          <label className="block">
            <span className="text-xs text-gray-500">Password (10+ characters)</span>
            <input
              required
              minLength={10}
              type="password"
              className={field}
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          </label>
          <label className="block">
            <span className="text-xs text-gray-500">Role</span>
            <select className={field} value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              {ROLES.map((r) => (
                <option key={r}>{r}</option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-xs text-gray-500">Team code (letters, digits, dashes — e.g. 0041)</span>
            <input
              className={field}
              maxLength={20}
              pattern="[A-Za-z0-9\-]{1,20}"
              value={form.team_code}
              onChange={(e) => setForm({ ...form, team_code: e.target.value.trim() })}
            />
          </label>
          <div className="col-span-2">
            <span className="text-xs text-gray-500">Where this person works (pick as deep as you know)</span>
            <div className="mt-1">
              <AreaPicker value={area} onChange={setArea} />
            </div>
          </div>
          <label className="block">
            <span className="text-xs text-gray-500">Training session</span>
            <select className={field} value={sessionId} onChange={(e) => setSessionId(e.target.value)}>
              <option value="">No session yet</option>
              {sessions.data?.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} ({t.start_date} to {t.end_date})
                </option>
              ))}
            </select>
          </label>
          <div className="col-span-2">
            <button disabled={create.isPending} className="bg-gray-900 text-white rounded px-4 py-1.5 disabled:opacity-50">
              {create.isPending ? "Creating…" : "Create account"}
            </button>
          </div>
        </form>
      )}

      <div className="bg-white border rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs text-gray-500">
            <tr>
              <th className="px-3 py-2">Name</th>
              <th className="px-3 py-2">Username</th>
              <th className="px-3 py-2">Role</th>
              <th className="px-3 py-2">Team</th>
              <th className="px-3 py-2">Area &amp; session</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Last sign-in</th>
            </tr>
          </thead>
          <tbody>
            {users.isLoading && (
              <tr>
                <td colSpan={7} className="px-3 py-4 text-gray-500">
                  Loading…
                </td>
              </tr>
            )}
            {users.data?.length === 0 && (
              <tr>
                <td colSpan={7} className="px-3 py-4 text-gray-500">
                  No users found.
                </td>
              </tr>
            )}
            {users.data?.map((u) => (
              <Fragment key={u.id}>
              <tr className="border-t">
                <td className="px-3 py-2">
                  {u.first_name} {u.last_name}
                  <div className="text-xs text-gray-500">{u.email}</div>
                </td>
                <td className="px-3 py-2 text-gray-600">{u.username}</td>
                <td className="px-3 py-2 text-gray-600">{u.role}</td>
                <td className="px-3 py-2">
                  {editing?.id === u.id ? (
                    <span className="flex items-center gap-2">
                      <input
                        autoFocus
                        className="border rounded px-1.5 py-0.5 w-24"
                        value={editing.value}
                        maxLength={20}
                        onChange={(e) => setEditing({ id: u.id, value: e.target.value.trim() })}
                      />
                      <button
                        className="text-xs underline text-green-700"
                        onClick={() => patch.mutate({ id: u.id, body: { team_code: editing.value } })}
                      >
                        Save
                      </button>
                      <button className="text-xs underline text-gray-500" onClick={() => setEditing(null)}>
                        Cancel
                      </button>
                    </span>
                  ) : (
                    <button className="underline decoration-dotted" onClick={() => setEditing({ id: u.id, value: u.team_code ?? "" })}>
                      {u.team_code ?? "— set"}
                    </button>
                  )}
                </td>
                <td className="px-3 py-2 text-xs text-gray-600">
                  {[u.state_name, u.lga_name, u.ward_name, u.facility_name].filter(Boolean).join(" › ") || "—"}
                  <div className="text-gray-500">
                    {u.session_name ? `Session: ${u.session_name}` : "No session"}
                    {u.session_status && <span className="text-gray-400"> · {u.session_status.toLowerCase()}</span>}
                  </div>
                  <button
                    className="underline decoration-dotted text-gray-500 block"
                    onClick={() =>
                      setAreaEdit({
                        id: u.id,
                        area: areaFromUser(u as unknown as Record<string, unknown>),
                        sessionId: u.training_session_id ?? "",
                      })
                    }
                  >
                    edit area / session
                  </button>
                  {u.role === "CDD" && (
                    <div className="mt-1">
                      <span className="text-xs text-gray-500">Attempt {u.training_attempt ?? 1}</span>{" "}
                      <button
                        className="text-xs underline text-red-700"
                        onClick={() => {
                          if (window.confirm(`Reset ${u.first_name} ${u.last_name}'s training? Their progress and quiz results are replaced by a fresh attempt. This cannot be undone.`))
                            resetTraining.mutate(u.id);
                        }}
                      >
                        reset training
                      </button>
                    </div>
                  )}
                </td>
                <td className="px-3 py-2">
                  <button
                    className="text-xs underline text-gray-700"
                    onClick={() => patch.mutate({ id: u.id, body: { status: u.status === "ACTIVE" ? "INACTIVE" : "ACTIVE" } })}
                  >
                    {u.status}
                  </button>
                </td>
                <td className="px-3 py-2 text-gray-500 whitespace-nowrap">
                  {u.last_login_at ? new Date(u.last_login_at).toLocaleString() : "never"}
                </td>
              </tr>
              {areaEdit?.id === u.id && (
                <tr className="bg-gray-50">
                  <td colSpan={7} className="px-3 py-3">
                    <div className="flex flex-wrap items-end gap-3">
                      <AreaPicker value={areaEdit.area} onChange={(a) => setAreaEdit({ ...areaEdit, area: a })} />
                      <select className="border rounded px-2 py-1.5 text-sm" value={areaEdit.sessionId} onChange={(e) => setAreaEdit({ ...areaEdit, sessionId: e.target.value })}>
                        <option value="">No session</option>
                        {sessions.data?.map((t) => (
                          <option key={t.id} value={t.id}>
                            {t.name}
                          </option>
                        ))}
                      </select>
                      <button
                        className="bg-gray-900 text-white text-sm rounded px-3 py-1.5"
                        onClick={() => {
                          const id = deepest(areaEdit.area);
                          patch.mutate({
                            id: u.id,
                            body: {
                              ...(id ? { boundary_id: id } : { clear_boundary: true }),
                              ...(areaEdit.sessionId ? { training_session_id: areaEdit.sessionId } : { clear_session: true }),
                            },
                          });
                        }}
                      >
                        Save
                      </button>
                      <button className="text-sm text-gray-500" onClick={() => setAreaEdit(null)}>
                        Cancel
                      </button>
                    </div>
                  </td>
                </tr>
              )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
