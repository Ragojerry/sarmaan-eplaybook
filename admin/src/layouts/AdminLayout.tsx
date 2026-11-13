import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../services/auth";
import PartnerLogos from "../components/PartnerLogos";

// `roles` mirrors the backend (the server is what actually enforces access;
// hiding a link is only a courtesy). SUPER_ADMIN always sees everything.
const navItems: { to: string; label: string; roles?: string[] }[] = [
  { to: "/", label: "Dashboard" },
  { to: "/content", label: "Content" },
  { to: "/videos", label: "Videos" },
  { to: "/tools", label: "Tools repository", roles: ["CONTENT_ADMIN", "PROGRAM_REVIEWER", "LOCALISATION_REVIEWER", "TECHNICAL_REVIEWER", "SUPERVISOR", "READ_ONLY"] },
  { to: "/learning", label: "Roles & tests", roles: ["CONTENT_ADMIN", "PROGRAM_REVIEWER", "LOCALISATION_REVIEWER", "TECHNICAL_REVIEWER", "SUPERVISOR", "READ_ONLY"] },
  { to: "/general-test", label: "General test", roles: ["CONTENT_ADMIN", "PROGRAM_REVIEWER", "LOCALISATION_REVIEWER", "TECHNICAL_REVIEWER", "SUPERVISOR", "READ_ONLY"] },
  { to: "/answers", label: "Curated answers", roles: ["CONTENT_ADMIN", "PROGRAM_REVIEWER", "LOCALISATION_REVIEWER", "TECHNICAL_REVIEWER"] },
  { to: "/references", label: "Reference library", roles: ["CONTENT_ADMIN", "PROGRAM_REVIEWER", "LOCALISATION_REVIEWER", "TECHNICAL_REVIEWER"] },
  { to: "/releases", label: "Releases" },
  { to: "/languages", label: "Languages" },
  { to: "/app-text", label: "App interface text", roles: ["CONTENT_ADMIN", "PROGRAM_REVIEWER", "LOCALISATION_REVIEWER", "TECHNICAL_REVIEWER"] },
  { to: "/consent", label: "Consent text", roles: ["CONTENT_ADMIN", "LOCALISATION_REVIEWER"] },
  { to: "/support-contacts", label: "Support contacts", roles: ["CONTENT_ADMIN", "PROGRAM_REVIEWER", "LOCALISATION_REVIEWER", "TECHNICAL_REVIEWER", "SUPERVISOR", "READ_ONLY"] },
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
      {/* Brand: IHS Teal sheen navigation (deep teal at the top) with white text (index.css). */}
      <aside className="admin-sidebar w-56 text-white p-4 flex flex-col">
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
                  isActive ? "bg-white text-brand-text-strong font-semibold" : "text-brand-on-primary-muted hover:bg-white/15 hover:text-white"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        {user && (
          <div className="border-t border-white/25 pt-3 mt-3">
            <p className="text-sm text-white">
              {user.first_name} {user.last_name}
            </p>
            <p className="text-xs text-brand-on-primary-muted mb-2">{user.role.replace("_", " ")}</p>
            <button onClick={() => logout()} className="text-xs text-brand-on-primary-muted hover:text-white underline">
              Sign out
            </button>
          </div>
        )}
      </aside>
      <main className="flex-1 flex flex-col min-w-0">
        {/* Partner logos on white: order and positions from src/brand/logos.json. */}
        <header className="border-b border-gray-200">
          <PartnerLogos placement="adminHeader" />
        </header>
        <div className="flex-1">
          <Outlet />
        </div>
        <footer className="border-t border-gray-200">
          <PartnerLogos placement="adminFooter" />
        </footer>
      </main>
    </div>
  );
}
