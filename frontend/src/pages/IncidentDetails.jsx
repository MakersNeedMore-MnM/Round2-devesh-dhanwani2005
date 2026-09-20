import { useCallback, useState } from "react";
import { useParams } from "react-router-dom";
import { IncidentsAPI } from "../services/api";
import { usePolling } from "../hooks/usePolling";
import { Panel, Spinner, ErrorState } from "../components/Panel";
import { SeverityBadge, StatusBadge } from "../components/Badges";
import { useToast } from "../components/Toast";
import { asList, formatTime, shortTime } from "../utils/format";

export default function IncidentDetails() {
  const { id } = useParams();
  const toast = useToast();
  const [busy, setBusy] = useState("");
  const [selectedLog, setSelectedLog] = useState(null);
  const loader = useCallback(() => IncidentsAPI.get(id), [id]);
  const { data, error, loading, refresh } = usePolling(loader, 6000);

  async function run(label, fn) {
    setBusy(label);
    try {
      await fn();
      await refresh();
      toast.push("Updated", "success");
    } catch (err) {
      toast.push(err.message, "error");
    } finally {
      setBusy("");
    }
  }

  if (loading && !data) return <Spinner label="Loading incident" />;
  if (error) return <ErrorState message={error} />;
  if (!data) return null;

  const assessment = data.investigation?.ai_assessment || {};
  const evidence = asList(assessment.evidence || data.investigation?.evidence);
  const impact = asList(data.potential_impact || assessment.potential_impact);
  const factors = Array.isArray(data.risk_factors) ? data.risk_factors : [];
  const recs = data.recommendations || [];
  const verification = (data.recommendations || [])
    .map(() => null);
  const latestVerification =
    recs.find((row) => row.status === "executed") ? data.status === "contained" || data.status === "resolved" ? data.status : "pending" : "pending";

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-soc-border bg-soc-panel p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="font-mono text-soc-accent">INCIDENT #{data.incident_number}</div>
            <h1 className="mt-1 text-3xl font-semibold">{data.title}</h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-400">{data.description}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <SeverityBadge value={data.severity} />
            <StatusBadge value={data.status} />
          </div>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-4">
          <Metric label="Risk" value={`${data.risk_score}/100`} />
          <Metric label="Confidence" value={`${data.confidence_score}%`} />
          <Metric label="Affected user" value={data.affected_user || "—"} />
          <Metric label="Detected" value={formatTime(data.detected_at)} />
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            className="rounded-md bg-soc-accent px-3 py-2 text-sm font-semibold text-slate-950"
            disabled={!!busy}
            onClick={() => run("investigate", () => IncidentsAPI.investigate(data.id))}
          >
            {busy === "investigate" ? "Investigating…" : "Run AI Investigation"}
          </button>
          <button className="rounded-md border border-soc-border px-3 py-2 text-sm" disabled={!!busy} onClick={() => run("verify", () => IncidentsAPI.verify(data.id))}>
            Run verification
          </button>
          <button
            className="rounded-md border border-soc-border px-3 py-2 text-sm"
            disabled={!!busy || data.status !== "contained"}
            onClick={() => run("resolve", () => IncidentsAPI.resolve(data.id))}
          >
            Mark resolved
          </button>
        </div>
      </div>

      <Panel title="Incident timeline">
        <ol className="space-y-3">
          {(data.events || []).map((event) => (
            <li key={event.id}>
              <button className="w-full rounded-md border border-soc-border px-3 py-2 text-left hover:bg-white/5" onClick={() => setSelectedLog(event)}>
                <div className="flex items-center justify-between gap-3">
                  <span className="font-mono text-soc-accent">{shortTime(event.timestamp)}</span>
                  <SeverityBadge value={event.severity} />
                </div>
                <div className="mt-1 text-sm">{event.message}</div>
                <div className="font-mono text-xs text-slate-500">{event.event_type} · {event.source_ip}</div>
              </button>
            </li>
          ))}
        </ol>
      </Panel>

      <div className="grid gap-4 xl:grid-cols-2">
        <Panel title="AI investigation summary">
          <p className="text-sm leading-6 text-slate-200">{assessment.summary || data.ai_summary || "Run AI Investigation to generate an evidence-bounded assessment."}</p>
          {assessment.reasoning && (
            <p className="mt-3 text-sm text-slate-400">{assessment.reasoning}</p>
          )}
          {assessment.attack_pattern && (
            <p className="mt-3 font-mono text-xs text-soc-accent">{assessment.attack_pattern}</p>
          )}
        </Panel>
        <Panel title="Evidence">
          {evidence.length === 0 ? (
            <p className="text-sm text-slate-400">No investigation evidence yet.</p>
          ) : (
            <ul className="space-y-2">
              {evidence.map((item) => (
                <li key={item}>
                  <button
                    className="w-full rounded-md border border-soc-border px-3 py-2 text-left text-sm hover:bg-white/5"
                    onClick={() => setSelectedLog((data.events || []).find((event) => (event.message || "").toLowerCase().includes(String(item).split(" ")[0])) || selectedLog)}
                  >
                    {item}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Panel title="Potential impact">
          <ul className="list-disc space-y-1 pl-5 text-sm">
            {impact.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </Panel>
        <Panel title="Risk factors">
          <p className="mb-3 text-xs text-slate-500">Transparent sum of matched detection-rule weights, clamped 0–100.</p>
          <ul className="space-y-2">
            {factors.map((factor) => (
              <li key={factor.indicator} className="flex items-center justify-between rounded-md border border-soc-border px-3 py-2 text-sm">
                <span>
                  {factor.indicator}
                  <span className="block text-xs text-slate-500">{factor.detail}</span>
                </span>
                <span className="font-mono text-soc-accent">+{factor.points}</span>
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <Panel title="Recommended response">
        <div className="space-y-3">
          {recs.map((rec) => (
            <div key={rec.id} className="rounded-lg border border-soc-border p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <div className="font-medium">{rec.description}</div>
                  <div className="font-mono text-xs text-slate-500">
                    {rec.action_type} · priority {rec.priority} · {rec.requires_approval ? "requires approval" : "low impact"} · {rec.status}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    className="rounded-md bg-soc-accent px-3 py-1.5 text-xs font-semibold text-slate-950 disabled:opacity-50"
                    disabled={!!busy || rec.status !== "pending"}
                    onClick={() => run("approve", () => IncidentsAPI.approve(data.id, rec.id))}
                  >
                    Approve
                  </button>
                  <button
                    className="rounded-md border border-rose-500/40 px-3 py-1.5 text-xs text-rose-200 disabled:opacity-50"
                    disabled={!!busy || rec.status !== "pending"}
                    onClick={() => run("reject", () => IncidentsAPI.reject(data.id, rec.id, "Rejected by analyst"))}
                  >
                    Reject
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="Verification">
        <StatusBadge value={data.status === "contained" || data.status === "resolved" ? "verified" : latestVerification} />
        <p className="mt-2 text-sm text-slate-400">
          After simulated containment (for example disabling the account), CyberSentinel checks whether new successful logins
          occurred. The incident moves responding → contained → resolved only after verification succeeds.
        </p>
      </Panel>

      {selectedLog && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 p-4" onClick={() => setSelectedLog(null)}>
          <div className="max-h-[80vh] w-full max-w-lg overflow-auto rounded-xl border border-soc-border bg-soc-panel p-5" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold">Event detail</h3>
            <pre className="mt-3 overflow-auto rounded-md bg-black/40 p-3 text-xs text-slate-300">{JSON.stringify(selectedLog, null, 2)}</pre>
            <button className="mt-3 text-sm text-soc-accent" onClick={() => setSelectedLog(null)}>
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-md border border-soc-border px-3 py-2">
      <div className="text-[11px] uppercase tracking-wide text-slate-500">{label}</div>
      <div className="font-mono text-lg text-white">{value}</div>
    </div>
  );
}
