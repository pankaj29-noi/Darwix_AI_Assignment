import { useEffect, useState } from "react";
import { api } from "../api";

const scenarios = {
  health: ["cooperative", "objection", "unsupported", "incomplete", "conflict"],
  philippines: ["cooperative", "objection", "taglish", "colloquial", "escalation"],
  indonesia: ["cooperative", "objection", "colloquial", "mixed", "escalation"],
};

export default function Voice({ useCase, title }) {
  const [call, setCall] = useState(null);
  const [turns, setTurns] = useState([]);
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [locale, setLocale] = useState(null);
  const [voiceName, setVoiceName] = useState("not used");

  useEffect(() => {
    if (useCase === "philippines") api.philippines().then(setLocale).catch((err) => setError(err.message));
    if (useCase === "indonesia") api.indonesia().then(setLocale).catch((err) => setError(err.message));
  }, [useCase]);

  function speak(message) {
    if (!window.speechSynthesis) {
      setVoiceName("speechSynthesis unavailable");
      return;
    }
    const utterance = new SpeechSynthesisUtterance(message);
    const voices = window.speechSynthesis.getVoices();
    const wanted = useCase === "indonesia" ? "id" : useCase === "philippines" ? "fil" : "en";
    const match = voices.find((voice) => voice.lang.toLowerCase().startsWith(wanted));
    if (match) utterance.voice = match;
    utterance.lang = match?.lang || (useCase === "indonesia" ? "id-ID" : useCase === "philippines" ? "fil-PH" : "en-IN");
    setVoiceName(match ? `${match.name} (${match.lang})` : `no ${wanted} voice installed; browser default`);
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }

  function listen() {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      setError("Microphone speech recognition is not available in this browser. Type the customer line.");
      return;
    }
    const recognition = new Recognition();
    recognition.lang = useCase === "indonesia" ? "id-ID" : useCase === "philippines" ? "fil-PH" : "en-IN";
    recognition.onresult = (event) => {
      const said = event.results[0][0].transcript;
      setText(said);
    };
    recognition.onerror = () => setError("The browser could not use the microphone.");
    recognition.start();
  }

  async function start() {
    setError("");
    const session = await api.startVoice(useCase);
    setCall(session);
    setTurns([{ speaker: "agent", text: session.message }]);
    speak(session.message);
  }

  async function send(event) {
    event.preventDefault();
    if (!call || !text.trim()) return;
    const customer = text.trim();
    setText("");
    const reply = await api.sendVoice(call.call_id, customer);
    setCall(reply);
    setTurns((current) => [...current, { speaker: "customer", text: customer }, { speaker: "agent", text: reply.message }]);
    speak(reply.message);
  }

  async function run(name) {
    setError("");
    const payload = await api.runScenario(useCase, name);
    setCall(payload.call);
    setTurns(payload.turns.filter((turn) => turn.speaker));
  }

  return (
    <section>
      <h2 className="text-2xl font-semibold">{title}</h2>
      <p className="mt-2 text-sm text-slate-600">
        Browser speech is local. It is labeled mock/web mode and is not a phone call. Server TTS did not create audio.
      </p>
      <p className="mt-1 text-sm text-slate-500">Browser voice: {voiceName}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <button className="rounded-md bg-tide px-3 py-2 text-sm text-white" onClick={start} type="button">
          Start web session
        </button>
        <button className="rounded-md border border-slate-300 px-3 py-2 text-sm" onClick={listen} type="button">
          Microphone
        </button>
        {scenarios[useCase].map((name) => (
          <button key={name} className="rounded-md border border-slate-300 px-3 py-2 text-sm" onClick={() => run(name)} type="button">
            Run {name}
          </button>
        ))}
      </div>
      {error && <p className="mt-3 text-sm text-red-700">{error}</p>}
      <div className="mt-4 grid gap-4 lg:grid-cols-[2fr_1fr]">
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          {turns.map((turn, index) => (
            <p key={index} className="mb-3 text-sm">
              <span className="font-medium capitalize">{turn.speaker}: </span>
              {turn.text}
            </p>
          ))}
          <form onSubmit={send} className="mt-4 flex gap-2">
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              value={text}
              placeholder="Customer says..."
              onChange={(event) => setText(event.target.value)}
            />
            <button className="rounded-md bg-slate-900 px-3 py-2 text-white" type="submit">
              Send
            </button>
          </form>
        </div>
        <aside className="rounded-lg border border-slate-200 bg-white p-4 text-sm">
          <h3 className="font-medium">Session</h3>
          <p className="mt-2">State: {call?.state || "not started"}</p>
          <p>Escalated: {String(call?.escalated || false)}</p>
          <p>Fallback: {String(call?.fallback || false)}</p>
          <h3 className="mt-4 font-medium">Qualification</h3>
          <pre className="mt-2 whitespace-pre-wrap text-xs text-slate-600">
            {JSON.stringify(call?.qualification || {}, null, 2)}
          </pre>
          {call?.summary && <p className="mt-3">{call.summary}</p>}
          {locale && (
            <div className="mt-4">
              <h3 className="font-medium">Localization examples</h3>
              {locale.examples.map((example) => (
                <p key={example.id} className="mt-2 text-xs text-slate-600">
                  <span className="font-medium text-slate-800">{example.id}. </span>
                  {example.text}
                </p>
              ))}
              {locale.accent_test && (
                <p className="mt-3 text-xs">
                  Accent ASR actual transcript: {locale.accent_test.actual_transcript}. {locale.accent_test.observed_error}
                </p>
              )}
            </div>
          )}
        </aside>
      </div>
    </section>
  );
}
