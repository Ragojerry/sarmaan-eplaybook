import BrandMark from "../components/BrandMark";
import { useState, FormEvent } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../services/auth";
import PartnerLogos from "../components/PartnerLogos";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const from = (location.state as { from?: string })?.from ?? "/";

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username, password);
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Login failed. Check your credentials.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <div className="flex-1 flex items-center justify-center">
      <form onSubmit={handleSubmit} className="w-full max-w-sm bg-white p-8 rounded-lg shadow">
        <BrandMark heading className="text-xl mb-6" subtitle="Admin Portal" />

        {error && (
          <div className="mb-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2">
            {error}
          </div>
        )}

        <label className="block text-sm font-medium mb-1" htmlFor="username">
          Username
        </label>
        <input
          id="username"
          className="w-full border rounded px-3 py-2 mb-4"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="username"
          required
        />

        <label className="block text-sm font-medium mb-1" htmlFor="password">
          Password
        </label>
        <input
          id="password"
          type="password"
          className="w-full border rounded px-3 py-2 mb-6"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          required
        />

        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-gray-900 text-white rounded py-2 font-medium disabled:opacity-50"
        >
          {submitting ? "Signing in…" : "Sign in"}
        </button>
      </form>
      </div>
      <footer className="border-t border-gray-200">
        <PartnerLogos placement="adminFooter" />
      </footer>
    </div>
  );
}
