import { useEffect, useState } from "react";
import { api, wsBase } from "../api";

export default function Dashboard() {
  const [scenarios, setScenarios] = useState([]);
  const [scenario, setScenario] = useState("full_demo");
  const [speed, setSpeed] = useState(1);
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  useEffect(() => {
    api.realtimeScenarios()
      .then((payload) => setScenarios(Object.keys(payload)))
      .catch((err) => setError(err.message));
  }, []);

  async function start() {
    setError("");
    setEvents([]);
    const session = await api.startRealtime();
    setStatus("connecting");
    const socket = new WebSocket(`${wsBase()}/ws/realtime/${session.call_id}`);
    socket.onmessage = (message) => {
      const event = JSON.parse(message.data);
      setEvents((current) => [...current, event]);
      if (event.type === "replay_complete") setStatus("complete");
    };
    socket.onerror = () => setError("WebSocket failed. Is the backend running?");
    socket.onopen = async () => {
      setStatus("live");
      await api.replay(session.call_id, scenario, Number(speed));
    };
  }

  const nudges = events.flatMap((event) => event.nudges || []);
  const signals = events.flatMap((event) => event.signals || []);

  return (
    <section>
      <h2 className="text-2xl font-semibold">Live call intelligence</h2>
      <p className="mt-2 text-sm text-slate-600">
        The server replays a transcript in chunks. Speed 1 follows the script timestamps. Nudges appear before the
        replay_complete event. This is not an uploaded recording analyzed after the call.
      </p>
      <div className="mt-4 flex flex-wrap items-end gap-3">
        <label className="text-sm">
          Scenario
          <select className="mt-1 block rounded-md border border-slate-300 px-2 py-2" value={scenario} onChange={(event) => setScenario(event.target.value)}>
            {scenarios.map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          Speed
          <input
            className="mt-1 block w-24 rounded-md border border-slate-300 px-2 py-2"
            type="number"
            min="0"
            step="0.5"
            value={speed}
            onChange={(event) => setSpeed(event.target.value)}
          />
        </label>
        <button className="rounded-md bg-tide px-4 py-2 text-white" onClick={start} type="button">
          Start replay
        </button>
        <span className="text-sm text-slate-500">Status: {status}</span>
      </div>
      {error && <p className="mt-3 text-sm text-red-700">{error}</p>}
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <h3 className="font-medium">Transcript</h3>
          {events
            .filter((event) => event.text)
            .map((event) => (
              <p key={`${event.chunk_index}-${event.speaker}`} className="mt-3 text-sm">
                <span className="font-medium">{event.offset_ms} ms {event.speaker}: </span>
                {event.text}
                <span className="block text-xs text-slate-500">
                  e2e {Number(event.latency_ms?.e2e_ms || 0).toFixed(2)} ms · signal {Number(event.latency_ms?.signal_ms || 0).toFixed(2)} ms · LLM {String(event.latency_ms?.llm_ms)}
                </span>
              </p>
            ))}
        </div>
        <div className="space-y-4">
          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <h3 className="font-medium">Signals ({signals.length})</h3>
            {signals.map((signal) => (
              <p key={signal.signal_id} className="mt-2 text-sm">
                {signal.type} · {signal.confidence} · {signal.evidence}
              </p>
            ))}
          </div>
          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <h3 className="font-medium">Nudges ({nudges.length})</h3>
            {nudges.map((nudge) => (
              <p key={nudge.nudge_id} className="mt-2 text-sm">
                {nudge.text}
                <span className="block text-xs text-slate-500">Evidence: {nudge.evidence}</span>
              </p>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
