import { useState } from "react";
import { api } from "../services/api";

type Found = { number: string; name: string | null; username: string | null; completed_at: string; correct: number; total: number; percent: number };

/**
 * Checks a training certificate number (e.g. SII-2026-06E1A47048). Learners earn the
 * certificate with 90% or more on the General post-test; the phone makes it offline,
 * so a new certificate is found once the learner's phone has synced.
 */
export default function CertificateCheck() {
  const [number, setNumber] = useState("");
  const [found, setFound] = useState<Found | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const check = async () => {
    setBusy(true);
    setFound(null);
    setError(null);
    try {
      setFound((await api.get(`/general-test/certificates/${encodeURIComponent(number.trim())}`)).data);
    } catch (e) {
      const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Could not check this number.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="bg-white border rounded-lg p-4 mb-6">
      <h2 className="text-sm font-medium mb-1">Check a certificate</h2>
      <p className="text-xs text-gray-500 mb-3">Enter the number printed on a learner&rsquo;s training certificate.</p>
      <form
        className="flex flex-wrap gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          if (number.trim()) check();
        }}
      >
        <input
          className="border rounded px-3 py-1.5 text-sm font-mono w-64"
          placeholder="SII-2026-XXXXXXXXXX"
          value={number}
          onChange={(e) => setNumber(e.target.value)}
        />
        <button type="submit" disabled={busy || !number.trim()} className="bg-gray-900 text-white text-sm rounded px-3 py-1.5 disabled:opacity-50">
          {busy ? "Checking…" : "Check"}
        </button>
      </form>
      {found && (
        <p className="text-sm text-green-700 mt-3">
          Genuine: {found.name} ({found.username}) passed the post-test with {found.correct} of {found.total} ({found.percent}%) on{" "}
          {new Date(found.completed_at).toLocaleDateString()}.
        </p>
      )}
      {error && <p className="text-sm text-red-600 mt-3">{error}</p>}
    </div>
  );
}
