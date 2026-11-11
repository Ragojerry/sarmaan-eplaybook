import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import { useAuth } from "../services/auth";

interface GeneralQuestion {
  id: string;
  number: number;
  prompt: string;
  options: string[];
  correct_index: number | null;
  correct_letter: string | null;
  cdd_specific: boolean;
  is_active: boolean;
}

interface TrainingSettings {
  module_min_seconds: number;
  general_test_active: boolean;
  cannot_activate_because: string | null;
}

const LETTERS = "ABCDEFGHIJ";
const detail = (e: any, fallback: string) => e?.response?.data?.detail ?? fallback;

/** The General pre/post test (one test for every learner: taken before any module and
 * again after all of them) and the training rules: minimum time per module and the
 * switch that turns the General test on once every active question has its answer. */
export default function GeneralTestPage() {
  const { user } = useAuth();
  const canEdit = user?.role === "CONTENT_ADMIN" || user?.role === "SUPER_ADMIN";
  const queryClient = useQueryClient();
  const [keyText, setKeyText] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<GeneralQuestion | null>(null);
  const [minutes, setMinutes] = useState<string | null>(null);

  const { data: questions } = useQuery<GeneralQuestion[]>({
    queryKey: ["general-test-questions"],
    queryFn: async () => (await api.get("/general-test/questions")).data,
  });
  const { data: settings } = useQuery<TrainingSettings>({
    queryKey: ["general-test-settings"],
    queryFn: async () => (await api.get("/general-test/settings")).data,
  });
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["general-test-questions"] });
    queryClient.invalidateQueries({ queryKey: ["general-test-settings"] });
  };
  const done = (text: string) => {
    setMessage(text);
    setError(null);
    refresh();
  };

  const saveKey = useMutation({
    mutationFn: async () => (await api.post("/general-test/answer-key", { key: keyText })).data,
    onSuccess: () => {
      setKeyText("");
      done("Answers saved. Activate the questions that have one, then switch the test on when you are ready.");
    },
    onError: (e) => setError(detail(e, "Could not read the answer key.")),
  });
  const saveQuestion = useMutation({
    mutationFn: async (q: GeneralQuestion) =>
      (
        await api.patch(`/general-test/questions/${q.id}`, {
          prompt: q.prompt,
          options: q.options,
          cdd_specific: q.cdd_specific,
          is_active: q.is_active,
          ...(q.correct_index === null ? { clear_answer: true } : { correct_index: q.correct_index }),
        })
      ).data,
    onSuccess: () => {
      setEditing(null);
      done("Question saved.");
    },
    onError: (e) => setError(detail(e, "Could not save the question.")),
  });
  const saveSettings = useMutation({
    mutationFn: async (body: Partial<TrainingSettings>) => (await api.put("/general-test/settings", body)).data,
    onSuccess: () => {
      setMinutes(null);
      done("Settings saved. Phones pick them up at their next sync.");
    },
    onError: (e) => setError(detail(e, "Could not save the settings.")),
  });
  const activateAllAnswered = useMutation({
    mutationFn: async () => {
      for (const q of questions ?? []) {
        if (q.correct_index !== null && !q.is_active) await api.patch(`/general-test/questions/${q.id}`, { is_active: true });
      }
    },
    onSuccess: () => done("Every question with an answer is active."),
    onError: (e) => setError(detail(e, "Could not activate the questions.")),
  });

  const answered = (questions ?? []).filter((q) => q.correct_index !== null).length;

  return (
    <div className="p-6 max-w-5xl">
      <h1 className="text-xl font-semibold mb-1">General test and training rules</h1>
      <p className="text-sm text-gray-600 mb-4">
        Every learner (CDD, HFW and others) takes the same General test: the <strong>pre-test</strong> once before any
        module opens, and the <strong>post-test</strong> (the same questions) once after completing all their modules. Scores
        are points out of the number of questions and a percentage; there is no pass mark. Questions marked
        &ldquo;CDD&rdquo; mention CDDs but are shown to everyone.
      </p>

      {message && <p className="text-sm text-green-700 mb-3">{message}</p>}
      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

      <section className="bg-white border rounded-lg p-4 mb-6 space-y-3">
        <h2 className="text-sm font-medium">Training rules</h2>
        {settings && (
          <>
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <span>Minimum active time per module:</span>
              <input
                type="number"
                min={0}
                max={60}
                step={0.5}
                className="border rounded px-2 py-1 w-24"
                disabled={!canEdit}
                value={minutes ?? String(settings.module_min_seconds / 60)}
                onChange={(e) => setMinutes(e.target.value)}
              />
              <span>minutes ({settings.module_min_seconds} seconds)</span>
              {canEdit && minutes !== null && (
                <button
                  className="bg-gray-900 text-white rounded px-3 py-1"
                  onClick={() => saveSettings.mutate({ module_min_seconds: Math.round(Number(minutes) * 60) })}
                >
                  Save
                </button>
              )}
            </div>
            <p className="text-xs text-gray-500">
              Counted on the phone only while the module is open and the app is in front (reported by the phone, like quiz
              results). A module can be completed when its quiz is passed and this time is reached.
            </p>
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <span>
                General test is{" "}
                <strong className={settings.general_test_active ? "text-green-700" : "text-gray-700"}>
                  {settings.general_test_active ? "ON" : "OFF"}
                </strong>
              </span>
              {canEdit && (
                <button
                  className="border rounded px-3 py-1 disabled:opacity-40"
                  disabled={!settings.general_test_active && !!settings.cannot_activate_because}
                  onClick={() => {
                    const on = !settings.general_test_active;
                    if (on && !window.confirm("Switch the General test on? From then on, every learner must take the pre-test before any module opens.")) return;
                    saveSettings.mutate({ general_test_active: on });
                  }}
                >
                  {settings.general_test_active ? "Switch off" : "Switch on"}
                </button>
              )}
            </div>
            {!settings.general_test_active && settings.cannot_activate_because && (
              <p className="text-xs text-amber-700">Cannot be switched on yet: {settings.cannot_activate_because}.</p>
            )}
          </>
        )}
      </section>

      {canEdit && (
        <section className="bg-white border rounded-lg p-4 mb-6 space-y-2">
          <h2 className="text-sm font-medium">Answer key</h2>
          <p className="text-xs text-gray-500">
            Paste the key as question-letter pairs, for example <code>1-B, 2-B, 3-C</code>. Letters follow the printed order of
            the options (A is the first). {answered} of {questions?.length ?? 0} questions have an answer.
          </p>
          <textarea className="w-full border rounded px-2 py-1 text-sm" rows={2} value={keyText} onChange={(e) => setKeyText(e.target.value)} />
          <div className="flex gap-2">
            <button
              className="bg-gray-900 text-white text-sm rounded px-3 py-1.5 disabled:opacity-50"
              disabled={!keyText.trim() || saveKey.isPending}
              onClick={() => saveKey.mutate()}
            >
              Save answers
            </button>
            <button
              className="border text-sm rounded px-3 py-1.5 disabled:opacity-50"
              disabled={answered === 0 || activateAllAnswered.isPending}
              onClick={() => activateAllAnswered.mutate()}
            >
              Activate every question that has an answer
            </button>
          </div>
        </section>
      )}

      <section className="bg-white border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-gray-500">
            <tr>
              <th className="px-3 py-2">No.</th>
              <th className="px-3 py-2">Question and options</th>
              <th className="px-3 py-2">Answer</th>
              <th className="px-3 py-2">Active</th>
              <th className="px-3 py-2">Audience note</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {(questions ?? []).map((q) =>
              editing?.id === q.id ? (
                <tr key={q.id} className="border-t bg-gray-50">
                  <td className="px-3 py-2 align-top">{q.number}</td>
                  <td className="px-3 py-2 space-y-1" colSpan={4}>
                    <textarea className="w-full border rounded px-2 py-1" rows={2} value={editing.prompt}
                      onChange={(e) => setEditing({ ...editing, prompt: e.target.value })} />
                    {editing.options.map((o, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <input type="radio" checked={editing.correct_index === i}
                          onChange={() => setEditing({ ...editing, correct_index: i })} title="Correct answer" />
                        <span className="w-4">{LETTERS[i]}</span>
                        <input className="flex-1 border rounded px-2 py-1" value={o}
                          onChange={(e) => setEditing({ ...editing, options: editing.options.map((x, j) => (j === i ? e.target.value : x)) })} />
                      </div>
                    ))}
                    <div className="flex gap-4 text-xs">
                      <label><input type="checkbox" checked={editing.is_active}
                        onChange={(e) => setEditing({ ...editing, is_active: e.target.checked })} /> Active</label>
                      <label><input type="checkbox" checked={editing.cdd_specific}
                        onChange={(e) => setEditing({ ...editing, cdd_specific: e.target.checked })} /> Mentions CDDs</label>
                      <button type="button" className="text-gray-500 underline" onClick={() => setEditing({ ...editing, correct_index: null })}>
                        Clear answer
                      </button>
                    </div>
                  </td>
                  <td className="px-3 py-2 align-top whitespace-nowrap">
                    <button className="text-blue-600 text-xs mr-2" onClick={() => saveQuestion.mutate(editing)}>Save</button>
                    <button className="text-gray-500 text-xs" onClick={() => setEditing(null)}>Cancel</button>
                  </td>
                </tr>
              ) : (
                <tr key={q.id} className="border-t align-top">
                  <td className="px-3 py-2">{q.number}</td>
                  <td className="px-3 py-2">
                    <p className="font-medium">{q.prompt}</p>
                    <ol className="text-xs text-gray-600 mt-1">
                      {q.options.map((o, i) => (
                        <li key={i} className={q.correct_index === i ? "font-semibold text-green-700" : ""}>
                          {LETTERS[i]}. {o}
                        </li>
                      ))}
                    </ol>
                  </td>
                  <td className="px-3 py-2">{q.correct_letter ?? <span className="text-amber-700">missing</span>}</td>
                  <td className="px-3 py-2">{q.is_active ? "Yes" : "No"}</td>
                  <td className="px-3 py-2 text-xs">{q.cdd_specific ? "Mentions CDDs (shown to everyone)" : "Everyone"}</td>
                  <td className="px-3 py-2">
                    {canEdit && (
                      <button className="text-blue-600 text-xs" onClick={() => setEditing({ ...q })}>Edit</button>
                    )}
                  </td>
                </tr>
              ),
            )}
            {questions && questions.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-4 text-gray-500">
                  No questions yet. Load them with <code>python -m scripts.load_learning_tests</code>.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}
