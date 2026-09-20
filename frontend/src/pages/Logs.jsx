import { useCallback, useState } from "react";
import { LogsAPI } from "../services/api";
import { usePolling } from "../hooks/usePolling";
import { Panel, Spinner, ErrorState, EmptyState } from "../components/Panel";
import { SeverityBadge } from "../components/Badges";
import { useToast } from "../components/Toast";
import { formatTime } from "../utils/format";

export default function Logs() {
  const toast = useToast();
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState("");
  const [eventType, setEventType] = useState("");
  const [progress, setProgress] = useState("");
  const loader = useCallback(
    () => LogsAPI.list({ search, severity, event_type: eventType }),
    [search, severity, eventType]
  );
  const { data, error, loading, refresh } = usePolling(loader, 8000);
  const rows = data || [];

  async function onUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setProgress("Uploading and normalizing…");
    try {
      const result = await LogsAPI.upload(file);
      setProgress(`Inserted ${result.inserted_count || 0}. Duplicates ${result.duplicate_count || 0}. Errors ${result.error_count || 0}.`);
      toast.push("Logs ingested", "success");
      refresh();
    } catch (err) {
      setProgress("");
      toast.push(err.message, "error");
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h1 className="text-2xl font-semibold">Security logs</h1>
        <label className="cursor-pointer rounded-md bg-soc-accent px-3 py-2 text-sm font-semibold text-slate-950">
          Upload JSON/CSV
          <input type="file" accept=".json,.csv,application/json,text/csv" className="hidden" onChange={onUpload} />
        </label>
      </div>
      {progress && <div className="font-mono text-xs text-soc-accent">{progress}</div>}
      <div className="flex flex-wrap gap-2">
        <input className="rounded-md border border-soc-border bg-soc-panel px-3 py-2 text-sm" placeholder="Search" value={search} onChange={(e) => setSearch(e.target.value)} />
        <input className="rounded-md border border-soc-border bg-soc-panel px-3 py-2 text-sm" placeholder="Event type" value={eventType} onChange={(e) => setEventType(e.target.value)} />
        <select className="rounded-md border border-soc-border bg-soc-panel px-3 py-2 text-sm" value={severity} onChange={(e) => setSeverity(e.target.value)}>
          <option value="">All severities</option>
          {["low", "medium", "high", "critical"].map((item) => (
            <option key={item}>{item}</option>
          ))}
        </select>
      </div>
      <Panel>
        {loading && !data ? (
          <Spinner />
        ) : error ? (
          <ErrorState message={error} />
        ) : rows.length === 0 ? (
          <EmptyState title="No logs" body="Upload a JSON/CSV file or load the demo attack." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase text-slate-500">
                <tr>
                  <th className="pb-2">Timestamp</th>
                  <th>Event</th>
                  <th>User</th>
                  <th>Src</th>
                  <th>Dst</th>
                  <th>Asset</th>
                  <th>Sev</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id} className="border-t border-soc-border">
                    <td className="py-2 whitespace-nowrap font-mono text-xs">{formatTime(row.timestamp)}</td>
                    <td>
                      <span className="rounded border border-cyan-500/20 px-2 py-0.5 font-mono text-[11px] text-cyan-200">{row.event_type}</span>
                    </td>
                    <td>{row.user_name}</td>
                    <td className="font-mono text-xs">{row.source_ip}</td>
                    <td className="font-mono text-xs">{row.destination_ip}</td>
                    <td className="font-mono text-xs">{row.asset_id || "—"}</td>
                    <td>
                      <SeverityBadge value={row.severity} />
                    </td>
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
