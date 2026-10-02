import { NavLink, Route, Routes } from "react-router-dom";
import { useEffect, useState } from "react";
import { api } from "./api";
import Home from "./pages/Home";
import Knowledge from "./pages/Knowledge";
import Voice from "./pages/Voice";
import Dashboard from "./pages/Dashboard";
import Report from "./pages/Report";

const links = [
  ["/", "Overview"],
  ["/knowledge", "Knowledge Base"],
  ["/voice", "Voice Agent"],
  ["/philippines", "Philippines Bot"],
  ["/indonesia", "Indonesia Bot"],
  ["/dashboard", "Live Intelligence"],
  ["/evaluation", "Evaluation"],
  ["/latency", "Latency"],
];

export default function App() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.health().then(setHealth).catch((err) => setError(err.message));
  }, []);

  return (
    <div className="min-h-screen md:grid md:grid-cols-[240px_1fr]">
      <aside className="border-b border-slate-200 bg-white md:border-b-0 md:border-r">
        <div className="px-5 py-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-tide">Darwix AI</p>
          <h1 className="mt-1 text-lg font-semibold">Voice Intelligence</h1>
        </div>
        <nav className="flex gap-2 overflow-x-auto px-3 pb-4 md:block md:px-3">
          {links.map(([to, label]) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `block whitespace-nowrap rounded-md px-3 py-2 text-sm ${
                  isActive ? "bg-teal-50 font-medium text-tide" : "text-slate-600 hover:bg-slate-50"
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="px-5 py-6 md:px-8">
        {error && (
          <p className="mb-4 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm">
            Backend is not reachable at {error}. Start it with the command in the README.
          </p>
        )}
        {health && (
          <p className="mb-4 rounded-md border border-teal-200 bg-teal-50 px-3 py-2 text-sm text-teal-950">
            Mode: LLM {health.llm_mode}, ASR {health.asr_mode}, TTS {health.tts_mode}, voice {health.voice_mode},
            embeddings {health.embedding_mode}. {health.mock_notice}
          </p>
        )}
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/knowledge" element={<Knowledge />} />
          <Route path="/voice" element={<Voice useCase="health" title="Health insurance qualification" />} />
          <Route path="/philippines" element={<Voice useCase="philippines" title="Philippines bancassurance bot" />} />
          <Route path="/indonesia" element={<Voice useCase="indonesia" title="Indonesia multifinance bot" />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/evaluation" element={<Report kind="evaluation" />} />
          <Route path="/latency" element={<Report kind="latency" />} />
        </Routes>
      </main>
    </div>
  );
}
