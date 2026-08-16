import { Link, NavLink, Route, Routes } from "react-router-dom";
import { AnalysisRun } from "./routes/AnalysisRun";
import { History } from "./routes/History";
import { ProfileSetup } from "./routes/ProfileSetup";
import { Results } from "./routes/Results";

const navLinkClass = (isActive: boolean) =>
  `flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-colors ${
    isActive
      ? "bg-secondary-container/50 text-on-secondary-container font-bold border border-secondary/20"
      : "text-on-surface-variant hover:bg-surface-container-high"
  }`;

export function App() {
  return (
    <>
      <nav className="hidden md:flex flex-col h-screen w-64 fixed left-0 top-0 bg-surface-container-low border-r border-outline-variant/30 p-4 gap-2 z-20">
        <div className="mb-8 px-2 flex items-center gap-3">
          <div
            className="agent-seal w-10 h-10 font-headline font-semibold text-base"
            style={{ ["--seal" as string]: "var(--color-primary)" }}
          >
            FA
          </div>
          <div>
            <h1 className="font-headline font-semibold text-lg text-on-surface leading-tight">
              FinAgents India
            </h1>
            <p className="text-xs text-on-surface-variant tracking-wide">AI Investment Intelligence</p>
          </div>
        </div>
        <Link
          to="/"
          className="w-full bg-primary text-on-primary rounded-md py-3 px-4 font-semibold text-sm mb-6 hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
        >
          <span className="material-symbols-outlined text-lg">add</span>
          New Analysis
        </Link>
        <div className="flex flex-col gap-1">
          <NavLink to="/" end className={({ isActive }) => navLinkClass(isActive)}>
            <span className="material-symbols-outlined">search_insights</span>
            Profile
          </NavLink>
          <NavLink to="/history" className={({ isActive }) => navLinkClass(isActive)}>
            <span className="material-symbols-outlined">description</span>
            History
          </NavLink>
        </div>
      </nav>
      <main className="md:ml-64 min-h-screen p-4 sm:p-6 md:p-8 lg:p-12">
        {/* max-width + centering lives on this inner wrapper, not on <main>
            itself -- putting both mx-auto and ml-64 on the same element makes
            them fight over margin-left, throwing the centering off to one
            side instead of balancing the space after the sidebar. */}
        <div className="max-w-[1600px] mx-auto">
          <Routes>
            <Route path="/" element={<ProfileSetup />} />
            <Route path="/analysis/:sessionId" element={<AnalysisRun />} />
            <Route path="/results/:sessionId" element={<Results />} />
            <Route path="/history" element={<History />} />
          </Routes>
        </div>
      </main>
    </>
  );
}
