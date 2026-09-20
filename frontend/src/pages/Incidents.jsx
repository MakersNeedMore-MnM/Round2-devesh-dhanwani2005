import { useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { IncidentsAPI } from "../services/api";
import { usePolling } from "../hooks/usePolling";
import { Panel, Spinner, ErrorState, EmptyState } from "../components/Panel";
import { SeverityBadge, StatusBadge } from "../components/Badges";
import { formatTime } from "../utils/format";

export default function Incidents() {
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("");
  const loader = useCallback(
    () => IncidentsAPI.list({ search, severity, status }),
    [search, severity, status]
  );
  const { data, error, loading } = usePolling(loader, 8000);
  const rows = data || [];
  const sorted = useMemo(() => rows, [rows]);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Incidents</h1>
      <div className="flex flex-wrap gap-2">
        <input
          className="rounded-md border border-soc-border bg-soc-panel px-3 py-2 text-sm"
          placeholder="Search ID, title, user"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select className="rounded-md border border-soc-border bg-soc-panel px-3 py-2 text-sm" value={severity} onChange={(e) => setSeverity(e.target.value)}>
          <option value="">All severities</option>
          {["low", "medium", "high", "critical"].map((item) => (
            <option key={item}>{item}</option>
          ))}
        </select>
        <select className="rounded-md border border-soc-border bg-soc-panel px-3 py-2 text-sm" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          {["new", "investigating", "awaiting_approval", "responding", "contained", "resolved", "rejected"].map((item) => (
            <option key={item}>{item}</option>
          ))}
        </select>
      </div>
      <Panel>
        {loading && !data ? (
          <Spinner />
        ) : error ? (
          <ErrorState message={error} />
        ) : sorted.length === 0 ? (
          <EmptyState title="No incidents" body="Load Demo Attack to correlate the account-compromise chain." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase text-slate-500">
                <tr>
                  <th className="pb-2">Incident ID</th>
                  <th>Title</th>
                  <th>Severity</th>
                  <th>Risk</th>
                  <th>Confidence</th>
                  <th>User</th>
                  <th>Asset</th>
                  <th>Status</th>
                  <th>Detected</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((row) => (
                  <tr key={row.id} className="border-t border-soc-border hover:bg-white/5">
                    <td className="py-2 font-mono text-soc-accent">
                      <Link to={`/incidents/${row.id}`}>{row.incident_number}</Link>
                    </td>
                    <td>{row.title}</td>
                    <td>
                      <SeverityBadge value={row.severity} />
                    </td>
                    <td className="font-mono">{row.risk_score}/100</td>
                    <td className="font-mono">{row.confidence_score}%</td>
                    <td>{row.affected_user || "—"}</td>
                    <td className="font-mono text-xs">{row.affected_asset || "—"}</td>
                    <td>
                      <StatusBadge value={row.status} />
                    </td>
                    <td className="whitespace-nowrap text-xs text-slate-400">{formatTime(row.detected_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  );
}
