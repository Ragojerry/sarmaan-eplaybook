import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import { useAuth } from "../services/auth";
import { LEARNER_ROLES, learnerRoleLabel } from "../learnerRoles";
import { LearnerRole, ModuleAudience, ToolItem, ToolItemType, ToolModule } from "../types/api";

const TYPES: Record<ToolItemType, string> = {
  DOCUMENT: "Document",
  SPREADSHEET: "Spreadsheet",
  PRESENTATION: "Presentation",
  PDF: "PDF",
  IMAGE: "Image",
  VIDEO_LINK: "Video link",
  WEBSITE: "Website",
  FORM: "Form",
  OTHER: "Other",
};
const HOSTS: Record<string, string> = {
  GOOGLE_DRIVE: "Google Drive",
  ONEDRIVE: "OneDrive",
  SHAREPOINT: "SharePoint",
  DROPBOX: "Dropbox",
  YOUTUBE: "YouTube",
};
const URL_NOTE =
  "The file is not stored in the app. The learner opens it online. Make sure the link sharing settings allow the intended people to open it.";
const STALE_DAYS = 365;

type ModuleDraft = { title: string; description: string; audience: ModuleAudience; learner_roles: LearnerRole[]; is_active: boolean };
type ItemDraft = {
  tool_module_id: string;
  title: string;
  description: string;
  type: ToolItemType;
  url: string;
  category: string;
  languages: string;
  audience: LearnerRole[];
  is_active: boolean;
  last_reviewed: string;
};
type ImportError = { row: number; title?: string | null; error: string };
type OpensPeriod = "30" | "90" | "365" | "all" | "custom";
type OpensData = { date_from: string | null; date_to: string | null; all_time: boolean; items: { item_id: string; title: string; deleted: boolean; opens: number }[] };

const PERIODS: { value: OpensPeriod; label: string }[] = [
  { value: "30", label: "Last 30 days" },
  { value: "90", label: "Last 90 days" },
  { value: "365", label: "Last 12 months" },
  { value: "all", label: "All time" },
  { value: "custom", label: "Custom dates" },
];

function isoDay(d: Date) {
  return d.toISOString().slice(0, 10);
}

/** Query for /tools/opens: preset periods end today (UTC); custom uses the chosen days (both inclusive). */
function opensParams(period: OpensPeriod, from: string, to: string): Record<string, string> {
  if (period === "all") return { all_time: "true" };
  if (period === "custom") return { ...(from ? { date_from: from } : {}), ...(to ? { date_to: to } : {}) };
  const start = new Date();
  start.setUTCDate(start.getUTCDate() - (Number(period) - 1));
  return { date_from: isoDay(start), date_to: isoDay(new Date()) };
}

const EMPTY_MODULE: ModuleDraft = { title: "", description: "", audience: "GENERAL", learner_roles: [], is_active: true };

function detail(err: unknown): unknown {
  return (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
}

function errorText(err: unknown, fallback: string) {
  const d = detail(err);
  if (typeof d === "string") return d;
  if (d && typeof d === "object" && "message" in d) return String((d as { message: unknown }).message);
  if (Array.isArray(d)) return "Please check the fields and try again.";
  return fallback;
}

// Same rules as the server (app/tools/links.py); the server has the final say.
function linkProblem(raw: string): string | null {
  const v = raw.trim();
  if (!v) return null;
  if (/\s/.test(v)) return "The link must not contain spaces.";
  try {
    const u = new URL(v);
    if (u.protocol !== "https:") return "Only https:// links are allowed.";
    if (u.username || u.password) return "Remove the user name or password from the link.";
    if (!u.hostname.includes(".")) return "The link needs a website address.";
  } catch {
    return "Only https:// links are allowed.";
  }
  return null;
}

function sameLink(url: string) {
  try {
    const u = new URL(url.trim());
    return `${u.hostname.toLowerCase()}${u.pathname.replace(/\/+$/, "")}${u.search}`;
  } catch {
    return url.trim();
  }
}

function audienceText(m: { audience: ModuleAudience; learner_roles: LearnerRole[] }) {
  return m.audience === "GENERAL" ? "All learner roles" : m.learner_roles.map(learnerRoleLabel).join(", ");
}

function stale(lastReviewed: string | null) {
  if (!lastReviewed) return true;
  return (Date.now() - new Date(lastReviewed).getTime()) / 86400000 > STALE_DAYS;
}

/** Opens the link from the admin's own browser (the server never opens it). */
function testLink(url: string) {
  if (!linkProblem(url) && url.trim()) window.open(url.trim(), "_blank", "noopener,noreferrer");
}

function RolePicker({ value, onChange, allLabel }: { value: LearnerRole[]; onChange: (v: LearnerRole[]) => void; allLabel: string }) {
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1">
      {LEARNER_ROLES.map((r) => (
        <label key={r.value} className="inline-flex items-center gap-1.5">
          <input
            type="checkbox"
            checked={value.includes(r.value)}
            onChange={(e) => onChange(e.target.checked ? [...value, r.value] : value.filter((x) => x !== r.value))}
          />
          {r.label}
        </label>
      ))}
      {value.length === 0 && <span className="text-xs text-gray-600">({allLabel})</span>}
    </div>
  );
}

