import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../services/auth";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/content", label: "Content" },
  { to: "/releases", label: "Releases" },
  { to: "/languages", label: "Languages" },
  { to: "/analytics", label: "Analytics" },
];

export default function AdminLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen flex bg-gray-50">
      <aside className="w-56 bg-gray-900 text-gray-100 p-4 flex flex-col">
        <div className="text-lg font-semibold mb-6">SARMAAN e-Playbook</div>
        <nav className="space-y-1 flex-1">
          {navItems.map((item) => (
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
