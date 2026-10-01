import { Link } from "react-router-dom";

const FEATURES = [
  ["Multi-Cloud Backup", "Backup files across Backblaze B2 and Supabase Storage."],
  ["Integrity Verification", "SHA-256 verification ensures that uploaded copies are not corrupted."],
  ["Disaster Recovery", "Restore your files from another cloud if one provider becomes unavailable."],
  ["Automated Backups", "Scheduled backup jobs automatically verify and replicate files."],
  ["Cloud Health", "Monitor the availability of Backblaze B2 and Supabase storage."],
];
const FLOW = ["React Frontend", "Flask API", "Backblaze B2 + Supabase Storage", "SHA-256 Verification", "Supabase Postgres", "GitHub Actions"];

export default function Landing() {
  return (
    <div className="min-h-screen bg-white">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <div className="flex items-center gap-2 font-semibold">
          <span className="grid h-7 w-7 place-items-center rounded-md bg-gradient-to-br from-b2 to-supabase text-sm font-bold text-white">C</span>
          CloudVault
        </div>
        <div className="flex gap-2">
          <Link to="/login" className="btn-ghost">Sign in</Link>
          <Link to="/register" className="btn-primary">Get Started</Link>
        </div>
      </nav>

      <section className="bg-ink px-6 py-24 text-center text-white">
        <h1 className="mx-auto max-w-3xl text-4xl font-bold leading-tight tracking-tight md:text-5xl">
          One Backup. Multiple Clouds. Zero Single Points of Failure.
        </h1>
        <p className="mx-auto mt-5 max-w-xl text-slate-300">
          Securely backup, verify and restore your files across multiple cloud providers.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link to="/register" className="btn bg-white text-slate-900 hover:bg-slate-200">Get Started</Link>
          <a href="#architecture" className="btn border border-white/30 text-white hover:bg-white/10">View Architecture</a>
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-4 px-6 py-16 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map(([t, d]) => (
          <div key={t} className="card">
            <h3 className="font-semibold">{t}</h3>
            <p className="mt-2 text-sm text-slate-600">{d}</p>
          </div>
        ))}
      </section>

      <section id="architecture" className="border-t border-slate-200 bg-slate-50 px-6 py-16">
        <h2 className="mb-8 text-center text-2xl font-bold tracking-tight">Architecture</h2>
        <div className="mx-auto flex max-w-4xl flex-wrap items-center justify-center gap-3">
          {FLOW.map((s, i) => (
            <div key={s} className="flex items-center gap-3">
              <div className="rounded-lg border border-slate-300 bg-white px-4 py-2 font-mono text-xs">{s}</div>
              {i < FLOW.length - 1 && <span className="text-slate-400">→</span>}
            </div>
          ))}
        </div>
      </section>
      <footer className="py-8 text-center text-xs text-slate-400">CloudVault — free-tier multi-cloud backup project</footer>
    </div>
  );
}
