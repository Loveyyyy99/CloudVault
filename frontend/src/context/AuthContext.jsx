import { createContext, useContext, useState } from "react";
import api, { clearSession, getSession, setSession } from "../services/api.js";

const Ctx = createContext(null);
export const useAuth = () => useContext(Ctx);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => getSession()?.user || null);

  const finish = (data) => {
    if (data.access_token) { setSession(data); setUser(data.user); }
    return data;
  };
  const login = async (email, password) => finish((await api.post("/auth/login", { email, password })).data);
  const register = async (email, password) => finish((await api.post("/auth/register", { email, password })).data);
  const logout = () => { clearSession(); setUser(null); };

  return <Ctx.Provider value={{ user, login, register, logout }}>{children}</Ctx.Provider>;
}
