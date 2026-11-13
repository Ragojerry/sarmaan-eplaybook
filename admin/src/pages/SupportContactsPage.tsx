import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import { useAuth } from "../services/auth";
import { LEARNER_ROLES, learnerRoleLabel } from "../learnerRoles";
import { LearnerRole, SupportContact, SupportContactType } from "../types/api";

type Draft = {
  type: SupportContactType;
  label: string;
  value: string;
  whatsapp_message: string;
  email_subject: string;
  include_app_version: boolean;
  availability: string;
  languages: string;
  audience: LearnerRole[];
  is_active: boolean;
};

const EMPTY: Draft = {
  type: "PHONE",
  label: "",
  value: "",
  whatsapp_message: "",
  email_subject: "",
  include_app_version: false,
  availability: "",
  languages: "",
  audience: [],
  is_active: true,
};

const TYPES: Record<SupportContactType, { name: string; valueLabel: string; placeholder: string; hint: string }> = {
  PHONE: { name: "Phone call", valueLabel: "Phone number", placeholder: "+234…", hint: "International format: + then the country code and number." },
  SMS: { name: "SMS", valueLabel: "Phone number for SMS", placeholder: "+234…", hint: "International format: + then the country code and number." },
  EMAIL: { name: "Email", valueLabel: "Email address", placeholder: "name@example.org", hint: "One address." },
  WHATSAPP: { name: "WhatsApp", valueLabel: "WhatsApp number", placeholder: "+234…", hint: "The number registered on WhatsApp, international format." },
  LINK: { name: "Link", valueLabel: "Web address", placeholder: "https://…", hint: "Must start with https://." },
};

// Same rules as the server (app/support/validation.py); the server has the final say.
const NUMBER = /^\+[1-9]\d{7,14}$/;
const EMAIL = /^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+$/;

function valueProblem(type: SupportContactType, raw: string): string | null {
  const v = raw.trim();
  if (!v) return null;
  if (type === "PHONE" || type === "SMS" || type === "WHATSAPP")
    return NUMBER.test(v.replace(/ /g, "")) ? null : "Use international format: + followed by digits only (spaces are fine).";
  if (type === "EMAIL") return EMAIL.test(v) && !v.includes("..") ? null : "This is not a valid email address.";
  try {
    const u = new URL(v);
    return u.protocol === "https:" && u.hostname.includes(".") && !/\s/.test(v) ? null : "Links must start with https://.";
  } catch {
    return "Links must start with https://.";
  }
}

function errorText(err: unknown, fallback: string) {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return "Please check the fields and try again.";
  return fallback;
}

function toDraft(c: SupportContact): Draft {
  return {
    type: c.type,
    label: c.label,
    value: c.value,
    whatsapp_message: c.whatsapp_message ?? "",
    email_subject: c.email_subject ?? "",
    include_app_version: c.include_app_version,
    availability: c.availability ?? "",
    languages: c.languages ?? "",
    audience: c.audience,
    is_active: c.is_active,
  };
}

function audienceText(audience: LearnerRole[]) {
  return audience.length ? audience.map(learnerRoleLabel).join(", ") : "All learners";
}

/** Small line icons per type. The type name is always written next to the icon. */
export function ContactIcon({ type, className = "w-4 h-4" }: { type: SupportContactType; className?: string }) {
  const paths: Record<SupportContactType, string> = {
    PHONE: "M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2",
    SMS: "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2zM8 9h8M8 13h5",
    EMAIL: "M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zM22 6l-10 7L2 6",
    WHATSAPP: "M3 21l1.7-5A9 9 0 1 1 8 19.3zM9 8.5c0 3.5 3 6.5 6.5 6.5l1-1.5-2-1-1 1a5 5 0 0 1-3-3l1-1-1-2z",
    LINK: "M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1",
  };
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={paths[type]} />
    </svg>
  );
}

/**
 * The people learners can reach from the Support deck on the phone's Ask tab.
 * Phones download the active contacts for their learner role at every sync and
 * keep them for offline use; with no active contact the deck is hidden.
 * Content admins manage the list; every change is recorded in the audit log.
 */
