import { useEffect, useState } from "react";
import { api } from "../api";

export default function Report({ kind }) {
  const [payload, setPayload] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const loader = kind === "latency" ? api.latency : api.evaluation;
    loader().then(setPayload).catch((err) => setError(err.message));
  }, [kind]);

  return (
    <section>
      <h2 className="text-2xl font-semibold">{kind === "latency" ? "Measured latency" : "Retrieval evaluation"}</h2>
      <p className="mt-2 text-sm text-slate-600">
        These numbers come from the backend files written by the evaluation run. Missing external ASR or LLM time is
        reported as NOT MEASURED.
      </p>
      {error && <p className="mt-3 text-sm text-red-700">{error}</p>}
      {kind === "evaluation" && payload?.results && (
        <div className="mt-4 overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="px-3 py-2">Type</th>
                <th className="px-3 py-2">Verdict</th>
                <th className="px-3 py-2">Score</th>
                <th className="px-3 py-2">Source</th>
              </tr>
            </thead>
            <tbody>
              {payload.results.map((row) => (
                <tr key={row.question_type} className="border-t border-slate-100">
                  <td className="px-3 py-2">{row.question_type}</td>
                  <td className="px-3 py-2">{row.verdict}</td>
                  <td className="px-3 py-2">{row.relevance_score}</td>
                  <td className="px-3 py-2">{row.source || "fallback"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {kind === "latency" && (
        <pre className="mt-4 overflow-x-auto rounded-lg border border-slate-200 bg-white p-4 text-xs">
          {JSON.stringify(payload, null, 2)}
        </pre>
      )}
    </section>
  );
}
