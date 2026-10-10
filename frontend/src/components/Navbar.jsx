import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const LINKS = [
  { to: "/dashboard", label: "Dashboard", roles: ["admin"] },
  { to: "/approvals", label: "Approvals", roles: ["manager", "admin"] },
  { to: "/submit", label: "Submit Expense", roles: ["employee", "manager", "admin"] },
  { to: "/my-expenses", label: "My Expenses", roles: ["employee", "manager", "admin"] },
];

const ROLE_STYLES = {
  employee: "bg-sky-100 text-sky-800",
  manager: "bg-violet-100 text-violet-800",
  admin: "bg-amber-100 text-amber-800",
};

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-500 text-lg font-bold text-white">
            S
          </span>
          <span className="text-lg font-bold text-slate-900">SpendFlow</span>
        </div>

        <nav className="flex flex-wrap items-center gap-1" aria-label="Main">
          {LINKS.filter((l) => l.roles.includes(user.role)).map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              className={({ isActive }) =>
                `rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                  isActive
                    ? "bg-brand-50 text-brand-700"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <div className="text-right leading-tight">
            <p className="text-sm font-semibold text-slate-800">{user.name}</p>
            <span
              className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold capitalize ${
                ROLE_STYLES[user.role] || "bg-slate-100 text-slate-700"
              }`}
            >
              {user.role}
            </span>
          </div>
          <button type="button" onClick={handleLogout} className="btn btn-ghost">
            Log out
          </button>
        </div>
      </div>
    </header>
  );
}
