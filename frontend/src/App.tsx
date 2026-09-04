import { Routes, Route, Navigate } from "react-router-dom";
import { RequireAuth } from "@/components/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { BusinessSearchPage } from "@/pages/BusinessSearchPage";
import { BusinessProfilePage } from "@/pages/BusinessProfilePage";
import { ReviewQueuePage } from "@/pages/ReviewQueuePage";
import { DistrictAnalyticsPage } from "@/pages/DistrictAnalyticsPage";
import { IngestionPage } from "@/pages/IngestionPage";
import { UsersPage } from "@/pages/UsersPage";
import { NotFoundPage } from "@/pages/NotFoundPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="businesses" element={<BusinessSearchPage />} />
        <Route path="businesses/:ubid" element={<BusinessProfilePage />} />
        <Route path="reviews" element={<ReviewQueuePage />} />
        <Route path="districts" element={<DistrictAnalyticsPage />} />
        <Route
          path="ingest"
          element={
            <RequireAuth role="admin">
              <IngestionPage />
            </RequireAuth>
          }
        />
        <Route
          path="users"
          element={
            <RequireAuth role="admin">
              <UsersPage />
            </RequireAuth>
          }
        />
        <Route path="404" element={<NotFoundPage />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Route>
    </Routes>
  );
}
