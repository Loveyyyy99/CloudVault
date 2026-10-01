import { useEffect, useState } from "react";
import BackupResult from "../components/BackupResult.jsx";
import api, { errorMessage } from "../services/api.js";
import { fmtBytes, sha256File, timeAgo } from "../utils/format.js";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [hash, setHash] = useState("");
  const [desc, setDesc] = useState("");
  const [progress, setProgress] = useState(null);
  const [result, setResult] = useState(null);
  const [dup, setDup] = useState(null);
  const [error, setError] = useState(null);
  const [limits, setLimits] = useState(null);
  const [retrying, setRetrying] = useState(false);

  useEffect(() => { api.get("/dashboard/stats").then((r) => setLimits(r.data.limits)).catch(() => {}); }, []);

  const pick = async (f) => {
    setFile(f); setHash(""); setResult(null); setDup(null); setError(null);
    if (f && (!limits || f.size <= limits.max_file_size)) setHash(await sha256File(f));
    if (f && limits && f.size > limits.max_file_size) setError(`File exceeds the ${fmtBytes(limits.max_file_size)} limit.`);
  };

  const upload = async () => {
    setError(null); setResult(null); setDup(null); setProgress(0);
    const fd = new FormData();
    fd.append("file", file); fd.append("description", desc);
    try {
      const { data } = await api.post("/files/upload", fd, { onUploadProgress: (e) => setProgress(Math.round((e.loaded * 100) / (e.total || file.size))) });
      setResult(data.file);
    } catch (e) {
      if (e.response?.data?.duplicate) setDup(e.response.data.existing);
      else setError(await errorMessage(e));
    } finally { setProgress(null); }
  };

  const retry = async (f) => {
    setRetrying(true);
    try { setResult((await api.post(`/files/${f.id}/retry`)).data); }
    catch (e) { setError(await errorMessage(e)); }
    finally { setRetrying(false); }
  };

  return (
    <div className="max-w-2xl space-y-5">
      <h1 className="text-xl font-bold">Upload &amp; back up</h1>
      <div className="card space-y-4">
        <label className="grid cursor-pointer place-items-center rounded-lg border-2 border-dashed border-slate-300 px-4 py-10 text-center text-sm text-slate-500 hover:bg-slate-50">
          <input type="file" className="hidden" onChange={(e) => pick(e.target.files[0])} />
          {file ? <span className="font-medium text-slate-800">{file.name} · {fmtBytes(file.size)}</span> : "Click to choose a file"}
        </label>
        {limits && <p className="text-xs text-slate-500">Max file size: {fmtBytes(limits.max_file_size)}</p>}
        {hash && <div className="break-all rounded-lg bg-slate-50 p-3 font-mono text-xs"><span className="text-slate-500">SHA-256 </span>{hash}</div>}
        <div><label className="label">Description (optional)</label><input className="input" maxLength={500} value={desc} onChange={(e) => setDesc(e.target.value)} /></div>
        <button className="btn-primary" disabled={!file || progress !== null || (limits && file.size > limits.max_file_size)} onClick={upload}>
          {progress === null ? "Back up to Backblaze B2 + Supabase" : progress < 100 ? `Uploading ${progress}%` : "Replicating & verifying…"}
        </button>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>

      {dup && (
        <div className="card border-amber-200 bg-amber-50 text-sm">
          <div className="font-semibold text-amber-800">Duplicate detected.</div>
          <p className="mt-1 text-amber-800">Existing backup: <b>{dup.filename}</b> · uploaded {timeAgo(dup.created_at)}. No new upload was made.</p>
        </div>
      )}
      {result && <BackupResult file={result} onRetry={retry} busy={retrying} />}
    </div>
  );
}
