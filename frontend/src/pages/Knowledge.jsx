import { useEffect, useState } from "react";
import { api } from "../api";

export default function Knowledge() {
  const [query, setQuery] = useState("What is the waiting period for pre-existing conditions?");
  const [result, setResult] = useState(null);
  const [records, setRecords] = useState([]);
  const [error, setError] = useState("");

  async function loadRecords() {
    const payload = await api.records();
    setRecords(payload.records);
  }

  useEffect(() => {
    loadRecords().catch((err) => setError(err.message));
  }, []);

  async function search(event) {
    event.preventDefault();
    setError("");
    try {
      setResult(await api.search(query));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section>
      <h2 className="text-2xl font-semibold">Knowledge base</h2>
      <p className="mt-2 text-sm text-slate-600">
        Answers are quoted from retrieved chunks. A low score returns the safe fallback instead of a guessed fact.
      </p>
      <form onSubmit={search} className="mt-4 flex gap-2">
        <input
          className="w-full rounded-md border border-slate-300 px-3 py-2"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <button className="rounded-md bg-tide px-4 py-2 text-white" type="submit">
          Search
        </button>
      </form>
      <button
        className="mt-3 text-sm text-tide underline"
        type="button"
        onClick={() => api.ingest().then(loadRecords).catch((err) => setError(err.message))}
      >
        Rebuild index from data/kb
      </button>
      {error && <p className="mt-3 text-sm text-red-700">{error}</p>}
      {result && (
        <article className="mt-4 rounded-lg border border-slate-200 bg-white p-4">
          <p className="text-sm text-slate-500">
            Confidence {result.confidence} · {result.generation_mode} · fallback {String(result.fallback)}
          </p>
          <p className="mt-2">{result.answer}</p>
          <ul className="mt-3 space-y-1 text-sm text-slate-600">
            {result.sources.map((source) => (
              <li key={source.record_id}>
                {source.source} · {source.record_id} · {source.section} · score {source.score}
              </li>
            ))}
          </ul>
        </article>
      )}
      <h3 className="mt-8 font-medium">Records ({records.length})</h3>
      <div className="mt-2 overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-500">
            <tr>
              <th className="px-3 py-2">Record</th>
              <th className="px-3 py-2">Category</th>
              <th className="px-3 py-2">Source</th>
              <th className="px-3 py-2">PII</th>
            </tr>
          </thead>
          <tbody>
            {records.map((record) => (
              <tr key={record.record_id} className="border-t border-slate-100">
                <td className="px-3 py-2">{record.title}</td>
                <td className="px-3 py-2">{record.category}</td>
                <td className="px-3 py-2">{record.source}</td>
                <td className="px-3 py-2">{record.pii ? "flagged" : "no"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
