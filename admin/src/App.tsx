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
import SupportContactsPage from "./pages/SupportContactsPage";
import ToolsPage from "./pages/ToolsPage";
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
import PageGate from "./components/PageGate";

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
        <Route path="/" element={<PageGate page="dashboard"><DashboardPage /></PageGate>} />
        <Route path="/content" element={<PageGate page="content"><ContentPage /></PageGate>} />
        <Route path="/content/:moduleId" element={<PageGate page="content"><ModuleDetailPage /></PageGate>} />
        <Route path="/content/:moduleId/quiz" element={<PageGate page="content"><QuizEditorPage /></PageGate>} />
        <Route path="/videos" element={<PageGate page="videos"><VideosPage /></PageGate>} />
        <Route path="/references" element={<PageGate page="references"><ReferencesPage /></PageGate>} />
        <Route path="/answers" element={<PageGate page="answers"><AnswersPage /></PageGate>} />
        <Route path="/consent" element={<PageGate page="consent"><ConsentPage /></PageGate>} />
        <Route path="/learning" element={<PageGate page="learning"><LearningReviewPage /></PageGate>} />
        <Route path="/general-test" element={<PageGate page="general-test"><GeneralTestPage /></PageGate>} />
        <Route path="/releases" element={<PageGate page="releases"><ReleasesPage /></PageGate>} />
        <Route path="/languages" element={<PageGate page="languages"><LanguagesPage /></PageGate>} />
        <Route path="/app-text" element={<PageGate page="app-text"><AppTextPage /></PageGate>} />
        <Route path="/support-contacts" element={<PageGate page="support-contacts"><SupportContactsPage /></PageGate>} />
        <Route path="/tools" element={<PageGate page="tools"><ToolsPage /></PageGate>} />
        <Route path="/analytics" element={<PageGate page="analytics"><AnalyticsPage /></PageGate>} />
        <Route path="/audit" element={<PageGate page="audit"><AuditLogPage /></PageGate>} />
        <Route path="/users" element={<PageGate page="users"><UsersPage /></PageGate>} />
        <Route path="/areas" element={<PageGate page="areas"><BoundariesPage /></PageGate>} />
        <Route path="/sessions" element={<PageGate page="sessions"><SessionsPage /></PageGate>} />
        <Route path="/reports" element={<PageGate page="reports"><ReportsPage /></PageGate>} />
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
