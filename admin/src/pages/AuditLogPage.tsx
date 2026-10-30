import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../services/api";
import { AuditPage } from "../types/api";

const PAGE_SIZE = 50;

/**
 * Read-only view of the audit trail (master prompt §61): who did what, when,
 * from where. Entries are written by the backend next to each action; there is
 * deliberately no way to edit or delete them from here.
 */
export default function AuditLogPage() {
  const [action, setAction] = useState("");
  const [entityType, setEntityType] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [offset, setOffset] = useState(0);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const params: Record<string, string | number> = { limit: PAGE_SIZE, offset };
  if (action) params.action = action;
  if (entityType.trim()) params.entity_type = entityType.trim();
  if (dateFrom) params.date_from = new Date(`${dateFrom}T00:00:00`).toISOString();
  if (dateTo) params.date_to = new Date(`${dateTo}T23:59:59`).toISOString();

  const actions = useQuery<string[]>({
    queryKey: ["audit-actions"],
    queryFn: async () => (await api.get("/audit/actions")).data,
  });

  const { data, isLoading, error, isFetching } = useQuery<AuditPage>({
    queryKey: ["audit", params],
    queryFn: async () => (await api.get("/audit", { params })).data,
    placeholderData: (prev) => prev,
  });

  function resetPaging<T>(setter: (v: T) => void) {
    return (v: T) => {
      setter(v);
      setOffset(0);
    };
  }

  async function exportCsv() {
    setExporting(true);
    setExportError(null);
    try {
      const { limit: _l, offset: _o, ...filters } = params;
      const resp = await api.get("/audit/export.csv", { params: filters, responseType: "blob" });
      const url = URL.createObjectURL(resp.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = "audit-log.csv";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setExportError("Could not export the audit log.");
    } finally {
      setExporting(false);
    }
  }

  if (error && !data) {
    const status = (error as { response?: { status?: number } }).response?.status;
    return (
      <div className="p-6 text-sm text-red-600">
        {status === 403
          ? "Your role is not permitted to view the audit log."
          : "Could not load the audit log from the backend."}
      </div>
    );
  }

  const total = data?.total ?? 0;
  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + PAGE_SIZE, total);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-semibold">Audit log</h1>
        <button
          onClick={exportCsv}
          disabled={exporting}
          className="text-sm border rounded px-3 py-1.5 bg-white hover:bg-gray-50 disabled:opacity-50"
        >
          {exporting ? "Exporting…" : "Export CSV"}
        </button>
      </div>
      {exportError && <p className="text-sm text-red-600 mb-2">{exportError}</p>}

      <div className="bg-white border rounded-lg p-3 mb-4 flex flex-wrap gap-3 items-end text-sm">
        <label className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">Action</span>
          <select
            className="border rounded px-2 py-1"
            value={action}
            onChange={(e) => resetPaging(setAction)(e.target.value)}
          >
            <option value="">All actions</option>
            {(actions.data ?? []).map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">Entity type</span>
          <input
            className="border rounded px-2 py-1 w-36"
            placeholder="e.g. content_release"
            value={entityType}
            onChange={(e) => resetPaging(setEntityType)(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">From</span>
          <input
            type="date"
            className="border rounded px-2 py-1"
            value={dateFrom}
            onChange={(e) => resetPaging(setDateFrom)(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">To</span>
          <input
            type="date"
            className="border rounded px-2 py-1"
            value={dateTo}
            onChange={(e) => resetPaging(setDateTo)(e.target.value)}
          />
        </label>
        {(action || entityType || dateFrom || dateTo) && (
          <button
            className="text-xs underline text-gray-600 pb-1.5"
            onClick={() => {
              setAction("");
              setEntityType("");
              setDateFrom("");
              setDateTo("");
              setOffset(0);
            }}
          >
            Clear filters
          </button>
        )}
      </div>

      <div className="bg-white border rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs text-gray-500">
            <tr>
              <th className="px-3 py-2">Time</th>
              <th className="px-3 py-2">Action</th>
              <th className="px-3 py-2">User</th>
              <th className="px-3 py-2">Entity</th>
              <th className="px-3 py-2">IP</th>
              <th className="px-3 py-2">Details</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={6} className="px-3 py-4 text-gray-500">
                  Loading…
                </td>
              </tr>
            )}
            {data?.items.map((e) => (
              <tr key={e.id} className="border-t align-top">
                <td className="px-3 py-2 whitespace-nowrap text-gray-600">{new Date(e.created_at).toLocaleString()}</td>
                <td className="px-3 py-2">
                  <span
                    className={`text-xs px-1.5 py-0.5 rounded ${
                      e.action === "LOGIN_FAILED" ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {e.action}
                  </span>
                </td>
                <td className="px-3 py-2">
                  {e.username ?? <span className="text-gray-400">—</span>}
                  {e.user_role && <div className="text-xs text-gray-400">{e.user_role.replace("_", " ")}</div>}
                </td>
                <td className="px-3 py-2 text-gray-600">{e.entity_type ?? "—"}</td>
                <td className="px-3 py-2 text-gray-600">{e.ip_address ?? "—"}</td>
                <td className="px-3 py-2 font-mono text-xs text-gray-600 max-w-md break-all">
                  {Object.keys(e.details).length ? JSON.stringify(e.details) : ""}
                </td>
              </tr>
            ))}
            {data && data.items.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-4 text-gray-500">
                  No entries match these filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between mt-3 text-sm text-gray-600">
        <span>
          {from}–{to} of {total} {isFetching && "· refreshing…"}
        </span>
        <div className="flex gap-2">
          <button
            disabled={offset === 0}
            onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            className="border rounded px-3 py-1 bg-white disabled:opacity-40"
          >
            Previous
          </button>
          <button
            disabled={offset + PAGE_SIZE >= total}
            onClick={() => setOffset(offset + PAGE_SIZE)}
            className="border rounded px-3 py-1 bg-white disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
