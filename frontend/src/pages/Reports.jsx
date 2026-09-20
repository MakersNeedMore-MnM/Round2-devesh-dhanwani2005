import { useCallback, useState } from "react";
import { IncidentsAPI } from "../services/api";
import { usePolling } from "../hooks/usePolling";
import { Panel, Spinner, ErrorState, EmptyState } from "../components/Panel";
import { useToast } from "../components/Toast";

export default function Reports() {
  const toast = useToast();
  const loader = useCallback(() => IncidentsAPI.list(), []);
  const { data, error, loading } = usePolling(loader, 10000);
  const [report, setReport] = useState(null);

  async function openReport(id) {
    try {
      const json = await IncidentsAPI.report(id);
      setReport(json);
    } catch (err) {
      toast.push(err.message, "error");
    }
  }

  function downloadJson() {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${report.incident_id || "incident"}-report.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  async function downloadPdf() {
    if (!report?.internal_id) return;
    const token = localStorage.getItem("cs_token");
    const url = IncidentsAPI.reportPdfUrl(report.internal_id);
    try {
      const response = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) throw new Error("PDF download failed");
      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = `${report.incident_id}-report.pdf`;
      link.click();
    } catch (err) {
      toast.push(err.message, "error");
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Incident reports</h1>
      <div className="grid gap-4 xl:grid-cols-[280px_1fr]">
        <Panel title="Incidents">
          {loading && !data ? (
            <Spinner />
          ) : error ? (
            <ErrorState message={error} />
          ) : (data || []).length === 0 ? (
            <EmptyState title="None" body="Create an incident first." />
          ) : (
            <ul className="space-y-2 text-sm">
              {data.map((row) => (
                <li key={row.id}>
                  <button className="text-left text-soc-accent" onClick={() => openReport(row.id)}>
                    {row.incident_number} · {row.title}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Panel>
        <Panel
          title="Report"
          actions={
            report ? (
              <div className="flex gap-2">
                <button className="text-xs text-soc-accent" onClick={downloadJson}>
                  Download JSON
                </button>
                <button className="text-xs text-soc-accent" onClick={downloadPdf}>
                  Download PDF
                </button>
              </div>
            ) : null
          }
        >
          {!report ? (
            <p className="text-sm text-slate-400">Select an incident to generate a report.</p>
          ) : (
            <div className="space-y-2 text-sm">
              <div className="font-mono text-soc-accent">{report.incident_id}</div>
              <div>
                Severity {report.severity} · Risk {report.risk_score} · Confidence {report.confidence}
              </div>
              <div>
                User {report.affected_user} · Status {report.status}
              </div>
              <pre className="max-h-[480px] overflow-auto rounded-md bg-black/30 p-3 text-xs">{JSON.stringify(report, null, 2)}</pre>
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