export default function SupportContactsPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const canEdit = user?.role === "CONTENT_ADMIN" || user?.role === "SUPER_ADMIN";
  const [editing, setEditing] = useState<string | "new" | null>(null);
  const [draft, setDraft] = useState<Draft>(EMPTY);
  const [message, setMessage] = useState<{ kind: "error" | "info"; text: string } | null>(null);
  const [noteDraft, setNoteDraft] = useState<string | null>(null);

  const contacts = useQuery<SupportContact[]>({
    queryKey: ["support-contacts"],
    queryFn: async () => (await api.get("/support-contacts")).data,
  });
  const settings = useQuery<{ note: string; note_max: number }>({
    queryKey: ["support-contacts-settings"],
    queryFn: async () => (await api.get("/support-contacts/settings")).data,
  });

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["support-contacts"] });
  const fail = (fallback: string) => (e: unknown) => setMessage({ kind: "error", text: errorText(e, fallback) });

  const save = useMutation({
    mutationFn: async () => {
      return editing === "new"
        ? (await api.post("/support-contacts", draft)).data
        : (await api.put(`/support-contacts/${editing}`, draft)).data;
    },
    onSuccess: () => {
      setMessage({ kind: "info", text: "Saved. Phones get the change at their next sync." });
      setEditing(null);
      refresh();
    },
    onError: fail("Could not save the contact."),
  });
  const setActive = useMutation({
    mutationFn: async ({ id, active }: { id: string; active: boolean }) => (await api.put(`/support-contacts/${id}/active`, { active })).data,
    onSuccess: refresh,
    onError: fail("Could not change the contact."),
  });
  const reorder = useMutation({
    mutationFn: async (ids: string[]) => (await api.post("/support-contacts/reorder", { ids })).data,
    onSuccess: (data) => queryClient.setQueryData(["support-contacts"], data),
    onError: fail("Could not change the order."),
  });
  const remove = useMutation({
    mutationFn: async (id: string) => api.delete(`/support-contacts/${id}`),
    onSuccess: () => {
      setMessage({ kind: "info", text: "Contact deleted. Phones remove it at their next sync." });
      setEditing(null);
      refresh();
    },
    onError: fail("Could not delete the contact."),
  });
  const saveNote = useMutation({
    mutationFn: async (note: string) => (await api.put("/support-contacts/settings", { note })).data,
    onSuccess: (data) => {
      queryClient.setQueryData(["support-contacts-settings"], data);
      setNoteDraft(null);
      setMessage({ kind: "info", text: data.note ? "Note saved." : "Note removed: the deck shows no note." });
    },
    onError: fail("Could not save the note."),
  });

  const rows = contacts.data ?? [];
  const move = (index: number, by: number) => {
    const ids = rows.map((c) => c.id);
    const [id] = ids.splice(index, 1);
    ids.splice(index + by, 0, id);
    reorder.mutate(ids);
  };
  const startEdit = (c: SupportContact | null) => {
    setMessage(null);
    setEditing(c ? c.id : "new");
    setDraft(c ? toDraft(c) : EMPTY);
  };

  const problem = valueProblem(draft.type, draft.value);
  const isNumber = draft.type === "PHONE" || draft.type === "SMS" || draft.type === "WHATSAPP";
  const note = noteDraft ?? settings.data?.note ?? "";

  // The preview shows the saved active contacts, with the one being edited as it would look after saving.
  const preview: Draft[] = rows
    .filter((c) => c.id !== editing)
    .map(toDraft)
    .concat(editing ? [draft] : [])
    .filter((d) => d.is_active && d.label.trim() && d.value.trim());
  if (editing && editing !== "new") {
    const at = rows.findIndex((c) => c.id === editing);
    const mine = preview.pop();
    if (mine) preview.splice(Math.min(at, preview.length), 0, mine);
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-xl font-semibold">Support contacts</h1>
        <p className="text-sm text-gray-500 mt-1 max-w-3xl">
          Ways for learners to reach a real person from the “Need help from a person?” deck on the Ask tab, and under any
          question the app could not answer. Phones keep the active contacts for offline use (calls and SMS work offline;
          email, WhatsApp and links need internet). With no active contact the deck is hidden. Every change is recorded in
          the audit log.
        </p>
      </div>

      {message && <p className={`text-sm mb-4 ${message.kind === "error" ? "text-red-600" : "text-green-700"}`}>{message.text}</p>}

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-6 min-w-0">
          <div className="bg-white border rounded-lg overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-xs text-gray-500 border-b">
                <tr>
                  <th className="px-3 py-2 w-20">Order</th>
                  <th className="px-3 py-2">Type</th>
                  <th className="px-3 py-2">Label</th>
                  <th className="px-3 py-2">Value</th>
                  <th className="px-3 py-2">Availability</th>
                  <th className="px-3 py-2">Audience</th>
                  <th className="px-3 py-2">Active</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {contacts.isLoading && (
                  <tr>
                    <td colSpan={8} className="px-3 py-4 text-gray-500">Loading…</td>
                  </tr>
                )}
                {!contacts.isLoading && rows.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-3 py-4 text-gray-600">No support contacts yet. The deck is hidden on phones until you add one.</td>
                  </tr>
                )}
                {rows.map((c, i) => (
                  <tr key={c.id} className={`border-b last:border-0 ${c.is_active ? "" : "bg-gray-50"}`}>
                    <td className="px-3 py-2 whitespace-nowrap">
                      {canEdit ? (
                        <>
                          <button
                            className="px-1.5 border rounded disabled:opacity-30"
                            disabled={i === 0 || reorder.isPending}
                            onClick={() => move(i, -1)}
                            aria-label={`Move ${c.label} up`}
                          >
                            ↑
                          </button>{" "}
                          <button
                            className="px-1.5 border rounded disabled:opacity-30"
                            disabled={i === rows.length - 1 || reorder.isPending}
                            onClick={() => move(i, 1)}
                            aria-label={`Move ${c.label} down`}
                          >
                            ↓
                          </button>
                        </>
                      ) : (
                        i + 1
                      )}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap">
                      <span className="inline-flex items-center gap-1.5 text-brand-primary-text">
                        <ContactIcon type={c.type} />
                        <span className="text-gray-800">{TYPES[c.type].name}</span>
                      </span>
                    </td>
                    <td className="px-3 py-2">{c.label}</td>
                    <td className="px-3 py-2 font-mono text-xs break-all">{c.value}</td>
                    <td className="px-3 py-2 text-gray-600">{c.availability ?? "—"}</td>
                    <td className="px-3 py-2 text-gray-600">{audienceText(c.audience)}</td>
                    <td className="px-3 py-2">
                      {canEdit ? (
                        <label className="inline-flex items-center gap-1.5">
                          <input
                            type="checkbox"
                            checked={c.is_active}
                            disabled={setActive.isPending}
                            onChange={(e) => setActive.mutate({ id: c.id, active: e.target.checked })}
                          />
                          <span>{c.is_active ? "Active" : "Inactive"}</span>
                        </label>
                      ) : c.is_active ? (
                        "Active"
                      ) : (
                        "Inactive"
                      )}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-right">
                      {canEdit && (
                        <>
                          <button className="text-xs underline mr-3" onClick={() => startEdit(c)}>
                            Edit
                          </button>
                          <button
                            className="text-xs underline text-red-700"
                            onClick={() => {
                              if (window.confirm(`Delete “${c.label}”? Phones remove it at their next sync. This cannot be undone here.`))
                                remove.mutate(c.id);
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

          {canEdit && editing === null && (
            <button className="bg-gray-900 text-white rounded px-4 py-1.5 text-sm" onClick={() => startEdit(null)}>
              Add contact
            </button>
          )}
          {!canEdit && <p className="text-xs text-gray-500">You can view the support contacts. Only content admins can change them.</p>}

          {canEdit && editing !== null && (
            <form
              className="bg-white border rounded-lg p-4 space-y-3 text-sm max-w-2xl"
              onSubmit={(e) => {
                e.preventDefault();
                if (!problem) save.mutate();
              }}
            >
              <h2 className="font-medium">{editing === "new" ? "Add a support contact" : "Edit support contact"}</h2>
              <label className="block">
                <span className="text-xs text-gray-500">Type</span>
                <select
                  className="mt-1 w-full border rounded px-2 py-1"
                  value={draft.type}
                  onChange={(e) => setDraft({ ...draft, type: e.target.value as SupportContactType })}
                >
                  {(Object.keys(TYPES) as SupportContactType[]).map((t) => (
                    <option key={t} value={t}>
                      {TYPES[t].name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="text-xs text-gray-500">Label shown to learners</span>
                <input
                  required
                  maxLength={80}
                  placeholder="e.g. Call the support line"
                  className="mt-1 w-full border rounded px-2 py-1"
                  value={draft.label}
                  onChange={(e) => setDraft({ ...draft, label: e.target.value })}
                />
              </label>
              <label className="block">
                <span className="text-xs text-gray-500">{TYPES[draft.type].valueLabel}</span>
                <input
                  required
                  maxLength={500}
                  inputMode={isNumber ? "tel" : draft.type === "EMAIL" ? "email" : "url"}
                  placeholder={TYPES[draft.type].placeholder}
                  className={`mt-1 w-full border rounded px-2 py-1 font-mono ${problem ? "border-red-600" : ""}`}
                  value={draft.value}
                  onChange={(e) => setDraft({ ...draft, value: e.target.value })}
                  aria-invalid={!!problem}
                />
                <span className={`text-xs ${problem ? "text-red-600" : "text-gray-500"}`}>{problem ?? TYPES[draft.type].hint}</span>
              </label>
              {draft.type === "WHATSAPP" && (
                <label className="block">
                  <span className="text-xs text-gray-500">Pre-filled message (optional)</span>
                  <textarea
                    rows={2}
                    maxLength={500}
                    placeholder="e.g. Hello, I have a question about the e-Playbook."
                    className="mt-1 w-full border rounded px-2 py-1"
                    value={draft.whatsapp_message}
                    onChange={(e) => setDraft({ ...draft, whatsapp_message: e.target.value })}
                  />
                </label>
              )}
              {draft.type === "EMAIL" && (
                <label className="block">
                  <span className="text-xs text-gray-500">Subject (optional)</span>
                  <input
                    maxLength={150}
                    className="mt-1 w-full border rounded px-2 py-1"
                    value={draft.email_subject}
                    onChange={(e) => setDraft({ ...draft, email_subject: e.target.value })}
                  />
                </label>
              )}
              {(draft.type === "WHATSAPP" || draft.type === "EMAIL") && (
                <>
                  <label className="flex items-start gap-2">
                    <input
                      type="checkbox"
                      className="mt-0.5"
                      checked={draft.include_app_version}
                      onChange={(e) => setDraft({ ...draft, include_app_version: e.target.checked })}
                    />
                    <span>Add the app version to the {draft.type === "EMAIL" ? "email" : "message"} (helps support staff; nothing else about the learner is added)</span>
                  </label>
                  <p className="text-xs text-gray-600">Never ask for names, learner IDs or locations in pre-filled text.</p>
                </>
              )}
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="block">
                  <span className="text-xs text-gray-500">Availability (optional)</span>
                  <input
                    maxLength={120}
                    placeholder="e.g. Mon-Fri 8am-5pm"
                    className="mt-1 w-full border rounded px-2 py-1"
                    value={draft.availability}
                    onChange={(e) => setDraft({ ...draft, availability: e.target.value })}
                  />
                </label>
                <label className="block">
                  <span className="text-xs text-gray-500">Languages offered (optional)</span>
                  <input
                    maxLength={120}
                    placeholder="e.g. English, Hausa"
                    className="mt-1 w-full border rounded px-2 py-1"
                    value={draft.languages}
                    onChange={(e) => setDraft({ ...draft, languages: e.target.value })}
                  />
                </label>
              </div>
              <fieldset>
                <legend className="text-xs text-gray-500">Audience (none ticked = all learners)</legend>
                <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1">
                  {LEARNER_ROLES.map((r) => (
                    <label key={r.value} className="inline-flex items-center gap-1.5">
                      <input
                        type="checkbox"
                        checked={draft.audience.includes(r.value)}
                        onChange={(e) =>
                          setDraft({
                            ...draft,
                            audience: e.target.checked ? [...draft.audience, r.value] : draft.audience.filter((a) => a !== r.value),
                          })
                        }
                      />
                      {r.label}
                    </label>
                  ))}
                </div>
              </fieldset>
              <label className="inline-flex items-center gap-2">
                <input type="checkbox" checked={draft.is_active} onChange={(e) => setDraft({ ...draft, is_active: e.target.checked })} />
                Active (shown on phones)
              </label>
              <div className="space-x-3 pt-1">
                <button disabled={save.isPending || !!problem} className="bg-gray-900 text-white rounded px-4 py-1.5 disabled:opacity-50">
                  {save.isPending ? "Saving…" : "Save contact"}
                </button>
                <button type="button" className="text-xs underline" onClick={() => setEditing(null)}>
                  Cancel
                </button>
              </div>
            </form>
          )}

          <div className="bg-white border rounded-lg p-4 text-sm max-w-2xl space-y-2">
            <h2 className="font-medium">Note under the deck (optional)</h2>
            <p className="text-xs text-gray-600">
              One short line shown at the bottom of the deck, for example to say where to go in a medical emergency. Leave it
              empty to show no note. It is shown exactly as written, in every language.
            </p>
            <textarea
              rows={2}
              maxLength={settings.data?.note_max ?? 200}
              disabled={!canEdit}
              className="w-full border rounded px-2 py-1 disabled:bg-gray-50"
              value={note}
              onChange={(e) => setNoteDraft(e.target.value)}
            />
            {canEdit && (
              <button
                disabled={saveNote.isPending || noteDraft === null}
                className="bg-gray-900 text-white rounded px-4 py-1.5 disabled:opacity-50"
                onClick={() => saveNote.mutate(note)}
              >
                {saveNote.isPending ? "Saving…" : "Save note"}
              </button>
            )}
          </div>
        </div>

        <aside>
          <h2 className="text-xs font-medium text-gray-500 mb-2">Phone preview{editing ? " (with your unsaved changes)" : ""}</h2>
          <DeckPreview contacts={preview} note={note.trim()} />
          <p className="text-xs text-gray-500 mt-2">Shows every active contact. Each learner sees only the contacts for their role.</p>
        </aside>
      </div>
    </div>
  );
}

/** How the deck looks on the phone (mobile/lib/widgets/support_deck.dart), in the app's colours. */
function DeckPreview({ contacts, note }: { contacts: Draft[]; note: string }) {
  return (
    <div className="mx-auto w-[300px] rounded-[28px] border-[6px] border-brand-text bg-brand-background p-3">
      {contacts.length === 0 ? (
        <p className="text-xs text-gray-600 text-center py-8">No active contact: the deck is hidden on phones.</p>
      ) : (
        <div className="rounded-brand-standard border border-brand-divider bg-brand-surface p-3">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-brand-primary-text">
              <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.8} aria-hidden="true">
                <path d="M4 14v-2a8 8 0 0 1 16 0v2M4 14h3v5H5a1 1 0 0 1-1-1zM20 14h-3v5h2a1 1 0 0 0 1-1z" />
              </svg>
            </span>
            <span className="text-[13px] font-bold text-brand-text">Need help from a person?</span>
          </div>
          <div className="space-y-1.5">
            {contacts.map((c, i) => (
              <div key={i} className="flex items-center gap-2 rounded-lg bg-brand-surface-selected px-2 py-2 min-h-[44px]">
                <span className="text-brand-primary-text shrink-0">
                  <ContactIcon type={c.type} className="w-5 h-5" />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="text-[12px] font-semibold text-brand-text leading-tight">{c.label}</div>
                  <div className="text-[11px] text-brand-text-muted break-all leading-tight">{c.value.trim()}</div>
                  {c.availability.trim() && <div className="text-[10.5px] text-brand-text-muted leading-tight">{c.availability.trim()}</div>}
                </div>
                <svg viewBox="0 0 24 24" className="w-4 h-4 text-brand-text-muted shrink-0" fill="none" stroke="currentColor" strokeWidth={1.8} aria-hidden="true">
                  <rect x="9" y="9" width="11" height="11" rx="2" />
                  <path d="M5 15V5a1 1 0 0 1 1-1h9" />
                </svg>
              </div>
            ))}
          </div>
          {note && <p className="text-[11px] text-brand-text-muted mt-2 leading-snug">{note}</p>}
        </div>
      )}
    </div>
  );
}
