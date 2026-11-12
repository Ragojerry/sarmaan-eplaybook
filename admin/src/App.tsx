import { Routes, Route, Link } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import ContentPage from "./pages/ContentPage";
import ModuleDetailPage from "./pages/ModuleDetailPage";
import ReleasesPage from "./pages/ReleasesPage";
import LanguagesPage from "./pages/LanguagesPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import AuditLogPage from "./pages/AuditLogPage";
import VideosPage from "./pages/VideosPage";
import ReferencesPage from "./pages/ReferencesPage";
import AnswersPage from "./pages/AnswersPage";
import ConsentPage from "./pages/ConsentPage";
import AppTextPage from "./pages/AppTextPage";
import LearningReviewPage from "./pages/LearningReviewPage";
import UsersPage from "./pages/UsersPage";
import BoundariesPage from "./pages/BoundariesPage";
import ReportsPage from "./pages/ReportsPage";
import SessionsPage from "./pages/SessionsPage";
import QuizEditorPage from "./pages/QuizEditorPage";
import GeneralTestPage from "./pages/GeneralTestPage";
import LoginPage from "./pages/LoginPage";
import AdminLayout from "./layouts/AdminLayout";
import ProtectedRoute from "./components/ProtectedRoute";

/** Dashboard, content, module detail, releases, languages, analytics (Phase 13) and audit log (Phase 13), all behind authentication. */
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
        <Route path="/content/:moduleId/quiz" element={<QuizEditorPage />} />
        <Route path="/videos" element={<VideosPage />} />
        <Route path="/references" element={<ReferencesPage />} />
        <Route path="/answers" element={<AnswersPage />} />
        <Route path="/consent" element={<ConsentPage />} />
        <Route path="/learning" element={<LearningReviewPage />} />
        <Route path="/general-test" element={<GeneralTestPage />} />
        <Route path="/releases" element={<ReleasesPage />} />
        <Route path="/languages" element={<LanguagesPage />} />
        <Route path="/app-text" element={<AppTextPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/audit" element={<AuditLogPage />} />
        <Route path="/users" element={<UsersPage />} />
        <Route path="/areas" element={<BoundariesPage />} />
        <Route path="/sessions" element={<SessionsPage />} />
        <Route path="/reports" element={<ReportsPage />} />
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
