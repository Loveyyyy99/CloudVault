import { useCallback, useEffect, useState } from "react";
import StatusBadge, { ProviderMark } from "../components/StatusBadge.jsx";
import api, { downloadFile, errorMessage } from "../services/api.js";
import { fmtBytes, PROVIDER_LABEL, timeAgo } from "../utils/format.js";

const FILTERS = ["ALL", "VERIFIED", "PARTIAL", "FAILED", "PENDING"];

export default function Backups() {
  const [filter, setFilter] = useState("ALL");
  const [rows, setRows] = useState(null);
  const [busy, setBusy] = useState(null);
  const [note, setNote] = useState(null);

  const load = useCallback(async () => {
    try {
      const { data } = await api.get("/backups/history", { params: filter === "ALL" ? {} : { status: filter } });
      setRows(data);
    } catch (e) { setNote({ ok: false, text: await errorMessage(e) }); setRows([]); }
  }, [filter]);
  useEffect(() => { load(); }, [load]);

  const act = async (f, label, fn) => {
    setBusy(f.id + label); setNote(null);
    try { const t = await fn(); if (t) setNote({ ok: true, text: t }); await load(); }
    catch (e) { setNote({ ok: false, text: await errorMessage(e) }); }
    finally { setBusy(null); }
  };

  const message = (f) => {
    const bad = f.backups.filter((b) => b.status !== "VERIFIED"), good = f.backups.filter((b) => b.status === "VERIFIED");
    if (!bad.length || f.status === "UPLOADING") return null;
    return good.length
      ? `${bad.map((b) => PROVIDER_LABEL[b.provider]).join(", ")} backup failed. Your ${good.map((b) => PROVIDER_LABEL[b.provider]).join(", ")} backup is still available.`
      : "No verified copy exists. Delete this record and upload the file again.";
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-bold">Backup history</h1>
        <div className="flex gap-1 rounded-lg bg-slate-200 p-1 text-xs font-medium">
          {FILTERS.map((s) => (
            <button key={s} onClick={() => setFilter(s)} className={`rounded-md px-3 py-1 ${filter === s ? "bg-white shadow-sm" : "text-slate-600"}`}>{s[0] + s.slice(1).toLowerCase()}</button>
          ))}
        </div>
      </div>
      {note && <p className={`text-sm ${note.ok ? "text-emerald-700" : "text-red-600"}`}>{note.text}</p>}

      <div className="card overflow-x-auto p-0">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
            <tr><th className="p-3">File</th><th className="p-3 text-center">Backblaze B2</th><th className="p-3 text-center">Supabase</th><th className="p-3">Status</th><th className="p-3">Date</th><th className="p-3 text-right">Actions</th></tr>
          </thead>
          <tbody>
            {rows === null && <tr><td colSpan={6} className="p-6 text-center text-slate-400">Loading…</td></tr>}
            {rows?.length === 0 && <tr><td colSpan={6} className="p-6 text-center text-slate-400">No backups found.</td></tr>}
            {rows?.map((f) => {
              const by = Object.fromEntries(f.backups.map((b) => [b.provider, b]));
              const msg = message(f);
              return (
                <tr key={f.id} className="border-b border-slate-100 align-top last:border-0">
                  <td className="p-3"><div className="font-medium">{f.filename}</div><div className="text-xs text-slate-500">{fmtBytes(f.size)}</div>{msg && <div className="mt-1 max-w-xs text-xs text-amber-700">{msg}</div>}</td>
                  <td className="p-3 text-center"><ProviderMark backup={by.b2} /></td>
                  <td className="p-3 text-center"><ProviderMark backup={by.supabase} /></td>
                  <td className="p-3"><StatusBadge status={f.status} /></td>
                  <td className="whitespace-nowrap p-3 text-slate-500">{timeAgo(f.created_at)}</td>
                  <td className="p-3">
                    <div className="flex flex-wrap justify-end gap-1.5">
                      <button className="btn-ghost !px-2.5 !py-1 text-xs" disabled={!!busy} onClick={() => act(f, "smart", async () => { const r = await downloadFile(f, "smart"); return `Restored from ${PROVIDER_LABEL[r.source]} (SHA-256 verified).`; })}>Smart restore</button>
                      <button className="btn-ghost !px-2.5 !py-1 text-xs" disabled={!!busy} onClick={() => act(f, "b2", () => downloadFile(f, "b2").then(() => "Downloaded from Backblaze B2."))}>B2</button>
                      <button className="btn-ghost !px-2.5 !py-1 text-xs" disabled={!!busy} onClick={() => act(f, "supabase", () => downloadFile(f, "supabase").then(() => "Downloaded from Supabase Storage."))}>Supabase</button>
                      {f.status !== "VERIFIED" && <button className="btn-ghost !px-2.5 !py-1 text-xs" disabled={!!busy} onClick={() => act(f, "retry", async () => { await api.post(`/files/${f.id}/retry`); return "Retry finished."; })}>{busy === f.id + "retry" ? "Retrying…" : "Retry"}</button>}
                      <button className="btn-danger !px-2.5 !py-1 text-xs" disabled={!!busy} onClick={() => window.confirm(`Delete ${f.filename} from both clouds?`) && act(f, "del", async () => { await api.delete(`/files/${f.id}`); return "Deleted from all clouds."; })}>Delete</button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
