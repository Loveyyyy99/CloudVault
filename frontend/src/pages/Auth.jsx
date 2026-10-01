import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { errorMessage } from "../services/api.js";

export default function Auth({ mode }) {
  const { user, login, register } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState(null);
  const [busy, setBusy] = useState(false);
  const isLogin = mode === "login";
  if (user) return <Navigate to="/dashboard" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setMsg(null);
    try {
      const data = await (isLogin ? login : register)(email, password);
      if (data.access_token) nav("/dashboard");
      else setMsg({ ok: true, text: data.message });
    } catch (err) {
      setMsg({ ok: false, text: await errorMessage(err) });
    } finally { setBusy(false); }
  };

  return (
    <div className="grid min-h-screen place-items-center bg-slate-50 px-4">
      <form onSubmit={submit} className="card w-full max-w-sm space-y-4">
        <Link to="/" className="text-sm font-semibold text-slate-500">← CloudVault</Link>
        <h1 className="text-xl font-bold">{isLogin ? "Sign in" : "Create your account"}</h1>
        <div><label className="label">Email</label><input className="input" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} /></div>
        <div><label className="label">Password</label><input className="input" type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} /></div>
        {msg && <p className={`text-sm ${msg.ok ? "text-emerald-700" : "text-red-600"}`}>{msg.text}</p>}
        <button className="btn-primary w-full" disabled={busy}>{busy ? "Please wait…" : isLogin ? "Sign in" : "Sign up"}</button>
        <p className="text-center text-sm text-slate-500">
          {isLogin ? <>New here? <Link className="font-medium text-slate-900" to="/register">Create an account</Link></> : <>Have an account? <Link className="font-medium text-slate-900" to="/login">Sign in</Link></>}
        </p>
      </form>
    </div>
  );
}
