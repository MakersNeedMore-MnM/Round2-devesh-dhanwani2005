import { useAuth } from "../hooks/useAuth";
import { Panel } from "../components/Panel";

export default function Settings() {
  const { user } = useAuth();
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <Panel title="Analyst profile">
        <dl className="grid gap-2 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-slate-500">Name</dt>
            <dd>{user?.full_name}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Email</dt>
            <dd>{user?.email}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Role</dt>
            <dd className="uppercase">{user?.role}</dd>
          </div>
        </dl>
      </Panel>
      <Panel title="Security notes">
        <ul className="list-disc space-y-2 pl-5 text-sm text-slate-300">
          <li>Response actions are simulated. This console does not disable real accounts or isolate real hosts.</li>
          <li>AI API keys and the Supabase service role stay on the FastAPI backend.</li>
          <li>VITE_SUPABASE_ANON_KEY is optional and only needed if you later add direct Supabase Auth in the browser.</li>
          <li>Realtime can be added on top of the current polling loop without changing the data model.</li>
        </ul>
      </Panel>
    </div>
  );
}
