import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  Activity,
  Bell,
  FileText,
  LayoutDashboard,
  LogOut,
  Radar,
  Server,
  Settings,
  ShieldAlert,
  Siren,
} from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { DemoAPI } from "../services/api";
import { useToast } from "../components/Toast";
import { useState } from "react";

const links = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/incidents", label: "Incidents", icon: Siren },
  { to: "/logs", label: "Logs", icon: Activity },
  { to: "/assets", label: "Assets", icon: Server },
  { to: "/threat-intel", label: "Threat Intel", icon: Radar },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);

  async function loadDemo() {
    setBusy(true);
    try {
      const result = await DemoAPI.load();
      toast.push("Demo attack correlated into CS-1042", "success");
      const id = result?.incident?.id;
      navigate(id ? `/incidents/${id}` : "/incidents");
    } catch (err) {
      toast.push(err.message, "error");
    } finally {
      setBusy(false);
    }
  }

  async function resetDemo() {
    setBusy(true);
    try {
      await DemoAPI.reset();
      toast.push("Demo data cleared", "success");
      navigate("/");
    } catch (err) {
      toast.push(err.message, "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[240px_1fr]">
      <aside className="border-b border-soc-border bg-[#080f1c] lg:border-b-0 lg:border-r">
        <div className="flex items-center gap-2 px-5 py-5">
          <ShieldAlert className="text-soc-accent" size={22} />
          <div>
            <div className="text-sm font-bold tracking-[0.2em] text-white">CYBERSENTINEL</div>
            <div className="font-mono text-[10px] text-slate-500">SOC INCIDENT AGENT</div>
          </div>
        </div>
        <nav className="flex gap-1 overflow-x-auto px-3 pb-3 lg:flex-col">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-md px-3 py-2 text-sm ${
                  isActive ? "bg-cyan-500/10 text-soc-accent" : "text-slate-400 hover:bg-white/5 hover:text-white"
                }`
              }
            >
              <link.icon size={16} />
              {link.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="min-w-0">
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-soc-border bg-[#0a1220]/90 px-5 py-3">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Bell size={14} />
            Live polling enabled · responses are simulated
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              disabled={busy}
              onClick={loadDemo}
              className="rounded-md bg-soc-accent px-3 py-1.5 text-xs font-semibold text-slate-950 disabled:opacity-60"
            >
              {busy ? "Working…" : "Load Demo Attack"}
            </button>
            <button
              disabled={busy}
              onClick={resetDemo}
              className="rounded-md border border-soc-border px-3 py-1.5 text-xs text-slate-300"
            >
              Reset Demo
            </button>
            <div className="text-right">
              <div className="text-sm text-white">{user?.full_name}</div>
              <div className="font-mono text-[10px] uppercase text-slate-500">{user?.role}</div>
            </div>
            <button onClick={logout} className="rounded-md border border-soc-border p-2 text-slate-400" title="Sign out">
              <LogOut size={16} />
            </button>
          </div>
        </header>
        <main className="p-5">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
