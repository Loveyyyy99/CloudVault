import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:5000/api";
const api = axios.create({ baseURL, timeout: 120000 });

export const getSession = () => {
  try { return JSON.parse(localStorage.getItem("cv_session")); } catch { return null; }
};
export const setSession = (s) => localStorage.setItem("cv_session", JSON.stringify(s));
export const clearSession = () => localStorage.removeItem("cv_session");

api.interceptors.request.use((cfg) => {
  const s = getSession();
  if (s?.access_token) cfg.headers.Authorization = `Bearer ${s.access_token}`;
  return cfg;
});

let refreshing = null;
api.interceptors.response.use(
  (r) => r,
  async (err) => {
    const orig = err.config;
    const s = getSession();
    if (err.response?.status === 401 && s?.refresh_token && !orig._retry && !orig.url.includes("/auth/")) {
      orig._retry = true;
      try {
        refreshing = refreshing || axios.post(`${baseURL}/auth/refresh`, { refresh_token: s.refresh_token });
        const { data } = await refreshing;
        refreshing = null;
        setSession(data);
        orig.headers.Authorization = `Bearer ${data.access_token}`;
        return api(orig);
      } catch {
        refreshing = null;
        clearSession();
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);

// Turns any axios error (including blob error bodies) into a friendly string.
export async function errorMessage(e) {
  let data = e.response?.data;
  if (data instanceof Blob) {
    try { data = JSON.parse(await data.text()); } catch { data = null; }
  }
  if (data?.error) return data.error;
  if (e.response?.status === 413) return "That file is too large for the hosting limit. Try a smaller file.";
  if (e.code === "ECONNABORTED") return "The request timed out. Please try again.";
  return "Could not reach the server. Please try again.";
}

export async function downloadFile(file, source) {
  const res = await api.get(`/files/${file.id}/restore`, { params: { source }, responseType: "blob" });
  const url = URL.createObjectURL(res.data);
  const a = document.createElement("a");
  a.href = url;
  a.download = file.filename;
  a.click();
  URL.revokeObjectURL(url);
  let attempts = [];
  try { attempts = JSON.parse(res.headers["x-restore-attempts"] || "[]"); } catch { /* ignore */ }
  return { source: res.headers["x-restore-source"], attempts };
}

export default api;