/**
 * Tools repository: libraries of links (documents on a shared drive, forms,
 * images, websites) assigned to learner roles like training modules, but
 * completely separate from training: no tests, no completion, no progress, and
 * never part of reports. Only links are stored; learners open them online.
 * Content admins manage it; every change is recorded in the audit log.
 */
export default function ToolsPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const canEdit = user?.role === "CONTENT_ADMIN" || user?.role === "SUPER_ADMIN";
  const [message, setMessage] = useState<{ kind: "error" | "info"; text: string } | null>(null);
  const [moduleEdit, setModuleEdit] = useState<string | "new" | null>(null);
  const [moduleDraft, setModuleDraft] = useState<ModuleDraft>(EMPTY_MODULE);
  const [itemEdit, setItemEdit] = useState<string | "new" | null>(null);
  const [itemDraft, setItemDraft] = useState<ItemDraft | null>(null);
  const [filters, setFilters] = useState({ q: "", module: "", type: "", category: "", role: "", active: "" });
  const [importModule, setImportModule] = useState("");
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importErrors, setImportErrors] = useState<ImportError[]>([]);
  const [period, setPeriod] = useState<OpensPeriod>("90");
  const [customFrom, setCustomFrom] = useState("");
  const [customTo, setCustomTo] = useState("");

  const modules = useQuery<ToolModule[]>({ queryKey: ["tool-modules"], queryFn: async () => (await api.get("/tools/modules")).data });
  const items = useQuery<ToolItem[]>({ queryKey: ["tool-items"], queryFn: async () => (await api.get("/tools/items")).data });
  const badRange = period === "custom" && !!customFrom && !!customTo && customFrom > customTo;
  const opensQuery = opensParams(period, customFrom, customTo);
  const opens = useQuery<OpensData>({
    queryKey: ["tool-opens", opensQuery],
    queryFn: async () => (await api.get("/tools/opens", { params: opensQuery })).data,
    enabled: !badRange,
  });

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["tool-modules"] });
    queryClient.invalidateQueries({ queryKey: ["tool-items"] });
  };
  const fail = (fallback: string) => (e: unknown) => setMessage({ kind: "error", text: errorText(e, fallback) });
  const ok = (text: string) => () => {
    setMessage({ kind: "info", text });
    refresh();
  };

  const saveModule = useMutation({
    mutationFn: async () => {
      const body = { ...moduleDraft, learner_roles: moduleDraft.audience === "GENERAL" ? [] : moduleDraft.learner_roles };
      return moduleEdit === "new" ? (await api.post("/tools/modules", body)).data : (await api.put(`/tools/modules/${moduleEdit}`, body)).data;
    },
    onSuccess: () => {
      setModuleEdit(null);
      ok("Tools module saved. Phones get the change at their next sync.")();
    },
    onError: fail("Could not save the Tools module."),
  });
  const moduleActive = useMutation({
    mutationFn: async ({ id, active }: { id: string; active: boolean }) => api.put(`/tools/modules/${id}/active`, { active }),
    onSuccess: refresh,
    onError: fail("Could not change the Tools module."),
  });
  const moduleOrder = useMutation({
    mutationFn: async (ids: string[]) => api.post("/tools/modules/reorder", { ids }),
    onSuccess: refresh,
    onError: fail("Could not change the order."),
  });
  const moduleDelete = useMutation({
    mutationFn: async (id: string) => api.delete(`/tools/modules/${id}`),
    onSuccess: ok("Tools module deleted with its links. Phones remove them at their next sync."),
    onError: fail("Could not delete the Tools module."),
  });
  const saveItem = useMutation({
    mutationFn: async () => {
      const d = itemDraft!;
      const body = { ...d, last_reviewed: d.last_reviewed || null };
      return itemEdit === "new" ? (await api.post("/tools/items", body)).data : (await api.put(`/tools/items/${itemEdit}`, body)).data;
    },
    onSuccess: (saved: ToolItem) => {
      setItemEdit(null);
      ok(
        saved.duplicates.length
          ? `Saved. Note: the same link is also used by “${saved.duplicates.map((d) => d.title).join("”, “")}”.`
          : "Saved. Phones get the change at their next sync.",
      )();
    },
    onError: fail("Could not save the link."),
  });
  const itemActive = useMutation({
    mutationFn: async ({ id, active }: { id: string; active: boolean }) => api.put(`/tools/items/${id}/active`, { active }),
    onSuccess: refresh,
    onError: fail("Could not change the link."),
  });
  const itemOrder = useMutation({
    mutationFn: async ({ moduleId, ids }: { moduleId: string; ids: string[] }) => api.post(`/tools/modules/${moduleId}/items/reorder`, { ids }),
    onSuccess: refresh,
    onError: fail("Could not change the order."),
  });
  const itemDelete = useMutation({
    mutationFn: async (id: string) => api.delete(`/tools/items/${id}`),
    onSuccess: ok("Link deleted. Phones remove it at their next sync."),
    onError: fail("Could not delete the link."),
  });
  const importCsv = useMutation({
    mutationFn: async () => {
      const form = new FormData();
      form.append("file", importFile!);
      return (await api.post(`/tools/modules/${importModule}/items/import`, form)).data as { created: number; duplicates: { title: string }[] };
    },
    onSuccess: (r) => {
      setImportErrors([]);
      setImportFile(null);
      ok(`${r.created} link(s) imported.${r.duplicates.length ? ` ${r.duplicates.length} use a link that already exists.` : ""}`)();
    },
    onError: (e) => {
      const d = detail(e);
      setImportErrors(d && typeof d === "object" && "errors" in d ? ((d as { errors: ImportError[] }).errors ?? []) : []);
      fail("Could not import the file.")(e);
    },
  });

  const mods = modules.data ?? [];
  const all = items.data ?? [];
  const moduleTitle = (id: string) => mods.find((m) => m.id === id)?.title ?? "—";
  const categories = useMemo(() => [...new Set(all.map((i) => i.category).filter(Boolean) as string[])].sort(), [all]);
  const shown = all.filter((i) => {
    const q = filters.q.trim().toLowerCase();
    if (q && ![i.title, i.description ?? "", i.url, i.category ?? ""].some((t) => t.toLowerCase().includes(q))) return false;
    if (filters.module && i.tool_module_id !== filters.module) return false;
    if (filters.type && i.type !== filters.type) return false;
    if (filters.category && (i.category ?? "") !== filters.category) return false;
    if (filters.role) {
      const m = mods.find((x) => x.id === i.tool_module_id);
      const moduleHas = m && (m.audience === "GENERAL" || m.learner_roles.includes(filters.role as LearnerRole));
      if (!moduleHas || (i.audience.length > 0 && !i.audience.includes(filters.role as LearnerRole))) return false;
    }
    if (filters.active && String(i.is_active) !== filters.active) return false;
    return true;
  });
  // Reordering needs one module's full list: a module is chosen and nothing else filters the rows.
  const canReorder =
    canEdit && !!filters.module && !filters.q && !filters.type && !filters.category && !filters.role && !filters.active;

  const moveModule = (index: number, by: number) => {
    const ids = mods.map((m) => m.id);
    const [id] = ids.splice(index, 1);
    ids.splice(index + by, 0, id);
    moduleOrder.mutate(ids);
  };
  const moveItem = (index: number, by: number) => {
    const ids = shown.map((i) => i.id);
    const [id] = ids.splice(index, 1);
    ids.splice(index + by, 0, id);
    itemOrder.mutate({ moduleId: filters.module, ids });
  };
  const startItem = (i: ToolItem | null) => {
    setMessage(null);
    setItemEdit(i ? i.id : "new");
    setItemDraft(
      i
        ? {
            tool_module_id: i.tool_module_id,
            title: i.title,
            description: i.description ?? "",
            type: i.type,
            url: i.url,
            category: i.category ?? "",
            languages: i.languages ?? "",
            audience: i.audience,
            is_active: i.is_active,
            last_reviewed: i.last_reviewed ?? "",
          }
        : {
            tool_module_id: filters.module || mods[0]?.id || "",
            title: "",
            description: "",
            type: "DOCUMENT",
            url: "",
            category: "",
            languages: "",
            audience: [],
            is_active: true,
            last_reviewed: "",
          },
    );
  };

  const draftProblem = itemDraft ? linkProblem(itemDraft.url) : null;
  const draftDuplicates = itemDraft?.url.trim()
    ? all.filter((i) => i.id !== itemEdit && sameLink(i.url) === sameLink(itemDraft.url))
    : [];

  return (
    <div className="p-6 space-y-8">
      <div>
        <h1 className="text-xl font-semibold">Tools repository</h1>
        <p className="text-sm text-gray-500 mt-1 max-w-3xl">
          Libraries of links to documents, forms, images and websites, assigned to learner roles. Completely separate from
          training: no tests, no completion and no progress, and never part of training reports. Only the links are stored;
          learners open them online. Every change is recorded in the audit log.
        </p>
      </div>
      {message && <p className={`text-sm ${message.kind === "error" ? "text-red-600" : "text-green-700"}`}>{message.text}</p>}

      {/* ---------- Tools modules ---------- */}
      <section>
        <h2 className="font-medium mb-2">Tools modules</h2>
        <div className="bg-white border rounded-lg overflow-x-auto max-w-4xl">
          <table className="w-full text-sm">
            <thead className="text-left text-xs text-gray-500 border-b">
              <tr>
                <th className="px-3 py-2 w-20">Order</th>
                <th className="px-3 py-2">Title</th>
                <th className="px-3 py-2">Assigned to</th>
                <th className="px-3 py-2">Links</th>
                <th className="px-3 py-2">Active</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {mods.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-3 py-4 text-gray-600">No Tools module yet. Phones show no Tools section until one has links.</td>
                </tr>
              )}
              {mods.map((m, i) => (
                <tr key={m.id} className={`border-b last:border-0 ${m.is_active ? "" : "bg-gray-50"}`}>
                  <td className="px-3 py-2 whitespace-nowrap">
                    {canEdit ? (
                      <>
                        <button className="px-1.5 border rounded disabled:opacity-30" disabled={i === 0} onClick={() => moveModule(i, -1)} aria-label={`Move ${m.title} up`}>
                          ↑
                        </button>{" "}
                        <button className="px-1.5 border rounded disabled:opacity-30" disabled={i === mods.length - 1} onClick={() => moveModule(i, 1)} aria-label={`Move ${m.title} down`}>
                          ↓
                        </button>
                      </>
                    ) : (
                      i + 1
                    )}
                  </td>
                  <td className="px-3 py-2">
                    <div className="font-medium">{m.title}</div>
                    {m.description && <div className="text-xs text-gray-600">{m.description}</div>}
                  </td>
                  <td className="px-3 py-2 text-gray-700">{audienceText(m)}</td>
                  <td className="px-3 py-2">{m.item_count}</td>
                  <td className="px-3 py-2">
                    {canEdit ? (
                      <label className="inline-flex items-center gap-1.5">
                        <input type="checkbox" checked={m.is_active} onChange={(e) => moduleActive.mutate({ id: m.id, active: e.target.checked })} />
                        {m.is_active ? "Active" : "Inactive"}
                      </label>
                    ) : m.is_active ? (
                      "Active"
                    ) : (
                      "Inactive"
                    )}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-right">
                    {canEdit && (
                      <>
                        <button
                          className="text-xs underline mr-3"
                          onClick={() => {
                            setModuleEdit(m.id);
                            setModuleDraft({ title: m.title, description: m.description ?? "", audience: m.audience, learner_roles: m.learner_roles, is_active: m.is_active });
                          }}
                        >
                          Edit
                        </button>
                        <button
                          className="text-xs underline text-red-700"
                          onClick={() => {
                            if (window.confirm(`Delete “${m.title}” and its ${m.item_count} link(s)? Phones remove them at their next sync.`))
                              moduleDelete.mutate(m.id);
                          }}
                        >
                          Delete
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {canEdit && moduleEdit === null && (
          <button
            className="mt-3 bg-gray-900 text-white rounded px-4 py-1.5 text-sm"
            onClick={() => {
              setModuleEdit("new");
              setModuleDraft(EMPTY_MODULE);
            }}
          >
            Add Tools module
          </button>
        )}
        {canEdit && moduleEdit !== null && (
          <form
            className="mt-3 bg-white border rounded-lg p-4 space-y-3 text-sm max-w-2xl"
            onSubmit={(e) => {
              e.preventDefault();
              saveModule.mutate();
            }}
          >
            <h3 className="font-medium">{moduleEdit === "new" ? "Add a Tools module" : "Edit Tools module"}</h3>
            <label className="block">
              <span className="text-xs text-gray-500">Title</span>
              <input required maxLength={120} className="mt-1 w-full border rounded px-2 py-1" value={moduleDraft.title} onChange={(e) => setModuleDraft({ ...moduleDraft, title: e.target.value })} />
            </label>
            <label className="block">
              <span className="text-xs text-gray-500">Description (optional)</span>
              <textarea rows={2} maxLength={2000} className="mt-1 w-full border rounded px-2 py-1" value={moduleDraft.description} onChange={(e) => setModuleDraft({ ...moduleDraft, description: e.target.value })} />
            </label>
            <fieldset>
              <legend className="text-xs text-gray-500">Assigned to (same roles as training modules)</legend>
              <label className="inline-flex items-center gap-1.5 mr-4">
                <input type="radio" checked={moduleDraft.audience === "GENERAL"} onChange={() => setModuleDraft({ ...moduleDraft, audience: "GENERAL" })} />
                General: every learner role
              </label>
              <label className="inline-flex items-center gap-1.5">
                <input type="radio" checked={moduleDraft.audience === "ROLE_SPECIFIC"} onChange={() => setModuleDraft({ ...moduleDraft, audience: "ROLE_SPECIFIC" })} />
                Role-specific
              </label>
              {moduleDraft.audience === "ROLE_SPECIFIC" && (
                <RolePicker value={moduleDraft.learner_roles} onChange={(v) => setModuleDraft({ ...moduleDraft, learner_roles: v })} allLabel="choose at least one" />
              )}
            </fieldset>
            <label className="inline-flex items-center gap-2">
              <input type="checkbox" checked={moduleDraft.is_active} onChange={(e) => setModuleDraft({ ...moduleDraft, is_active: e.target.checked })} />
              Active (shown on phones)
            </label>
            <div className="space-x-3">
              <button disabled={saveModule.isPending} className="bg-gray-900 text-white rounded px-4 py-1.5 disabled:opacity-50">
                {saveModule.isPending ? "Saving…" : "Save Tools module"}
              </button>
              <button type="button" className="text-xs underline" onClick={() => setModuleEdit(null)}>
                Cancel
              </button>
            </div>
          </form>
        )}
      </section>

      {/* ---------- links ---------- */}
      <section>
        <h2 className="font-medium mb-2">Links</h2>
        <div className="flex flex-wrap gap-2 mb-3 text-sm">
          <input
            placeholder="Search title, description, link…"
            className="border rounded px-2 py-1 w-64"
            value={filters.q}
            onChange={(e) => setFilters({ ...filters, q: e.target.value })}
            aria-label="Search links"
          />
          <select className="border rounded px-2 py-1" value={filters.module} onChange={(e) => setFilters({ ...filters, module: e.target.value })} aria-label="Tools module">
            <option value="">All Tools modules</option>
            {mods.map((m) => (
              <option key={m.id} value={m.id}>
                {m.title}
              </option>
            ))}
          </select>
          <select className="border rounded px-2 py-1" value={filters.type} onChange={(e) => setFilters({ ...filters, type: e.target.value })} aria-label="Type">
            <option value="">All types</option>
            {(Object.keys(TYPES) as ToolItemType[]).map((t) => (
              <option key={t} value={t}>
                {TYPES[t]}
              </option>
            ))}
          </select>
          <select className="border rounded px-2 py-1" value={filters.category} onChange={(e) => setFilters({ ...filters, category: e.target.value })} aria-label="Category">
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <select className="border rounded px-2 py-1" value={filters.role} onChange={(e) => setFilters({ ...filters, role: e.target.value })} aria-label="Learner role">
            <option value="">All roles</option>
            {LEARNER_ROLES.map((r) => (
              <option key={r.value} value={r.value}>
                Seen by {r.label}
              </option>
            ))}
          </select>
          <select className="border rounded px-2 py-1" value={filters.active} onChange={(e) => setFilters({ ...filters, active: e.target.value })} aria-label="Active">
            <option value="">Active and inactive</option>
            <option value="true">Active only</option>
            <option value="false">Inactive only</option>
          </select>
        </div>
        {canEdit && !canReorder && <p className="text-xs text-gray-600 mb-2">To change the order of links, choose one Tools module and clear the other filters.</p>}

        <div className="bg-white border rounded-lg overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-xs text-gray-500 border-b">
              <tr>
                {canReorder && <th className="px-3 py-2 w-20">Order</th>}
                <th className="px-3 py-2">Type</th>
                <th className="px-3 py-2">Title</th>
                <th className="px-3 py-2">Category</th>
                <th className="px-3 py-2">Link</th>
                <th className="px-3 py-2">Seen by</th>
                <th className="px-3 py-2">Last reviewed</th>
                <th className="px-3 py-2">Active</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {shown.length === 0 && (
                <tr>
                  <td colSpan={9} className="px-3 py-4 text-gray-600">{all.length ? "No link matches the filters." : "No links yet."}</td>
                </tr>
              )}
              {shown.map((i, n) => (
                <tr key={i.id} className={`border-b last:border-0 align-top ${i.is_active ? "" : "bg-gray-50"}`}>
                  {canReorder && (
                    <td className="px-3 py-2 whitespace-nowrap">
                      <button className="px-1.5 border rounded disabled:opacity-30" disabled={n === 0} onClick={() => moveItem(n, -1)} aria-label={`Move ${i.title} up`}>
                        ↑
                      </button>{" "}
                      <button className="px-1.5 border rounded disabled:opacity-30" disabled={n === shown.length - 1} onClick={() => moveItem(n, 1)} aria-label={`Move ${i.title} down`}>
                        ↓
                      </button>
                    </td>
                  )}
                  <td className="px-3 py-2 whitespace-nowrap">{TYPES[i.type]}</td>
                  <td className="px-3 py-2">
                    <div className="font-medium">{i.title}</div>
                    {i.description && <div className="text-xs text-gray-600">{i.description}</div>}
                    {!filters.module && <div className="text-xs text-gray-600">in {moduleTitle(i.tool_module_id)}</div>}
                    {i.duplicates.length > 0 && (
                      <div className="text-xs text-amber-800 mt-1">⚠ Same link as: {i.duplicates.map((d) => d.title).join(", ")}</div>
                    )}
                  </td>
                  <td className="px-3 py-2 text-gray-700">{i.category ?? "—"}</td>
                  <td className="px-3 py-2 max-w-xs">
                    {i.host && <div className="text-xs font-medium">{HOSTS[i.host] ?? i.host}</div>}
                    <div className="font-mono text-xs break-all text-gray-700">{i.url}</div>
                    <button className="text-xs underline" onClick={() => testLink(i.url)}>
                      Test link
                    </button>
                  </td>
                  <td className="px-3 py-2 text-gray-700">{i.audience.length ? i.audience.map(learnerRoleLabel).join(", ") : "Everyone in the module"}</td>
                  <td className={`px-3 py-2 whitespace-nowrap ${stale(i.last_reviewed) ? "text-amber-800 font-medium" : "text-gray-700"}`}>
                    {i.last_reviewed ?? "Never"}
                    {stale(i.last_reviewed) && <div className="text-xs">Review due</div>}
                  </td>
                  <td className="px-3 py-2">
                    {canEdit ? (
                      <label className="inline-flex items-center gap-1.5">
                        <input type="checkbox" checked={i.is_active} onChange={(e) => itemActive.mutate({ id: i.id, active: e.target.checked })} />
                        {i.is_active ? "Active" : "Inactive"}
                      </label>
                    ) : i.is_active ? (
                      "Active"
                    ) : (
                      "Inactive"
                    )}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-right">
                    {canEdit && (
                      <>
                        <button className="text-xs underline mr-3" onClick={() => startItem(i)}>
                          Edit
                        </button>
                        <button
                          className="text-xs underline text-red-700"
                          onClick={() => {
                            if (window.confirm(`Delete “${i.title}”? Phones remove it at their next sync.`)) itemDelete.mutate(i.id);
                          }}
                        >
                          Delete
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!canEdit && <p className="text-xs text-gray-500 mt-2">You can view the Tools repository. Only content admins can change it.</p>}

        {canEdit && itemEdit === null && mods.length > 0 && (
          <button className="mt-3 bg-gray-900 text-white rounded px-4 py-1.5 text-sm" onClick={() => startItem(null)}>
            Add link
          </button>
        )}
        {canEdit && itemEdit !== null && itemDraft && (
          <form
            className="mt-3 bg-white border rounded-lg p-4 space-y-3 text-sm max-w-2xl"
            onSubmit={(e) => {
              e.preventDefault();
              if (!draftProblem) saveItem.mutate();
            }}
          >
            <h3 className="font-medium">{itemEdit === "new" ? "Add a link" : "Edit link"}</h3>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block">
                <span className="text-xs text-gray-500">Tools module</span>
                <select className="mt-1 w-full border rounded px-2 py-1" value={itemDraft.tool_module_id} onChange={(e) => setItemDraft({ ...itemDraft, tool_module_id: e.target.value })}>
                  {mods.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.title}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="text-xs text-gray-500">Type</span>
                <select className="mt-1 w-full border rounded px-2 py-1" value={itemDraft.type} onChange={(e) => setItemDraft({ ...itemDraft, type: e.target.value as ToolItemType })}>
                  {(Object.keys(TYPES) as ToolItemType[]).map((t) => (
                    <option key={t} value={t}>
                      {TYPES[t]}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <label className="block">
              <span className="text-xs text-gray-500">Title</span>
              <input required maxLength={150} className="mt-1 w-full border rounded px-2 py-1" value={itemDraft.title} onChange={(e) => setItemDraft({ ...itemDraft, title: e.target.value })} />
            </label>
            <label className="block">
              <span className="text-xs text-gray-500">Short description (optional)</span>
              <textarea rows={2} maxLength={500} className="mt-1 w-full border rounded px-2 py-1" value={itemDraft.description} onChange={(e) => setItemDraft({ ...itemDraft, description: e.target.value })} />
            </label>
            <div>
              <label className="block">
                <span className="text-xs text-gray-500">Link (https://)</span>
                <input
                  required
                  maxLength={2000}
                  inputMode="url"
                  placeholder="https://drive.google.com/…"
                  className={`mt-1 w-full border rounded px-2 py-1 font-mono ${draftProblem ? "border-red-600" : ""}`}
                  value={itemDraft.url}
                  onChange={(e) => setItemDraft({ ...itemDraft, url: e.target.value })}
                  aria-invalid={!!draftProblem}
                  aria-describedby="tool-url-note"
                />
              </label>
              {draftProblem && <p className="text-xs text-red-600">{draftProblem}</p>}
              <p id="tool-url-note" className="text-xs text-gray-700 mt-1 bg-gray-100 rounded px-2 py-1.5">
                {URL_NOTE}
              </p>
              {draftDuplicates.length > 0 && (
                <p className="text-xs text-amber-800 mt-1">⚠ This link is already used by: {draftDuplicates.map((d) => d.title).join(", ")}</p>
              )}
              <button type="button" className="text-xs underline mt-1 disabled:opacity-40" disabled={!!draftProblem || !itemDraft.url.trim()} onClick={() => testLink(itemDraft.url)}>
                Test link (opens in a new tab)
              </button>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <label className="block">
                <span className="text-xs text-gray-500">Category (optional)</span>
                <input list="tool-categories" maxLength={80} placeholder="e.g. Job aids" className="mt-1 w-full border rounded px-2 py-1" value={itemDraft.category} onChange={(e) => setItemDraft({ ...itemDraft, category: e.target.value })} />
                <datalist id="tool-categories">
                  {categories.map((c) => (
                    <option key={c} value={c} />
                  ))}
                </datalist>
              </label>
              <label className="block">
                <span className="text-xs text-gray-500">Languages (optional)</span>
                <input maxLength={120} placeholder="e.g. English, Hausa" className="mt-1 w-full border rounded px-2 py-1" value={itemDraft.languages} onChange={(e) => setItemDraft({ ...itemDraft, languages: e.target.value })} />
              </label>
              <label className="block">
                <span className="text-xs text-gray-500">Last reviewed (optional)</span>
                <input type="date" className="mt-1 w-full border rounded px-2 py-1" value={itemDraft.last_reviewed} onChange={(e) => setItemDraft({ ...itemDraft, last_reviewed: e.target.value })} />
              </label>
            </div>
            <fieldset>
              <legend className="text-xs text-gray-500">Seen by (narrows the module's roles; none ticked = everyone the module is assigned to)</legend>
              <RolePicker value={itemDraft.audience} onChange={(v) => setItemDraft({ ...itemDraft, audience: v })} allLabel="everyone in the module" />
            </fieldset>
            <label className="inline-flex items-center gap-2">
              <input type="checkbox" checked={itemDraft.is_active} onChange={(e) => setItemDraft({ ...itemDraft, is_active: e.target.checked })} />
              Active (shown on phones)
            </label>
            <div className="space-x-3">
              <button disabled={saveItem.isPending || !!draftProblem} className="bg-gray-900 text-white rounded px-4 py-1.5 disabled:opacity-50">
                {saveItem.isPending ? "Saving…" : "Save link"}
              </button>
              <button type="button" className="text-xs underline" onClick={() => setItemEdit(null)}>
                Cancel
              </button>
            </div>
          </form>
        )}
      </section>

      {/* ---------- CSV import ---------- */}
      {canEdit && mods.length > 0 && (
        <section className="max-w-2xl">
          <h2 className="font-medium mb-1">Import links from CSV</h2>
          <p className="text-xs text-gray-600 mb-2">
            Columns: <span className="font-mono">title, description, type, url, category</span> (and optionally{" "}
            <span className="font-mono">languages</span>), with a header row, saved as CSV UTF-8. Type is one of:{" "}
            {Object.keys(TYPES).join(", ")}. If any row is invalid, nothing is imported and every problem is listed below.
          </p>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <select className="border rounded px-2 py-1" value={importModule} onChange={(e) => setImportModule(e.target.value)} aria-label="Import into">
              <option value="">Import into…</option>
              {mods.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.title}
                </option>
              ))}
            </select>
            <input type="file" accept=".csv,text/csv" onChange={(e) => setImportFile(e.target.files?.[0] ?? null)} aria-label="CSV file" />
            <button
              disabled={!importModule || !importFile || importCsv.isPending}
              className="bg-gray-900 text-white rounded px-4 py-1.5 disabled:opacity-50"
              onClick={() => importCsv.mutate()}
            >
              {importCsv.isPending ? "Importing…" : "Import"}
            </button>
          </div>
          {importErrors.length > 0 && (
            <table className="mt-3 w-full text-sm bg-white border rounded">
              <thead className="text-left text-xs text-gray-500 border-b">
                <tr>
                  <th className="px-3 py-1.5">Line</th>
                  <th className="px-3 py-1.5">Title</th>
                  <th className="px-3 py-1.5">Problem</th>
                </tr>
              </thead>
              <tbody>
                {importErrors.map((e) => (
                  <tr key={e.row} className="border-b last:border-0">
                    <td className="px-3 py-1.5">{e.row}</td>
                    <td className="px-3 py-1.5">{e.title ?? "—"}</td>
                    <td className="px-3 py-1.5 text-red-700">{e.error}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {/* ---------- most opened ---------- */}
      <section className="max-w-2xl">
        <h2 className="font-medium mb-1">Most opened tools</h2>
        <p className="text-xs text-gray-600 mb-2">
          From phones whose users agreed to share usage statistics. Counts only, no names. Not part of training reports.
        </p>
        <div className="flex flex-wrap items-end gap-2 mb-2 text-sm">
          <label className="block">
            <span className="text-xs text-gray-500">Period</span>
            <select className="mt-1 block border rounded px-2 py-1" value={period} onChange={(e) => setPeriod(e.target.value as OpensPeriod)}>
              {PERIODS.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
          </label>
          {period === "custom" && (
            <>
              <label className="block">
                <span className="text-xs text-gray-500">From</span>
                <input type="date" className="mt-1 block border rounded px-2 py-1" value={customFrom} max={customTo || undefined} onChange={(e) => setCustomFrom(e.target.value)} />
              </label>
              <label className="block">
                <span className="text-xs text-gray-500">To</span>
                <input type="date" className="mt-1 block border rounded px-2 py-1" value={customTo} min={customFrom || undefined} onChange={(e) => setCustomTo(e.target.value)} />
              </label>
            </>
          )}
        </div>
        {badRange && <p className="text-sm text-red-600 mb-2">The start date is after the end date.</p>}
        {opens.data && (
          <p className="text-xs text-gray-600 mb-2">
            {opens.data.all_time
              ? "Showing all time."
              : `Showing ${opens.data.date_from ?? "the beginning"} to ${opens.data.date_to ?? "today"} (UTC, both days included).`}
          </p>
        )}
        {badRange ? null : opens.data && opens.data.items.length === 0 ? (
          <p className="text-sm text-gray-600">No opens recorded in this period.</p>
        ) : (
          <table className="w-full text-sm bg-white border rounded">
            <thead className="text-left text-xs text-gray-500 border-b">
              <tr>
                <th className="px-3 py-1.5">Link</th>
                <th className="px-3 py-1.5 text-right">Opens</th>
              </tr>
            </thead>
            <tbody>
              {(opens.data?.items ?? []).slice(0, 20).map((r) => (
                <tr key={r.item_id} className="border-b last:border-0">
                  <td className="px-3 py-1.5">
                    {r.title}
                    {r.deleted && <span className="text-xs text-gray-600"> (deleted)</span>}
                  </td>
                  <td className="px-3 py-1.5 text-right">{r.opens}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
