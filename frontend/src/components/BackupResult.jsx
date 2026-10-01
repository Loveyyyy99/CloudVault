import { PROVIDER_LABEL } from "../utils/format.js";
import StatusBadge from "./StatusBadge.jsx";

const OVERALL = { VERIFIED: "✓ BACKUP COMPLETE", PARTIAL: "⚠ PARTIAL BACKUP", FAILED: "✗ BACKUP FAILED" };

export default function BackupResult({ file, onRetry, busy }) {
  const failed = (file.backups || []).filter((b) => b.status !== "VERIFIED");
  const healthy = (file.backups || []).filter((b) => b.status === "VERIFIED");
  return (
    <div className="card space-y-4">
      <div>
        <div className="font-semibold">{file.filename}</div>
        <div className="mt-1 break-all font-mono text-xs text-slate-500">SHA-256: {file.sha256}</div>
      </div>
      {(file.backups || []).map((b) => (
        <div key={b.provider} className="rounded-lg bg-slate-50 p-3 text-sm">
          <div className="mb-1 font-semibold">{PROVIDER_LABEL[b.provider]}</div>
          <div className={b.status === "VERIFIED" || b.uploaded_at ? "text-emerald-700" : "text-slate-400"}>
            {b.status === "VERIFIED" ? "✓ Uploaded" : b.status === "FAILED" ? "✗ Upload failed" : "… Pending"}
          </div>
          <div className={b.status === "VERIFIED" ? "text-emerald-700" : "text-slate-400"}>
            {b.status === "VERIFIED" ? "✓ Verified (hash matches)" : "– Not verified"}
          </div>
          {b.error_message && <div className="mt-1 text-xs text-red-600">{b.error_message}</div>}
        </div>
      ))}
      <div className="flex items-center justify-between">
        <div className="text-sm font-semibold">Overall status <StatusBadge status={file.status} /> <span className="ml-2">{OVERALL[file.status]}</span></div>
      </div>
      {failed.length > 0 && healthy.length > 0 && (
        <p className="text-sm text-slate-600">
          {failed.map((b) => PROVIDER_LABEL[b.provider]).join(", ")} backup failed. Your {healthy.map((b) => PROVIDER_LABEL[b.provider]).join(", ")} backup is still available.
        </p>
      )}
      {failed.length > 0 && onRetry && (
        <button className="btn-primary" disabled={busy} onClick={() => onRetry(file)}>
          {busy ? "Retrying…" : `Retry ${failed.map((b) => PROVIDER_LABEL[b.provider]).join(" + ")} backup`}
        </button>
      )}
    </div>
  );
}
