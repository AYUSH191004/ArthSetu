import { Routes, Route, Navigate } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { DashboardPage } from "@/pages/DashboardPage";
import { BusinessSearchPage } from "@/pages/BusinessSearchPage";
import { BusinessProfilePage } from "@/pages/BusinessProfilePage";
import { ReviewQueuePage } from "@/pages/ReviewQueuePage";
import { DistrictAnalyticsPage } from "@/pages/DistrictAnalyticsPage";
import { NotFoundPage } from "@/pages/NotFoundPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route path="businesses" element={<BusinessSearchPage />} />
        <Route path="businesses/:ubid" element={<BusinessProfilePage />} />
        <Route path="reviews" element={<ReviewQueuePage />} />
        <Route path="districts" element={<DistrictAnalyticsPage />} />
        <Route path="404" element={<NotFoundPage />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Route>
    </Routes>
  );
}
