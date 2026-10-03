import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import StatusBadge from "../components/StatusBadge.jsx";
import api, { errorMessage } from "../services/api.js";
import { fmtBytes, PROVIDER_LABEL, timeAgo } from "../utils/format.js";
import Loader from "../components/Loader.jsx";

const Stat = ({ label, value }) => (
  <div className="card"><div className="label">{label}</div><div className="text-2xl font-bold tracking-tight">{value}</div></div>
);

function Meter({ label, pct, color }) {
  const warn = pct >= 80;
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm"><span>{label}</span><span className={warn ? "font-semibold text-amber-700" : "text-slate-500"}>{pct}%</span></div>
      <div className="h-2 rounded-full bg-slate-100"><div className="h-2 rounded-full" style={{ width: `${pct}%`, background: warn ? "#d97706" : color }} /></div>
    </div>
  );
}

export default function Dashboard() {
  const [s, setS] = useState(null);
  const [health, setHealth] = useState({});
  const [error, setError] = useState(null);
  const [price, setPrice] = useState(() => JSON.parse(localStorage.getItem("cv_price") || '{"b2":0.006,"supabase":0.021}'));

  useEffect(() => {
    api.get("/dashboard/stats").then((r) => setS(r.data)).catch(async (e) => setError(await errorMessage(e)));
    Promise.allSettled([api.get("/cloud/b2/status"), api.get("/cloud/supabase/status")]).then(([a, z]) =>
      setHealth({ b2: a.value?.data.status || "UNAVAILABLE", supabase: z.value?.data.status || "UNAVAILABLE" }));
  }, []);
  useEffect(() => localStorage.setItem("cv_price", JSON.stringify(price)), [price]);

  if (error) return <p className="text-red-600">{error}</p>;
  if (!s) return <Loader />;
  const { totals: t, providers: p, metrics: m, limits } = s;
  const usage = [{ name: "Backblaze B2", MB: +(p.b2.used / 1048576).toFixed(2) }, { name: "Supabase Storage", MB: +(p.supabase.used / 1048576).toFixed(2) }];
  const gb = (b) => b / 1073741824;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold">Dashboard</h1>
      {(s.usage.storage_pct >= 80 || s.usage.daily_pct >= 80) && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">You are approaching your free-tier limits ({s.usage.storage_pct}% storage, {t.uploads_today}/{limits.max_daily_uploads} uploads today).</div>
      )}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Total files" value={t.files} />
        <Stat label="Total storage" value={fmtBytes(t.bytes)} />
        <Stat label="Verified backups" value={t.verified} />
        <Stat label="Failed / partial" value={t.failed + t.partial} />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="card lg:col-span-1">
          <div className="label">Cloud health</div>
          <div className="space-y-2">
            {["b2", "supabase"].map((k) => <div key={k} className="flex items-center justify-between text-sm"><span>{PROVIDER_LABEL[k]}</span><StatusBadge status={health[k] || "PENDING"} /></div>)}
          </div>
          <div className="label mt-5">Storage usage (of {fmtBytes(limits.max_total_storage)} limit)</div>
          <div className="space-y-3"><Meter label="Backblaze B2" pct={p.b2.pct} color="#e21e29" /><Meter label="Supabase Storage" pct={p.supabase.pct} color="#3ecf8e" /></div>
        </div>
        <div className="card lg:col-span-2">
          <div className="label">Storage comparison (MB)</div>
          <div className="h-52"><ResponsiveContainer><BarChart data={usage}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="name" /><YAxis /><Tooltip /><Bar dataKey="MB" fill="#0f172a" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></div>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="card lg:col-span-2">
          <div className="label">Backups, last 7 days</div>
          <div className="h-52"><ResponsiveContainer><BarChart data={s.trend}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="day" /><YAxis allowDecimals={false} /><Tooltip /><Legend /><Bar dataKey="ok" name="Verified" stackId="a" fill="#10b981" /><Bar dataKey="bad" name="Failed" stackId="a" fill="#ef4444" /></BarChart></ResponsiveContainer></div>
        </div>
        <div className="card space-y-3 text-sm">
          <div className="label">Monitoring</div>
          <div className="flex justify-between"><span>Backup success rate</span><b>{m.success_rate === null ? "—" : `${m.success_rate}%`}</b></div>
          <div className="flex justify-between"><span>Failed backups</span><b>{m.failed_backups}</b></div>
          <div className="flex justify-between"><span>Avg backup time</span><b>{m.avg_backup_ms ? `${(m.avg_backup_ms / 1000).toFixed(1)} s` : "—"}</b></div>
          <div className="flex justify-between"><span>Last successful backup</span><b>{timeAgo(m.last_success)}</b></div>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <div className="label">Recent backups</div>
          {s.recent.length === 0 && <p className="text-sm text-slate-400">Nothing yet.</p>}
          {s.recent.map((f) => <div key={f.id} className="flex items-center justify-between border-b border-slate-100 py-2 text-sm last:border-0"><span>{f.filename}</span><StatusBadge status={f.status} /></div>)}
        </div>
        <div className="card text-sm">
          <div className="label">Cost estimator (your own $/GB-month prices)</div>
          {["b2", "supabase"].map((k) => (
            <div key={k} className="mb-2 flex items-center justify-between gap-3">
              <span>{PROVIDER_LABEL[k]}</span>
              <input type="number" step="0.001" min="0" className="input !w-24" value={price[k]} onChange={(e) => setPrice({ ...price, [k]: +e.target.value })} />
              <b className="w-20 text-right">${(gb(p[k].used) * price[k]).toFixed(4)}</b>
            </div>
          ))}
          <p className="mt-2 text-xs text-slate-400">An estimate from stored bytes × the prices you enter — not real billing data.</p>
        </div>
      </div>
    </div>
  );
}
