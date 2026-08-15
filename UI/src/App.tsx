import { NavLink, Route, Routes } from "react-router-dom";
import { AnalysisRun } from "./routes/AnalysisRun";
import { History } from "./routes/History";
import { ProfileSetup } from "./routes/ProfileSetup";
import { Results } from "./routes/Results";

export function App() {
  return (
    <>
      <nav className="nav-bar">
        <NavLink to="/" end>
          Profile
        </NavLink>
        <NavLink to="/history">History</NavLink>
      </nav>
      <Routes>
        <Route path="/" element={<ProfileSetup />} />
        <Route path="/analysis/:sessionId" element={<AnalysisRun />} />
        <Route path="/results/:sessionId" element={<Results />} />
        <Route path="/history" element={<History />} />
      </Routes>
    </>
  );
}
