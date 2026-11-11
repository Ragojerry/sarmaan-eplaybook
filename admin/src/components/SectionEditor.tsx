import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "../services/api";
import { ContentSection } from "../types/api";
import SectionMediaField from "./SectionMediaField";

const str = (v: unknown) => (typeof v === "string" ? v : "");

/** The fields of an inline True/False quiz statement (content type TRUE_FALSE). Learners
 * answer it in the reader; with three statements all must be right to pass (90% rule). */
export function TrueFalseFields({
  statement,
  answer,
  explanation,
  audience,
  onChange,
}: {
  statement: string;
  answer: boolean;
  explanation: string;
  audience: string;
  onChange: (v: Partial<{ statement: string; answer: boolean; explanation: string; audience: string }>) => void;
}) {
  const field = "w-full border rounded px-2 py-1 text-sm";
  return (
    <div className="space-y-2">
      <textarea className={field} rows={2} placeholder="Statement" value={statement}
        onChange={(e) => onChange({ statement: e.target.value })} />
      <div className="flex flex-wrap gap-3 items-center text-sm">
        <label className="flex items-center gap-1">
          Correct answer
          <select className="border rounded px-2 py-1" value={answer ? "true" : "false"}
            onChange={(e) => onChange({ answer: e.target.value === "true" })}>
            <option value="true">True</option>
            <option value="false">False</option>
          </select>
        </label>
        <label className="flex items-center gap-1">
          Audience
          <select className="border rounded px-2 py-1" value={audience} onChange={(e) => onChange({ audience: e.target.value })}>
            <option value="HFW">HFW &amp; others</option>
            <option value="CDD">CDD</option>
          </select>
        </label>
      </div>
      <input className={field} placeholder="Short explanation shown after answering (optional)" value={explanation}
        onChange={(e) => onChange({ explanation: e.target.value })} />
      <p className="text-xs text-gray-500">
        Who sees it is decided by the module&apos;s audience; the audience tag here labels it for reports. Place it right
        after the section that teaches the point (Move up / Move down).
      </p>
    </div>
  );
}

/** Inline editor for the English text of one section. Structure (type, order,
 * pictures) is not changed here; only wording, and the file of an AUDIO/VIDEO section. */
