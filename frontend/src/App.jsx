import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import { useAuth } from "./context/AuthContext.jsx";
import Account from "./pages/Account.jsx";
import Auth from "./pages/Auth.jsx";
import Backups from "./pages/Backups.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import DisasterRecovery from "./pages/DisasterRecovery.jsx";
import Landing from "./pages/Landing.jsx";
import Upload from "./pages/Upload.jsx";

function Protected({ children }) {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Auth mode="login" />} />
      <Route path="/register" element={<Auth mode="register" />} />
      <Route element={<Protected><Layout /></Protected>}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/backups" element={<Backups />} />
        <Route path="/recovery" element={<DisasterRecovery />} />
        <Route path="/account" element={<Account />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
