import { useCallback } from "react";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Line, LineChart } from "recharts";
import { DashboardAPI } from "../services/api";
import { usePolling } from "../hooks/usePolling";
import { Panel, StatCard, Spinner, ErrorState, EmptyState } from "../components/Panel";
import { SeverityBadge, StatusBadge } from "../components/Badges";
import { formatTime } from "../utils/format";

const COLORS = ["#7dd3fc", "#fbbf24", "#fb923c", "#fb7185"];

export default function Dashboard() {
  const loader = useCallback(() => DashboardAPI.stats(), []);
  const { data, error, loading } = usePolling(loader, 8000);

  if (loading && !data) return <Spinner label="Loading SOC dashboard" />;
  if (error) return <ErrorState message={error} />;
  if (!data) return <EmptyState title="No telemetry" body="Load the demo attack or ingest logs." />;

  const severityData = Object.entries(data.incidents_by_severity || {}).map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Operations overview</h1>
        <p className="text-sm text-slate-400">Observe · Detect · Investigate · Reason · Plan · Act · Verify</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <StatCard label="Total events" value={data.total_events} />
        <StatCard label="Active incidents" value={data.active_incidents} />
        <StatCard label="Critical" value={data.critical_incidents} />
        <StatCard label="High-risk" value={data.high_risk_incidents} hint="Risk ≥ 61" />
        <StatCard label="Resolved" value={data.resolved_incidents} />
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <Panel title="Incidents by severity">
          <div className="h-56">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={severityData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80}>
                  {severityData.map((entry, index) => (
                    <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Panel>
        <Panel title="Incidents over time">
          <div className="h-56">
            <ResponsiveContainer>
              <LineChart data={data.incidents_over_time || []}>
                <CartesianGrid stroke="#1c2a44" />
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" fontSize={11} allowDecimals={false} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#3ee0c5" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>
        <Panel title="Event types">
          <div className="h-56">
            <ResponsiveContainer>
              <BarChart data={data.event_types || []}>
                <CartesianGrid stroke="#1c2a44" />
                <XAxis dataKey="type" stroke="#94a3b8" fontSize={10} interval={0} angle={-20} textAnchor="end" height={60} />
                <YAxis stroke="#94a3b8" fontSize={11} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#38bdf8" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
        <Panel title="Risk distribution">
          <div className="h-56">
            <ResponsiveContainer>
              <BarChart data={data.risk_distribution || []}>
                <CartesianGrid stroke="#1c2a44" />
                <XAxis dataKey="bucket" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" fontSize={11} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#fb7185" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <Panel title="Recent incidents">
          {(data.recent_incidents || []).length === 0 ? (
            <EmptyState title="No incidents" body="Click Load Demo Attack to generate CS-1042." />
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase text-slate-500">
                <tr>
                  <th className="pb-2">ID</th>
                  <th>Title</th>
                  <th>Sev</th>
                  <th>Risk</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_incidents.map((row) => (
                  <tr key={row.id} className="border-t border-soc-border">
                    <td className="py-2 font-mono text-soc-accent">
                      <Link to={`/incidents/${row.id}`}>{row.incident_number}</Link>
                    </td>
                    <td>{row.title}</td>
                    <td>
                      <SeverityBadge value={row.severity} />
                    </td>
                    <td className="font-mono">{row.risk_score}</td>
                    <td>
                      <StatusBadge value={row.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>
        <Panel title="Recent security events">
          <div className="space-y-2">
            {(data.recent_events || []).map((event) => (
              <div key={event.id} className="rounded-md border border-soc-border/80 px-3 py-2 text-sm">
                <div className="flex justify-between gap-2 font-mono text-xs text-slate-400">
                  <span>{formatTime(event.timestamp)}</span>
                  <SeverityBadge value={event.severity} />
                </div>
                <div className="mt-1 text-slate-200">{event.message}</div>
              </div>
            ))}
          </div>
        </Panel>
      </div>
      <Panel title="System status">
        <div className="grid gap-3 sm:grid-cols-4 font-mono text-sm">
          {Object.entries(data.system_status || {}).map(([key, value]) => (
            <div key={key} className="rounded-md border border-soc-border px-3 py-2">
              <div className="text-[11px] uppercase text-slate-500">{key}</div>
              <div className="text-soc-accent">{String(value)}</div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
