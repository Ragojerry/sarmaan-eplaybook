import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "../services/api";
import { Module, ModuleTranslation } from "../types/api";

/** Edit the English title, description and read-aloud text of a module. The
 * module row (used in lists) and its English translation are kept in step. */
export default function ModuleDetailsEditor({
  module,
  translation,
  onSaved,
}: {
  module: Module;
  translation: ModuleTranslation | undefined;
  onSaved: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState(module.title);
  const [description, setDescription] = useState(module.description ?? "");
  const [audio, setAudio] = useState(translation?.audio_text ?? "");
  const [error, setError] = useState<string | null>(null);

  const save = useMutation({
    mutationFn: async () => {
      await api.patch(`/modules/${module.id}`, { title: title.trim(), description: description.trim() || null });
      if (translation) {
        await api.patch(`/modules/translations/${translation.id}`, {
          title: title.trim(),
          description: description.trim() || null,
          audio_text: audio.trim() || null,
        });
      }
    },
    onSuccess: () => {
      setOpen(false);
      setError(null);
      onSaved();
    },
    onError: (e: any) => setError(e?.response?.data?.detail ?? "Could not save."),
  });

  if (!open) {
    return (
      <button
        onClick={() => {
          setTitle(module.title);
          setDescription(module.description ?? "");
          setAudio(translation?.audio_text ?? "");
          setOpen(true);
        }}
        className="text-sm text-blue-600 hover:underline mb-4 block"
      >
        Edit title, description and audio text (English)
      </button>
    );
  }

  const field = "w-full border rounded px-3 py-2 text-sm";
  return (
    <div className="bg-white border rounded-lg p-4 mb-6 space-y-3 max-w-2xl">
      <h2 className="text-sm font-medium">Edit module (English)</h2>
      <div>
        <label className="block text-xs text-gray-500 mb-1">Title</label>
        <input className={field} value={title} onChange={(e) => setTitle(e.target.value)} />
      </div>
      <div>
        <label className="block text-xs text-gray-500 mb-1">Description</label>
        <textarea className={field} rows={3} value={description} onChange={(e) => setDescription(e.target.value)} />
      </div>
      {translation ? (
        <div>
          <label className="block text-xs text-gray-500 mb-1">Audio text (read aloud on the phone)</label>
          <textarea className={field} rows={5} value={audio} onChange={(e) => setAudio(e.target.value)} />
        </div>
      ) : (
        <p className="text-xs text-gray-500">Start the English content below to edit the audio text.</p>
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex gap-2">
        <button
          onClick={() => save.mutate()}
          disabled={save.isPending || !title.trim()}
          className="bg-gray-900 text-white text-sm rounded px-4 py-2 disabled:opacity-50"
        >
          {save.isPending ? "Saving…" : "Save"}
        </button>
        <button onClick={() => setOpen(false)} className="text-sm text-gray-500 px-3 py-2">
          Cancel
        </button>
      </div>
    </div>
  );
}
