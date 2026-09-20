import { useCallback, useState } from "react";
import { AssetsAPI } from "../services/api";
import { usePolling } from "../hooks/usePolling";
import { Panel, Spinner, ErrorState } from "../components/Panel";
import { StatusBadge, SeverityBadge } from "../components/Badges";

export default function Assets() {
  const loader = useCallback(() => AssetsAPI.list(), []);
  const { data, error, loading } = usePolling(loader, 12000);
  const [selected, setSelected] = useState(null);
  const rows = data || [];

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Assets</h1>
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
                  <th className="pb-2">Name</th>
                  <th>Type</th>
                  <th>IP</th>
                  <th>Hostname</th>
                  <th>Owner</th>
                  <th>Risk</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id} className="cursor-pointer border-t border-soc-border hover:bg-white/5" onClick={() => setSelected(row)}>
                    <td className="py-2 font-medium">{row.asset_name}</td>
                    <td>{row.asset_type}</td>
                    <td className="font-mono text-xs">{row.ip_address}</td>
                    <td className="font-mono text-xs">{row.hostname}</td>
                    <td>{row.owner}</td>
                    <td>
                      <SeverityBadge value={row.risk_level} />
                    </td>
                    <td>
                      <StatusBadge value={row.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
      {selected && (
        <Panel title={`Asset ${selected.asset_name}`} actions={<button onClick={() => setSelected(null)} className="text-xs text-slate-400">Close</button>}>
          <pre className="overflow-auto text-xs text-slate-300">{JSON.stringify(selected, null, 2)}</pre>
        </Panel>
      )}
    </div>
  );
}
