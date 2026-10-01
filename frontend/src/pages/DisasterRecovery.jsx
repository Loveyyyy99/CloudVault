import { useCallback, useEffect, useState } from "react";
import StatusBadge from "../components/StatusBadge.jsx";
import api, { downloadFile, errorMessage } from "../services/api.js";
import { PROVIDER_LABEL } from "../utils/format.js";

const DOT = { HEALTHY: "bg-emerald-500", UNAVAILABLE: "bg-red-500", SIMULATED_FAILURE: "bg-red-500" };
const TEXT = { HEALTHY: "HEALTHY", UNAVAILABLE: "UNAVAILABLE", SIMULATED_FAILURE: "SIMULATED FAILURE" };

export default function DisasterRecovery() {
  const [health, setHealth] = useState({});
  const [files, setFiles] = useState([]);
  const [fileId, setFileId] = useState("");
  const [attempts, setAttempts] = useState(null);
  const [note, setNote] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const [a, z, f] = await Promise.allSettled([api.get("/cloud/b2/status"), api.get("/cloud/supabase/status"), api.get("/files")]);
    setHealth({ b2: a.value?.data.status || "UNAVAILABLE", supabase: z.value?.data.status || "UNAVAILABLE" });
    if (f.value) { setFiles(f.value.data); setFileId((cur) => cur || f.value.data[0]?.id || ""); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const sim = async (path) => {
    setBusy(true); setAttempts(null); setNote(null);
    try { await api.post(`/simulation/${path}`); await load(); }
    catch (e) { setNote({ ok: false, text: await errorMessage(e) }); }
    finally { setBusy(false); }
  };

  const restore = async () => {
    const file = files.find((f) => f.id === fileId);
    setBusy(true); setAttempts(null); setNote(null);
    try {
      const r = await downloadFile(file, "smart");
      setAttempts(r.attempts); setNote({ ok: true, text: `RESTORE SUCCESSFUL — recovered from ${PROVIDER_LABEL[r.source]}.` });
    } catch (e) {
      const data = e.response?.data instanceof Blob ? JSON.parse(await e.response.data.text()) : e.response?.data;
      setAttempts(data?.attempts || null); setNote({ ok: false, text: await errorMessage(e) });
    } finally { setBusy(false); }
  };

  const down = Object.entries(health).filter(([, s]) => s !== "HEALTHY").map(([p]) => p);
  const up = Object.entries(health).filter(([, s]) => s === "HEALTHY").map(([p]) => p);

  return (
    <div className="max-w-3xl space-y-5">
      <h1 className="text-xl font-bold">Disaster Recovery Lab</h1>
      <p className="text-sm text-slate-500">Simulations are software-level only: cloud data is never touched. They just disable that provider inside CloudVault.</p>

      <div className="grid gap-4 sm:grid-cols-2">
        {["b2", "supabase"].map((p) => (
          <div key={p} className="card">
            <div className="label">{PROVIDER_LABEL[p]}</div>
            <div className="flex items-center gap-2 text-lg font-semibold">
              <span className={`h-2.5 w-2.5 rounded-full ${DOT[health[p]] || "bg-slate-300"}`} />{TEXT[health[p]] || "CHECKING…"}
            </div>
          </div>
        ))}
      </div>
      {down.length > 0 && up.length > 0 && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800">Recovery available from {up.map((p) => PROVIDER_LABEL[p]).join(", ")}.</div>
      )}

      <div className="flex flex-wrap gap-2">
        <button className="btn-danger" disabled={busy} onClick={() => sim("b2-failure")}>Simulate B2 Failure</button>
        <button className="btn-danger" disabled={busy} onClick={() => sim("supabase-failure")}>Simulate Supabase Failure</button>
        <button className="btn-ghost" disabled={busy} onClick={() => sim("reset")}>Reset Simulation</button>
      </div>

      <div className="card space-y-3">
        <div className="label">Smart restore</div>
        {files.length === 0 ? <p className="text-sm text-slate-500">Upload a file first.</p> : (
          <>
            <select className="input" value={fileId} onChange={(e) => setFileId(e.target.value)}>
              {files.map((f) => <option key={f.id} value={f.id}>{f.filename} ({f.status})</option>)}
            </select>
            <button className="btn-primary" disabled={busy || !fileId} onClick={restore}>{busy ? "Working…" : "Smart Restore"}</button>
          </>
        )}
        {note && <p className={`text-sm font-medium ${note.ok ? "text-emerald-700" : "text-red-600"}`}>{note.text}</p>}
        {attempts && (
          <ol className="space-y-1 rounded-lg bg-slate-50 p-3 font-mono text-xs">
            {attempts.map((a, i) => (
              <li key={i}>{i + 1}. Check {PROVIDER_LABEL[a.provider]} → {a.ok ? "✓" : "✗"} {a.reason}</li>
            ))}
            {attempts.some((a) => a.ok) && <li className="font-semibold text-emerald-700">→ SHA-256 verified · <StatusBadge status="RESTORED" /></li>}
          </ol>
        )}
      </div>
    </div>
  );
}
