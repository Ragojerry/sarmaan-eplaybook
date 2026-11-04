import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../services/auth";

// `roles` mirrors the backend (the server is what actually enforces access;
// hiding a link is only a courtesy). SUPER_ADMIN always sees everything.
const navItems: { to: string; label: string; roles?: string[] }[] = [
  { to: "/", label: "Dashboard" },
  { to: "/content", label: "Content" },
  { to: "/videos", label: "Videos" },
  { to: "/references", label: "Reference library", roles: ["CONTENT_ADMIN", "PROGRAM_REVIEWER", "LOCALISATION_REVIEWER", "TECHNICAL_REVIEWER"] },
  { to: "/releases", label: "Releases" },
  { to: "/languages", label: "Languages" },
  { to: "/analytics", label: "Analytics", roles: ["CONTENT_ADMIN", "PROGRAM_REVIEWER", "LOCALISATION_REVIEWER", "TECHNICAL_REVIEWER", "SUPERVISOR", "READ_ONLY"] },
  { to: "/reports", label: "Reports", roles: ["CONTENT_ADMIN", "PROGRAM_REVIEWER", "LOCALISATION_REVIEWER", "TECHNICAL_REVIEWER", "SUPERVISOR", "READ_ONLY"] },
  { to: "/audit", label: "Audit log", roles: ["CONTENT_ADMIN", "TECHNICAL_REVIEWER"] },
  { to: "/users", label: "Users", roles: [] }, // SUPER_ADMIN only
  { to: "/sessions", label: "Sessions", roles: [] }, // SUPER_ADMIN only
  { to: "/areas", label: "Areas", roles: [] }, // SUPER_ADMIN only
];

export default function AdminLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen flex bg-gray-50">
      <aside className="w-56 bg-gray-900 text-gray-100 p-4 flex flex-col">
        <div className="text-lg font-semibold mb-6">SARMAAN e-Playbook</div>
        <nav className="space-y-1 flex-1">
          {navItems
            .filter((item) => !item.roles || user?.role === "SUPER_ADMIN" || (user && item.roles.includes(user.role)))
            .map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `block rounded px-3 py-2 text-sm ${
                  isActive ? "bg-gray-700 text-white" : "text-gray-300 hover:bg-gray-800"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        {user && (
          <div className="border-t border-gray-800 pt-3 mt-3">
            <p className="text-sm text-gray-200">
              {user.first_name} {user.last_name}
            </p>
            <p className="text-xs text-gray-400 mb-2">{user.role.replace("_", " ")}</p>
            <button onClick={() => logout()} className="text-xs text-gray-400 hover:text-white underline">
              Sign out
            </button>
          </div>
        )}
      </aside>
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}
