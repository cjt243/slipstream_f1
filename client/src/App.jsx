import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import AppLayout from "./components/layout/AppLayout";
import LoginPage from "./pages/LoginPage";
import VerifyPage from "./pages/VerifyPage";
import TeamPage from "./pages/TeamPage";
import RacesPage from "./pages/RacesPage";
import RaceDetailPage from "./pages/RaceDetailPage";
import LeaderboardPage from "./pages/LeaderboardPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/auth/verify" element={<VerifyPage />} />

          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/team" element={<TeamPage />} />
              <Route path="/races" element={<RacesPage />} />
              <Route path="/race/:id" element={<RaceDetailPage />} />
              <Route path="/leaderboard" element={<LeaderboardPage />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/team" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
