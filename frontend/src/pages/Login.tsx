import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../auth/AuthContext";
import Brand from "../components/Brand";

export default function Login() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(username, password);
      navigate("/");
    } catch {
      setError("Invalid credentials");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-800 via-slate-900 to-slate-950 p-4">
      <form onSubmit={submit} className="card w-full max-w-sm p-8">
        <div className="mb-6 mx-auto w-40">
          <Brand layout="vertical" variant="dark" />
        </div>
        {error && <div className="mb-4 rounded-lg bg-red-50 text-red-700 text-sm px-3 py-2">{error}</div>}
        <label className="label">{t("username")}</label>
        <input className="input mb-4" value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
        <label className="label">{t("password")}</label>
        <input
          type="password"
          className="input mb-6"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button className="btn-primary w-full" disabled={busy}>
          {busy ? "…" : t("login")}
        </button>
      </form>
    </div>
  );
}
