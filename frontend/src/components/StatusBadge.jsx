const STYLES = {
  VERIFIED: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  HEALTHY: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  RESTORED: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  PARTIAL: "bg-amber-50 text-amber-700 ring-amber-200",
  UPLOADING: "bg-blue-50 text-blue-700 ring-blue-200",
  RESTORING: "bg-blue-50 text-blue-700 ring-blue-200",
  PENDING: "bg-slate-100 text-slate-600 ring-slate-200",
  FAILED: "bg-red-50 text-red-700 ring-red-200",
  UNAVAILABLE: "bg-red-50 text-red-700 ring-red-200",
  SIMULATED_FAILURE: "bg-red-50 text-red-700 ring-red-200",
};

export default function StatusBadge({ status }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${STYLES[status] || STYLES.PENDING}`}>
      {(status || "").replace("_", " ")}
    </span>
  );
}

// ✓ / ✗ / … cell for one provider inside a file row
export function ProviderMark({ backup }) {
  const s = backup?.status;
  const map = { VERIFIED: ["✓", "text-emerald-600"], FAILED: ["✗", "text-red-600"], UPLOADING: ["…", "text-blue-600"] };
  const [glyph, cls] = map[s] || ["–", "text-slate-400"];
  return <span title={backup?.error_message || s || "No copy"} className={`font-mono text-base font-bold ${cls}`}>{glyph}</span>;
}
