import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import { Boundary } from "../types/api";
import AreaPicker, { AreaValue, deepest, LEVELS, LEVEL_LABEL } from "../components/AreaPicker";

function errorText(err: unknown, fallback: string) {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
}

const TEMPLATE_ROWS = [
  ["country", "state", "lga", "ward", "facility"],
  ["Nigeria", "Example State", "Example LGA 1", "Example Ward A", "Example Health Facility 1"],
  ["Nigeria", "Example State", "Example LGA 1", "Example Ward A", "Example Health Facility 2"],
  ["Nigeria", "Example State", "Example LGA 1", "Example Ward B", ""],
  ["Nigeria", "Example State", "Example LGA 2", "", ""],
];

/** Saves the import template (UTF-8 with BOM so Excel opens it correctly). */
function downloadTemplate() {
  const csv = "\ufeff" + TEMPLATE_ROWS.map((r) => r.join(",")).join("\r\n") + "\r\n";
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = "administrative_areas_template.csv";
  a.click();
  URL.revokeObjectURL(url);
}

/** Country > State > LGA > Ward > Facility. SUPER_ADMIN manages the lists; users and reports use them. */
export default function BoundariesPage() {
  const queryClient = useQueryClient();
  const [area, setArea] = useState<AreaValue>({});
  const [form, setForm] = useState({ name: "", code: "" });
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  const parentId = deepest(area);
  const depth = LEVELS.filter((l) => area[l]).length; // 0..5
  const nextLevel = depth < LEVELS.length ? LEVELS[depth] : null;

  const children = useQuery<Boundary[]>({
    queryKey: ["boundaries-admin", nextLevel, parentId ?? "root"],
    queryFn: async () =>
      (await api.get("/boundaries", { params: { level: nextLevel, ...(parentId ? { parent_id: parentId } : {}), limit: 2000 } })).data,
    enabled: nextLevel !== null,
  });
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["boundaries"] });
    queryClient.invalidateQueries({ queryKey: ["boundaries-admin"] });
  };

  const add = useMutation({
    mutationFn: async () =>
      (
        await api.post("/boundaries", {
          level: nextLevel,
          name: form.name.trim(),
          code: form.code.trim() || null,
          parent_id: parentId,
        })
      ).data,
    onSuccess: () => {
      setForm({ name: "", code: "" });
      setMessage(null);
      refresh();
    },
    onError: (e) => setMessage({ ok: false, text: errorText(e, "Could not add it.") }),
  });

  const remove = useMutation({
    mutationFn: async (id: string) => api.delete(`/boundaries/${id}`),
    onSuccess: () => {
      setMessage(null);
      refresh();
    },
    onError: (e) => setMessage({ ok: false, text: errorText(e, "Could not delete it.") }),
  });

  const upload = useMutation({
    mutationFn: async (file: File) => {
      const body = new FormData();
      body.append("file", file);
      return (await api.post("/boundaries/import", body)).data;
    },
    onSuccess: (d) => {
      setMessage({ ok: true, text: `Imported. ${d.created} new area(s) added.` });
      refresh();
    },
    onError: (e) => setMessage({ ok: false, text: errorText(e, "Import failed.") }),
  });

  const input = "border rounded px-2 py-1.5 text-sm";
  return (
    <div className="p-6 max-w-4xl">
      <h1 className="text-xl font-semibold mb-1">Administrative areas</h1>
      <p className="text-sm text-gray-500 mb-5">
        Country &gt; State &gt; LGA &gt; Ward &gt; Facility. Users are placed in one of these, and reports roll up by them.
      </p>

      {message && <p className={`text-sm mb-4 ${message.ok ? "text-green-700" : "text-red-600"}`}>{message.text}</p>}

      <div className="bg-white border rounded-lg p-4 mb-6">
        <h2 className="text-sm font-medium mb-2">Browse</h2>
        <AreaPicker value={area} onChange={setArea} />
        {nextLevel ? (
          <>
            <h3 className="text-sm font-medium mt-5 mb-2">
              {LEVEL_LABEL[nextLevel]} list {parentId ? "under the selection" : ""}
            </h3>
            <ul className="divide-y border rounded mb-4 max-h-72 overflow-y-auto">
              {children.data?.length === 0 && <li className="px-3 py-2 text-sm text-gray-500">None yet.</li>}
              {children.data?.map((b) => (
                <li key={b.id} className="px-3 py-1.5 text-sm flex items-center justify-between">
                  <span>
                    {b.name} {b.code && <span className="text-xs text-gray-400">({b.code})</span>}
                  </span>
                  <button
                    className="text-xs text-red-500 underline"
                    onClick={() => window.confirm(`Delete ${b.name}?`) && remove.mutate(b.id)}
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
            <form
              className="flex flex-wrap items-end gap-2"
              onSubmit={(e) => {
                e.preventDefault();
                add.mutate();
              }}
            >
              <label className="text-xs text-gray-500">
                New {LEVEL_LABEL[nextLevel].toLowerCase()}
                <input required className={`${input} block`} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              </label>
              <label className="text-xs text-gray-500">
                Code (optional)
                <input className={`${input} block w-28`} value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
              </label>
              <button disabled={add.isPending} className="bg-gray-900 text-white text-sm rounded px-4 py-1.5 disabled:opacity-50">
                Add
              </button>
            </form>
          </>
        ) : (
          <p className="text-sm text-gray-500 mt-4">A facility is the lowest level.</p>
        )}
      </div>

      <div className="bg-white border rounded-lg p-4">
        <h2 className="text-sm font-medium mb-1">Import from CSV</h2>
        <p className="text-xs text-gray-500 mb-3">
          Columns: <code>country,state,lga,ward,facility</code>. A row may stop at any depth. Existing names are reused, so the same file can be
          imported again safely. Download the template, replace the example rows with your own, and keep the header row. If any row is wrong nothing is imported. Save from Excel as <em>CSV UTF-8</em>.
        </p>
        <button type="button" onClick={downloadTemplate} className="border text-sm rounded px-4 py-2 mr-2">
          Download template (CSV)
        </button>
        <label className="inline-block bg-gray-900 text-white text-sm rounded px-4 py-2 cursor-pointer">
          {upload.isPending ? "Importing…" : "Choose CSV file"}
          <input
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) upload.mutate(f);
              e.target.value = "";
            }}
          />
        </label>
      </div>
    </div>
  );
}
