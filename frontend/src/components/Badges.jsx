const severityClass = {
  low: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  medium: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  high: "bg-orange-500/15 text-orange-300 border-orange-500/30",
  critical: "bg-rose-500/15 text-rose-300 border-rose-500/30",
};

const statusClass = {
  new: "bg-slate-500/20 text-slate-200",
  investigating: "bg-cyan-500/15 text-cyan-300",
  awaiting_approval: "bg-amber-500/15 text-amber-200",
  responding: "bg-indigo-500/15 text-indigo-200",
  contained: "bg-emerald-500/15 text-emerald-300",
  resolved: "bg-emerald-700/20 text-emerald-200",
  rejected: "bg-rose-500/15 text-rose-200",
  healthy: "bg-emerald-500/15 text-emerald-300",
  suspicious: "bg-amber-500/15 text-amber-300",
  compromised: "bg-rose-500/15 text-rose-300",
  isolated: "bg-fuchsia-500/15 text-fuchsia-300",
};

export function Badge({ children, tone = "slate" }) {
  return (
    <span className={`inline-flex items-center rounded border px-2 py-0.5 font-mono text-[11px] uppercase tracking-wide ${tone}`}>
      {children}
    </span>
  );
}

export function SeverityBadge({ value }) {
  const key = String(value || "low").toLowerCase();
  return <Badge tone={severityClass[key] || severityClass.low}>{key}</Badge>;
}

export function StatusBadge({ value }) {
  const key = String(value || "new").toLowerCase();
  return <Badge tone={`${statusClass[key] || "bg-slate-500/20 text-slate-200"} border-white/10`}>{key.replaceAll("_", " ")}</Badge>;
}
