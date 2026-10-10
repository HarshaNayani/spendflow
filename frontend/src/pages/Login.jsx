import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { errorMessage } from "../api";
import { useAuth } from "../context/AuthContext";
import { DEMO_ACCOUNTS } from "../constants";
import { homePath } from "../utils";

export default function Login() {
  const { user, login, register } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={homePath(user.role)} replace />;

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const loggedIn =
        mode === "login"
          ? await login(form.email, form.password)
          : await register(form.name, form.email, form.password);
      navigate(homePath(loggedIn.role), { replace: true });
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-indigo-50 via-slate-50 to-sky-50 px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <span className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-500 text-2xl font-bold text-white">
            S
          </span>
          <h1 className="text-2xl font-bold text-slate-900">SpendFlow</h1>
          <p className="mt-1 text-sm text-slate-600">
            Expense approvals with clear roles, an audit trail and AI checks
          </p>
        </div>

        <div className="card">
          <div className="mb-5 grid grid-cols-2 rounded-lg bg-slate-100 p-1 text-sm font-semibold">
            {["login", "register"].map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => {
                  setMode(m);
                  setError("");
                }}
                className={`rounded-md py-1.5 capitalize transition ${
                  mode === m ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"
                }`}
              >
                {m === "login" ? "Log in" : "Sign up"}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === "register" && (
              <div>
                <label className="label" htmlFor="name">
                  Full name
                </label>
                <input id="name" required minLength={2} className="input" value={form.name} onChange={set("name")} />
              </div>
            )}
            <div>
              <label className="label" htmlFor="email">
                Email
              </label>
              <input id="email" type="email" required className="input" value={form.email} onChange={set("email")} />
            </div>
            <div>
              <label className="label" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                minLength={6}
                className="input"
                value={form.password}
                onChange={set("password")}
              />
            </div>

            {error && (
              <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800">
                {error}
              </p>
            )}

            <button type="submit" disabled={busy} className="btn btn-primary w-full">
              {busy ? "Please wait..." : mode === "login" ? "Log in" : "Create employee account"}
            </button>
          </form>
        </div>

        <div className="mt-5 rounded-xl border border-slate-200 bg-white/70 p-4">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Demo accounts (click to fill)
          </p>
          <div className="grid grid-cols-3 gap-2">
            {DEMO_ACCOUNTS.map((a) => (
              <button
                key={a.role}
                type="button"
                onClick={() => {
                  setMode("login");
                  setError("");
                  setForm({ name: "", email: a.email, password: a.password });
                }}
                className="btn btn-ghost !px-2"
              >
                {a.role}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
