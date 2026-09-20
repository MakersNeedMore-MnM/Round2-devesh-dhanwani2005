export function Panel({ title, actions, children, className = "" }) {
  return (
    <section className={`rounded-xl border border-soc-border bg-soc-panel/90 ${className}`}>
      {(title || actions) && (
        <header className="flex items-center justify-between gap-3 border-b border-soc-border px-4 py-3">
          <h2 className="text-sm font-semibold tracking-wide text-slate-200">{title}</h2>
          {actions}
        </header>
      )}
      <div className="p-4">{children}</div>
    </section>
  );
}

export function StatCard({ label, value, hint }) {
  return (
    <div className="rounded-xl border border-soc-border bg-soc-panel p-4">
      <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{label}</div>
      <div className="mt-2 font-mono text-3xl text-soc-accent">{value}</div>
      {hint && <div className="mt-1 text-xs text-slate-500">{hint}</div>}
    </div>
  );
}

export function EmptyState({ title, body }) {
  return (
    <div className="rounded-lg border border-dashed border-soc-border px-4 py-10 text-center text-slate-400">
      <div className="font-medium text-slate-200">{title}</div>
      <p className="mt-2 text-sm">{body}</p>
    </div>
  );
}

export function ErrorState({ message }) {
  return (
    <div className="rounded-lg border border-rose-500/30 bg-rose-950/40 px-4 py-3 text-sm text-rose-100">
      {message}
    </div>
  );
}

export function Spinner({ label = "Loading" }) {
  return <div className="py-8 text-center font-mono text-sm text-slate-400">{label}…</div>;
}
