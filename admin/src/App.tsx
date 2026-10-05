import { Routes, Route, Link } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import ContentPage from "./pages/ContentPage";
import ModuleDetailPage from "./pages/ModuleDetailPage";
import ReleasesPage from "./pages/ReleasesPage";
import LanguagesPage from "./pages/LanguagesPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import LoginPage from "./pages/LoginPage";
import AdminLayout from "./layouts/AdminLayout";
import ProtectedRoute from "./components/ProtectedRoute";

/**
 * Phase 5 scope: real dashboard/content/module-detail/release/language
 * screens, all behind authentication. AnalyticsPage stays a Phase-2 stub —
 * it's not in the master prompt's explicit Phase 5 admin list (dashboard,
 * modules, content, languages, releases); a dedicated deep-dive analytics
 * screen beyond the dashboard's charts is future work, not required here.
 */
export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <AdminLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route path="/content" element={<ContentPage />} />
        <Route path="/content/:moduleId" element={<ModuleDetailPage />} />
        <Route path="/releases" element={<ReleasesPage />} />
        <Route path="/languages" element={<LanguagesPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route
          path="*"
          element={
            <div className="p-6">
              <p>Page not found.</p>
              <Link to="/" className="text-blue-600 underline">
                Back to dashboard
              </Link>
            </div>
          }
        />
      </Route>
    </Routes>
  );
}
