import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { CockpitPage } from "./pages/CockpitPage";
import { PositionsPage } from "./pages/PositionsPage";
import { ReplayPage } from "./pages/ReplayPage";
import { RiskPage } from "./pages/RiskPage";
import { SettingsPage } from "./pages/SettingsPage";

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<CockpitPage />} />
          <Route path="/positions" element={<PositionsPage />} />
          <Route path="/replay" element={<ReplayPage />} />
          <Route path="/risk" element={<RiskPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
};
