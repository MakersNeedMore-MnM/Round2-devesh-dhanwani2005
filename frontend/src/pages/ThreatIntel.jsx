import { useCallback } from "react";
import { IntelAPI } from "../services/api";
import { usePolling } from "../hooks/usePolling";
import { Panel, Spinner, ErrorState } from "../components/Panel";

export default function ThreatIntel() {
  const loader = useCallback(() => IntelAPI.list(), []);
  const { data, error, loading } = usePolling(loader, 15000);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Threat intelligence</h1>
      <p className="text-sm text-amber-200/90">
        Sample / internal indicators only. This page does not claim a live commercial threat-intel integration.
      </p>
      <Panel>
        {loading && !data ? (
          <Spinner />
        ) : error ? (
          <ErrorState message={error} />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase text-slate-500">
                <tr>
                  <th className="pb-2">Indicator</th>
                  <th>Type</th>
                  <th>Reputation</th>
                  <th>Confidence</th>
                  <th>Source</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {(data?.indicators || []).map((row) => (
                  <tr key={row.id} className="border-t border-soc-border">
                    <td className="py-2 font-mono text-soc-accent">{row.indicator_value}</td>
                    <td>{row.indicator_type}</td>
                    <td>{row.reputation}</td>
                    <td className="font-mono">{row.confidence}</td>
                    <td>{row.source}</td>
                    <td className="max-w-sm truncate text-xs text-slate-400">{JSON.stringify(row.details)}</td>
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
