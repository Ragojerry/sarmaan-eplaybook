import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";

interface KeyRow {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string | null;
  last_used_at: string | null;
  revoked: boolean;
}

/** SUPER_ADMIN: create/revoke read-only API keys and see how to connect Power BI. */
export default function BiAccess() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [fresh, setFresh] = useState<{ name: string; key: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const base = String(api.defaults.baseURL ?? "").replace(/\/$/, "");

  const keys = useQuery<KeyRow[]>({ queryKey: ["bi-keys"], queryFn: async () => (await api.get("/bi/keys")).data });
  const create = useMutation({
    mutationFn: async () => (await api.post("/bi/keys", { name: name.trim() })).data,
    onSuccess: (d) => {
      setFresh({ name: d.name, key: d.key });
      setName("");
      setError(null);
      queryClient.invalidateQueries({ queryKey: ["bi-keys"] });
    },
    onError: () => setError("Could not create the key."),
  });
  const revoke = useMutation({
    mutationFn: async (id: string) => api.delete(`/bi/keys/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["bi-keys"] }),
  });

  const sample = `let
    Source = Json.Document(Web.Contents("${base}/bi/users", [
        Headers = [#"X-API-Key" = "PASTE_YOUR_KEY_HERE"],
        Query = [state_id = "OPTIONAL_STATE_ID"]
    ])),
    Table = Table.FromRecords(Source)
in
    Table`;

  return (
    <div className="space-y-5">
      <div className="bg-white border rounded-lg p-4">
        <h2 className="text-sm font-medium mb-1">API keys</h2>
        <p className="text-xs text-gray-500 mb-3">
          A key gives read-only access to the reports below. It is shown once when created; only a fingerprint is kept.
          Revoke a key if it is lost or shared by mistake.
        </p>
        <form
          className="flex gap-2 mb-3"
          onSubmit={(e) => {
            e.preventDefault();
            create.mutate();
          }}
        >
          <input
            required
            className="border rounded px-2 py-1.5 text-sm w-64"
            placeholder="Name, e.g. Power BI – M&E team"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <button disabled={create.isPending} className="bg-gray-900 text-white text-sm rounded px-4 py-1.5 disabled:opacity-50">
            Create key
          </button>
        </form>
        {error && <p className="text-sm text-red-600 mb-2">{error}</p>}
        {fresh && (
          <div className="border border-amber-300 bg-amber-50 rounded p-3 mb-3 text-sm">
            <p className="font-medium">Copy this key now: it will not be shown again.</p>
            <code className="block break-all my-2 bg-white border rounded px-2 py-1">{fresh.key}</code>
            <button
              className="text-xs underline mr-3"
              onClick={() => navigator.clipboard?.writeText(fresh.key)}
            >
              Copy
            </button>
            <button className="text-xs underline text-gray-500" onClick={() => setFresh(null)}>
              I have saved it
            </button>
          </div>
        )}
        <table className="w-full text-sm">
          <thead className="text-left text-xs text-gray-500">
            <tr>
              <th className="py-1">Name</th>
              <th>Key starts with</th>
              <th>Last used</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {keys.data?.length === 0 && (
              <tr>
                <td colSpan={4} className="py-2 text-gray-500">
                  No keys yet.
                </td>
              </tr>
            )}
            {keys.data?.map((k) => (
              <tr key={k.id} className="border-t">
                <td className="py-1.5">
                  {k.name} {k.revoked && <span className="text-xs text-red-500">(revoked)</span>}
                </td>
                <td className="font-mono text-xs">{k.key_prefix}…</td>
                <td className="text-xs text-gray-500">{k.last_used_at ? new Date(k.last_used_at).toLocaleString() : "never"}</td>
                <td className="text-right">
                  {!k.revoked && (
                    <button
                      className="text-xs text-red-500 underline"
                      onClick={() => window.confirm(`Revoke "${k.name}"? Anything using it stops working.`) && revoke.mutate(k.id)}
                    >
                      Revoke
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="bg-white border rounded-lg p-4 text-sm">
        <h2 className="text-sm font-medium mb-2">Endpoints</h2>
        <p className="text-xs text-gray-500 mb-2">
          Send the key in the <code>X-API-Key</code> header. All return a JSON array (add <code>format=csv</code> for CSV).
          Filters: <code>session_id, country_id, state_id, lga_id, ward_id, facility_id, team_code, date_from, date_to, all_roles</code>.
        </p>
        <ul className="space-y-1 font-mono text-xs break-all">
          <li>{base}/bi/users: one row per user (area, location, completion, quiz, activity categories)</li>
          <li>{base}/bi/sessions: one row per training session (dates, status, enrolment, completion, finished by end date)</li>
          <li>{base}/bi/boundaries?level=state: totals by country / state / lga / ward / facility</li>
          <li>{base}/bi/modules?level=state: completion and quiz results per module (and per area or session)</li>
        </ul>
        <h3 className="text-sm font-medium mt-4 mb-1">Power BI Desktop</h3>
        <ol className="list-decimal list-inside text-xs text-gray-600 space-y-1 mb-2">
          <li>Home → Get data → Blank query → Advanced Editor.</li>
          <li>Paste the query below, put your key in place of PASTE_YOUR_KEY_HERE, and remove the Query line if you do not filter.</li>
          <li>Done → choose Anonymous access when asked (the key is already in the header) → Close &amp; Apply.</li>
          <li>For scheduled refresh in the Power BI service the API must be reachable from the internet over HTTPS, not localhost.</li>
        </ol>
        <pre className="bg-gray-50 border rounded p-3 text-xs overflow-x-auto">{sample}</pre>
        <p className="text-xs text-gray-500 mt-2">
          These reports contain names, user names and work locations. Share keys only with people who may see them.
        </p>
      </div>
    </div>
  );
}
