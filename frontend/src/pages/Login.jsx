import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldAlert } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../components/Toast";

export default function Login() {
  const { login } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const [email, setEmail] = useState("sofia.alvarez@cybersentinel.demo");
  const [password, setPassword] = useState("DemoAnalyst!123");
  const [busy, setBusy] = useState(false);

  async function onSubmit(event) {
    event.preventDefault();
    setBusy(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      toast.push(err.message, "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <form onSubmit={onSubmit} className="w-full max-w-md rounded-2xl border border-soc-border bg-soc-panel p-8">
        <div className="mb-6 flex items-center gap-3">
          <ShieldAlert className="text-soc-accent" />
          <div>
            <h1 className="text-xl font-bold tracking-[0.18em]">CYBERSENTINEL</h1>
            <p className="text-xs text-slate-400">Analyst access · defensive SOC console</p>
          </div>
        </div>
        <label className="mb-3 block text-sm text-slate-300">
          Email
          <input
            className="mt-1 w-full rounded-md border border-soc-border bg-[#070b12] px-3 py-2"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            required
          />
        </label>
        <label className="mb-5 block text-sm text-slate-300">
          Password
          <input
            className="mt-1 w-full rounded-md border border-soc-border bg-[#070b12] px-3 py-2"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            required
          />
        </label>
        <button disabled={busy} className="w-full rounded-md bg-soc-accent py-2 font-semibold text-slate-950">
          {busy ? "Signing in…" : "Sign in"}
        </button>
        <p className="mt-4 text-xs leading-5 text-slate-500">
          Demo mode uses the seeded analyst account when <span className="font-mono">DEMO_MODE=true</span>. Production uses
          Supabase Auth. Privileged database keys never ship in this frontend.
        </p>
      </form>
    </div>
  );
}
