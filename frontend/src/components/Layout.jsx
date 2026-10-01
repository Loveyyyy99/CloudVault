import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

const NAV = [
  ["/dashboard", "Dashboard"],
  ["/upload", "Upload"],
  ["/backups", "Backups"],
  ["/recovery", "Disaster Recovery"],
  ["/account", "Account"],
];

export default function Layout() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const link = ({ isActive }) =>
    `block rounded-lg px-3 py-2 text-sm font-medium ${isActive ? "bg-white/10 text-white" : "text-slate-400 hover:text-white"}`;

  return (
    <div className="min-h-screen md:flex">
      <aside className="bg-ink px-4 py-5 md:fixed md:inset-y-0 md:w-56">
        <div className="mb-6 flex items-center gap-2 px-2 text-white">
          <span className="grid h-7 w-7 place-items-center rounded-md bg-gradient-to-br from-b2 to-supabase text-sm font-bold">C</span>
          <span className="font-semibold tracking-tight">CloudVault</span>
        </div>
        <nav className="flex gap-1 overflow-x-auto md:block md:space-y-1">
          {NAV.map(([to, label]) => <NavLink key={to} to={to} className={link}>{label}</NavLink>)}
        </nav>
      </aside>
      <div className="flex-1 md:ml-56">
        <header className="flex items-center justify-end gap-4 border-b border-slate-200 bg-white px-6 py-3 text-sm">
          <span className="text-slate-500">{user?.email}</span>
          <button className="btn-ghost" onClick={() => { logout(); nav("/"); }}>Sign out</button>
        </header>
        <main className="mx-auto max-w-6xl p-6"><Outlet /></main>
      </div>
    </div>
  );
}
