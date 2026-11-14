import { Navigate } from "react-router-dom";
import { useAuth } from "../services/auth";
import { navItems } from "../layouts/AdminLayout";

/** Shows a page only to accounts that include it (the server checks too).
 *  Without the dashboard, the home address opens the account's first page. */
export default function PageGate({ page, children }: { page: string; children: React.ReactNode }) {
  const { user } = useAuth();
  const pages = user?.pages ?? [];
  if (pages.includes(page)) return <>{children}</>;
  if (page === "dashboard") {
    const first = navItems.find((item) => pages.includes(item.page));
    if (first) return <Navigate to={first.to} replace />;
  }
  return (
    <div className="p-6 text-sm text-gray-600">
      {pages.length
        ? "Your account does not include this page. Ask a super admin to add it."
        : "Your account has no portal pages yet. Ask a super admin to add some."}
    </div>
  );
}
