import { useEffect, useState } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { api } from "./api/client";
import { Layout } from "./components/Layout";
import { ErrorState, LoadingState } from "./components/StateViews";
import { CockpitPage } from "./pages/CockpitPage";
import { PositionsPage } from "./pages/PositionsPage";
import { ReplayPage } from "./pages/ReplayPage";
import { RiskPage } from "./pages/RiskPage";
import { SettingsPage } from "./pages/SettingsPage";
import "./index.css";

export function App() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [demoMode, setDemoMode] = useState(true);
  const [paperMode, setPaperMode] = useState(true);

  useEffect(() => {
    void (async () => {
      try {
        const [health, settings] = await Promise.all([api.health(), api.settings()]);
        setDemoMode(Boolean(health.demo_mode ?? settings.demo_mode));
        setPaperMode(Boolean(settings.paper_mode));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Backend unavailable");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div className="boot-screen">
        <LoadingState title="FlightDeck Alpha" message="Connecting to backend…" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="boot-screen">
        <ErrorState
          title="Backend unavailable"
          message={`${error}. Start the FastAPI server on port 8000, then refresh.`}
        />
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout demoMode={demoMode} paperMode={paperMode} />}>
          <Route index element={<CockpitPage />} />
          <Route path="replay" element={<ReplayPage />} />
          <Route path="positions" element={<PositionsPage />} />
          <Route path="risk" element={<RiskPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
