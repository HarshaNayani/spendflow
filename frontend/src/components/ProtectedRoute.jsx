import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { homePath } from "../utils";

// Not logged in -> login page. Wrong role -> that role's home page.
export default function ProtectedRoute({ roles }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) {
    return <Navigate to={homePath(user.role)} replace />;
  }
  return <Outlet />;
}
