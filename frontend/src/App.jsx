import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import { useAuth } from "./context/AuthContext";
import Approvals from "./pages/Approvals";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import MyExpenses from "./pages/MyExpenses";
import SubmitExpense from "./pages/SubmitExpense";
import { homePath } from "./utils";

function Home() {
  const { user } = useAuth();
  return <Navigate to={user ? homePath(user.role) : "/login"} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/submit" element={<SubmitExpense />} />
          <Route path="/my-expenses" element={<MyExpenses />} />

          <Route element={<ProtectedRoute roles={["manager", "admin"]} />}>
            <Route path="/approvals" element={<Approvals />} />
          </Route>

          <Route element={<ProtectedRoute roles={["admin"]} />}>
            <Route path="/dashboard" element={<Dashboard />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Home />} />
    </Routes>
  );
}
