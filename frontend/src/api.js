const BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export function apiBase() {
  return BASE;
}

export function wsBase() {
  return BASE.replace(/^http/, "ws");
}

async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await response.text();
  const body = text ? JSON.parse(text) : null;
  if (!response.ok) {
    throw new Error(body?.detail || response.statusText);
  }
  return body;
}

export const api = {
  health: () => request("/health"),
  search: (query) => request("/kb/search", { method: "POST", body: JSON.stringify({ query, top_k: 4 }) }),
  records: () => request("/kb/records"),
  ingest: () => request("/kb/ingest", { method: "POST", body: JSON.stringify({ path: "" }) }),
  startVoice: (useCase) => request("/voice/session", { method: "POST", body: JSON.stringify({ use_case: useCase }) }),
  sendVoice: (callId, text) =>
    request("/voice/message", { method: "POST", body: JSON.stringify({ call_id: callId, text }) }),
  runScenario: (useCase, scenario) =>
    request(`/voice/scenario?scenario=${scenario}`, { method: "POST", body: JSON.stringify({ use_case: useCase }) }),
  evaluation: () => request("/evaluation"),
  latency: () => request("/latency"),
  philippines: () => request("/multilingual/philippines"),
  indonesia: () => request("/multilingual/indonesia"),
  accent: () => request("/multilingual/indonesia/accent-test"),
  realtimeScenarios: () => request("/realtime/scenarios"),
  startRealtime: () => request("/realtime/session", { method: "POST", body: JSON.stringify({}) }),
  replay: (callId, scenario, speed) =>
    request("/realtime/replay", {
      method: "POST",
      body: JSON.stringify({ call_id: callId, scenario, speed }),
    }),
};
