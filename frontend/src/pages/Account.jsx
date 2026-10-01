import { useAuth } from "../context/AuthContext.jsx";

export default function Account() {
  const { user } = useAuth();
  return (
    <div className="max-w-md space-y-4">
      <h1 className="text-xl font-bold">Account</h1>
      <div className="card space-y-3 text-sm">
        <div><div className="label">Email</div>{user?.email}</div>
        <div><div className="label">User ID</div><span className="font-mono text-xs">{user?.id}</span></div>
        <p className="text-slate-500">You can only see and restore your own files. Passwords are managed by Supabase Auth and never stored by CloudVault.</p>
      </div>
    </div>
  );
}
