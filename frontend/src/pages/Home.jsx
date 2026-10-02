import { Link } from "react-router-dom";

const cards = [
  ["Knowledge Base", "Ingest, clean, retrieve, and cite health, Philippines, and Indonesia material.", "/knowledge"],
  ["Voice Agent", "Qualify a synthetic health-insurance lead from the knowledge base.", "/voice"],
  ["Philippines", "Taglish bancassurance flow with local payment wording.", "/philippines"],
  ["Indonesia", "Formal and colloquial multifinance flow, plus an honest accent report.", "/indonesia"],
  ["Live Intelligence", "Replay a call in chunks and show signals and nudges while it runs.", "/dashboard"],
];

export default function Home() {
  return (
    <section>
      <h2 className="text-2xl font-semibold">Assignment workspace</h2>
      <p className="mt-2 max-w-3xl text-slate-600">
        This is a local web demo for health-insurance qualification, a traceable knowledge base, Philippines and
        Indonesia voice flows, and live call nudges. Synthetic demo data only. The web session is not a phone call.
      </p>
      <div className="mt-6 grid gap-3 md:grid-cols-2">
        {cards.map(([title, copy, href]) => (
          <Link key={href} to={href} className="rounded-lg border border-slate-200 bg-white p-4 hover:border-teal-300">
            <h3 className="font-medium">{title}</h3>
            <p className="mt-1 text-sm text-slate-600">{copy}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
