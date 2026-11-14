import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../services/auth";
import PartnerLogos from "../components/PartnerLogos";
import BrandMark from "../components/BrandMark";

// `page` is a key from the server (backend/app/auth/pages.py), which decides
// who sees what: the role, narrowed by pages a super admin ticked. The server
// enforces it; hiding a link is only a courtesy.
export const navItems: { to: string; label: string; page: string }[] = [
  { to: "/", label: "Dashboard", page: "dashboard" },
  { to: "/content", label: "Content", page: "content" },
  { to: "/videos", label: "Videos", page: "videos" },
  { to: "/tools", label: "Tools repository", page: "tools" },
  { to: "/learning", label: "Roles & tests", page: "learning" },
  { to: "/general-test", label: "General test", page: "general-test" },
  { to: "/answers", label: "Curated answers", page: "answers" },
  { to: "/references", label: "Reference library", page: "references" },
  { to: "/releases", label: "Releases", page: "releases" },
  { to: "/languages", label: "Languages", page: "languages" },
  { to: "/app-text", label: "App interface text", page: "app-text" },
  { to: "/consent", label: "Consent text", page: "consent" },
  { to: "/support-contacts", label: "Support contacts", page: "support-contacts" },
  { to: "/analytics", label: "Analytics", page: "analytics" },
  { to: "/reports", label: "Reports", page: "reports" },
  { to: "/audit", label: "Audit log", page: "audit" },
  { to: "/users", label: "Users", page: "users" },
  { to: "/sessions", label: "Sessions", page: "sessions" },
  { to: "/areas", label: "Areas", page: "areas" },
];

export default function AdminLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen flex bg-gray-50">
      {/* Brand: IHS Teal sheen navigation (deep teal at the top) with white text (index.css). */}
      <aside className="admin-sidebar w-56 text-white p-4 flex flex-col">
        <BrandMark short className="text-base mb-6" size={36} />
        <nav className="space-y-1 flex-1">
          {navItems
            .filter((item) => user?.pages?.includes(item.page))
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