export default function SectionEditor({
  section,
  onDone,
}: {
  section: ContentSection;
  onDone: (saved: boolean) => void;
}) {
  // Kept up to date when an audio/video file is uploaded or removed, so Save never puts back the old file.
  const [c, setC] = useState(section.content as Record<string, any>);
  const type = section.content_type;
  const [title, setTitle] = useState(section.title ?? "");
  const [text, setText] = useState(str(c.text));
  const [heading, setHeading] = useState(str(c.heading));
  const [caption, setCaption] = useState(str(c.caption));
  const [alt, setAlt] = useState(str(c.alt));
  const [itemsText, setItemsText] = useState(Array.isArray(c.items) ? c.items.map(String).join("\n") : "");
  const [headers, setHeaders] = useState<string[]>(Array.isArray(c.headers) ? c.headers.map(String) : []);
  const [rows, setRows] = useState<string[][]>(
    Array.isArray(c.rows) ? c.rows.map((r: unknown[]) => r.map(String)) : [],
  );
  const [statement, setStatement] = useState(str(c.statement));
  const [answer, setAnswer] = useState<boolean>(c.answer === true);
  const [explanation, setExplanation] = useState(str(c.explanation));
  const [audience, setAudience] = useState(str(c.audience) || "HFW");
  const [error, setError] = useState<string | null>(null);
  const [fileChanged, setFileChanged] = useState(false);

  const save = useMutation({
    mutationFn: async () => {
      const content: Record<string, unknown> = { ...c };
      if (type === "TEXT" || type === "HEADING") content.text = text;
      if (type === "CALLOUT" || type === "WARNING" || type === "JOB_AID") {
        content.heading = heading;
        content.text = text;
      }
      if (type === "LIST") content.items = itemsText.split("\n").map((s) => s.trim()).filter(Boolean);
      if (type === "TABLE") {
        content.headers = headers;
        content.rows = rows;
      }
      if (type === "IMAGE") {
        content.caption = caption;
        content.alt = alt;
      }
      if (type === "TRUE_FALSE") {
        content.statement = statement;
        content.answer = answer;
        content.explanation = explanation.trim() || null;
        content.audience = audience;
      }
      return (await api.patch(`/modules/sections/${section.id}`, { title: title.trim() || null, content })).data;
    },
    onSuccess: () => onDone(true),
    onError: (e: any) => setError(e?.response?.data?.detail ?? "Could not save the section."),
  });

  const field = "w-full border rounded px-2 py-1 text-sm";
  const hasText = ["TEXT", "HEADING", "CALLOUT", "WARNING", "JOB_AID"].includes(type);

  return (
    <div className="border rounded p-3 bg-gray-50 space-y-2 flex-1">
      <span className="text-xs uppercase text-gray-400">{type}</span>
      <input className={field} placeholder="Section title (optional)" value={title} onChange={(e) => setTitle(e.target.value)} />
      {["CALLOUT", "WARNING", "JOB_AID"].includes(type) && (
        <input className={field} placeholder="Heading" value={heading} onChange={(e) => setHeading(e.target.value)} />
      )}
      {hasText && (
        <textarea className={field} rows={6} placeholder="Text" value={text} onChange={(e) => setText(e.target.value)} />
      )}
      {type === "LIST" && (
        <>
          <textarea className={field} rows={7} value={itemsText} onChange={(e) => setItemsText(e.target.value)} />
          <p className="text-xs text-gray-500">One list item per line.</p>
        </>
      )}
      {type === "TRUE_FALSE" && (
        <TrueFalseFields
          statement={statement}
          answer={answer}
          explanation={explanation}
          audience={audience}
          onChange={(v) => {
            if (v.statement !== undefined) setStatement(v.statement);
            if (v.answer !== undefined) setAnswer(v.answer);
            if (v.explanation !== undefined) setExplanation(v.explanation);
            if (v.audience !== undefined) setAudience(v.audience);
          }}
        />
      )}
      {type === "IMAGE" && (
        <>
          <input className={field} placeholder="Caption" value={caption} onChange={(e) => setCaption(e.target.value)} />
          <input className={field} placeholder="Alt text (for screen readers)" value={alt} onChange={(e) => setAlt(e.target.value)} />
        </>
      )}
      {type === "TABLE" && (
        <div className="overflow-x-auto">
          <table className="text-sm">
            <thead>
              <tr>
                {headers.map((h, i) => (
                  <th key={i} className="p-1">
                    <input
                      className="border rounded px-2 py-1 font-medium w-36"
                      value={h}
                      onChange={(e) => setHeaders(headers.map((x, j) => (j === i ? e.target.value : x)))}
                    />
                  </th>
                ))}
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map((row, r) => (
                <tr key={r}>
                  {row.map((cell, k) => (
                    <td key={k} className="p-1">
                      <input
                        className="border rounded px-2 py-1 w-36"
                        value={cell}
                        onChange={(e) =>
                          setRows(rows.map((rw, i) => (i === r ? rw.map((x, j) => (j === k ? e.target.value : x)) : rw)))
                        }
                      />
                    </td>
                  ))}
                  <td>
                    <button
                      type="button"
                      className="text-xs text-red-500"
                      onClick={() => setRows(rows.filter((_, i) => i !== r))}
                    >
                      remove row
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <button
            type="button"
            className="text-xs text-blue-600 mt-1"
            onClick={() => setRows([...rows, headers.map(() => "")])}
          >
            + add row
          </button>
        </div>
      )}
      {(type === "VIDEO" || type === "AUDIO") && (
        <SectionMediaField sectionId={section.id} kind={type} content={c} onChanged={(next) => {
            setC(next);
            setFileChanged(true);
          }} />
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => save.mutate()}
          disabled={save.isPending}
          className="bg-gray-900 text-white text-sm rounded px-3 py-1.5 disabled:opacity-50"
        >
          {save.isPending ? "Saving…" : "Save changes"}
        </button>
        <button type="button" onClick={() => onDone(fileChanged)} className="text-sm text-gray-500 px-3 py-1.5">
          Cancel
        </button>
      </div>
    </div>
  );
}
