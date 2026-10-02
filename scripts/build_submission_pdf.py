"""Build the reviewer-facing Darwix submission PDF.

Install the small optional dependency first:
    pip install -r scripts/requirements-submission.txt

Replace both link arguments before the final upload.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "submission" / "DARWIX_AI_ASSIGNMENT_SUBMISSION.pdf"


def ascii_text(text: str) -> str:
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2022": "-",
        "\u2192": "->",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text.encode("latin-1", errors="replace").decode("latin-1")


class SubmissionPDF(FPDF):
    def header(self) -> None:
        if self.page_no() > 1:
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(34, 53, 73)
            self.cell(0, 6, "Darwix AI Engineer Assessment", align="L")
            self.ln(8)
            self.set_draw_color(205, 214, 223)
            self.line(15, self.get_y(), 195, self.get_y())
            self.ln(4)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(95, 105, 120)
        self.cell(0, 5, f"Page {self.page_no()}/{{nb}}", align="C")

    def title_text(self, text: str) -> None:
        self.set_font("Helvetica", "B", 23)
        self.set_text_color(15, 55, 72)
        self.multi_cell(0, 10, ascii_text(text), new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def section(self, text: str) -> None:
        self.ln(2)
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(16, 93, 112)
        self.multi_cell(0, 8, ascii_text(text), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def subsection(self, text: str) -> None:
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(34, 53, 73)
        self.multi_cell(0, 6, ascii_text(text), new_x="LMARGIN", new_y="NEXT")

    def body(self, text: str, *, bold: bool = False) -> None:
        self.set_font("Helvetica", "B" if bold else "", 9.5)
        self.set_text_color(38, 48, 60)
        self.multi_cell(0, 5.2, ascii_text(text), new_x="LMARGIN", new_y="NEXT")

    def bullet(self, text: str) -> None:
        self.set_font("Helvetica", "", 9.3)
        self.set_text_color(38, 48, 60)
        x = self.get_x()
        self.cell(5, 5, "-")
        self.multi_cell(0, 5, ascii_text(text), new_x="LMARGIN", new_y="NEXT")
        self.set_x(x)

    def link_box(self, label: str, value: str) -> None:
        self.set_fill_color(239, 246, 248)
        self.set_draw_color(173, 203, 211)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(15, 55, 72)
        self.cell(0, 7, ascii_text(label), border="LTR", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(38, 48, 60)
        self.multi_cell(
            0,
            6,
            ascii_text(value),
            border="LBR",
            fill=True,
            new_x="LMARGIN",
            new_y="NEXT",
        )
        self.ln(3)


def build_pdf(github_url: str, video_url: str, output: Path) -> None:
    pdf = SubmissionPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.set_margins(15, 14, 15)

    # Cover
    pdf.add_page()
    pdf.set_fill_color(15, 55, 72)
    pdf.rect(0, 0, 210, 54, style="F")
    pdf.set_y(18)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 25)
    pdf.multi_cell(
        0,
        11,
        "Darwix AI Voice\nIntelligence Platform",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.set_y(61)
    pdf.set_text_color(16, 93, 112)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "AI Engineer Assessment Submission")
    pdf.ln(13)
    pdf.body("Candidate: Pankaj Bishnoi", bold=True)
    pdf.body("Coverage: Questions 1-4 | Local working prototype | Synthetic demo data")
    pdf.ln(4)
    pdf.link_box("GitHub repository", github_url)
    pdf.link_box("Video walkthrough", video_url)
    pdf.section("Submission snapshot")
    pdf.bullet("34 automated tests passed; 0 failed.")
    pdf.bullet("6/6 RAG evaluation cases marked CORRECT by the executed rubric.")
    pdf.bullet("Full real-time demo produced 6 signals and 5 evidence-backed nudges.")
    pdf.bullet("Neutral and noisy false-positive scenarios produced 0 nudges.")
    pdf.bullet("Latest local end-to-end latency: P50 1.178541 ms; P95 1.426871 ms over 7 chunks.")
    pdf.ln(2)
    pdf.body(
        "Important disclosure: the web interface is not a phone call. Cloud ASR quality/latency, "
        "LLM latency, and Filipino TTS quality are NOT MEASURED. No result is inferred or fabricated."
    )

    # Q1/Q2
    pdf.add_page()
    pdf.title_text("Q1 + Q2: Grounded voice agent and knowledge base")
    pdf.subsection("Q1 - Health-insurance lead qualification")
    for item in (
        "Conversation flow: greeting, consent, discovery, qualification, FAQ/objection, preliminary eligibility, callback/escalation, summary, and end.",
        "The voice agent calls the same KnowledgeBase.answer path used by the retrieval API; policy and objection facts are not embedded in the system prompt.",
        "Unsupported questions return a fixed safe fallback and can route to a human.",
        "The UI is a clearly labeled mock web session. A mock CRM summary and callback preference are stored.",
        "Executed scenarios cover cooperative, objection, incomplete, conflicting details, out-of-scope, and human assistance.",
    ):
        pdf.bullet(item)
    pdf.subsection("Q2 - Traceable RAG pipeline")
    for item in (
        "Input support: PDF, TXT, Markdown, HTML, and CSV.",
        "Pipeline: extraction -> cleaning -> normalization -> dedupe/near-dedupe -> PII redaction -> section-aware chunking -> metadata -> TF-IDF/FAISS -> reranking -> threshold -> cited answer or fallback.",
        "Records retain record_id, title, content, category, source, source_url, section, version, timestamps, PII, language, document_type, chunk_id, and hash.",
        "Six executed queries cover product, policy, qualification, FAQ, objection, and out-of-scope.",
    ):
        pdf.bullet(item)
    pdf.subsection("Executed retrieval results")
    rows = (
        ("Product", "kb_health_product_c001", "0.4464", "CORRECT"),
        ("Policy", "kb_health_policy_c001", "0.4166", "CORRECT"),
        ("Qualification", "kb_health_qualification_c001", "0.2743", "CORRECT"),
        ("FAQ", "kb_health_faq_c001", "0.3710", "CORRECT"),
        ("Objection", "kb_health_objection_c001", "0.3078", "CORRECT"),
        ("Out of scope", "safe fallback", "0.0000", "CORRECT"),
    )
    pdf.set_font("Helvetica", "B", 8.3)
    pdf.set_fill_color(226, 239, 242)
    for width, label in zip((33, 77, 27, 35), ("Type", "Top record", "Score", "Verdict")):
        pdf.cell(width, 7, label, border=1, fill=True)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    for row in rows:
        for width, value in zip((33, 77, 27, 35), row):
            pdf.cell(width, 7, value, border=1)
        pdf.ln()

    # Q3/Q4
    pdf.add_page()
    pdf.title_text("Q3 + Q4: Localization and live intelligence")
    pdf.subsection("Q3 - Philippines and Indonesia")
    for item in (
        "Philippines bancassurance supports English, Filipino/Tagalog, and natural Taglish, including premium, policy, beneficiary, rider, lapse, coverage, and bank referral.",
        "Indonesia multifinance supports formal and colloquial Bahasa plus finance terms such as cicilan, tenor, denda, DP, jatuh tempo, angsuran, and pembiayaan.",
        "At least three documented localization examples per market explain why wording is localized rather than literally translated.",
        "Fallback and escalation remain in the customer's language/register.",
        "The Javanese-influenced case reports expected meaning and a text-normalization preview. Actual acoustic accent recognition is NOT MEASURED.",
    ):
        pdf.bullet(item)
    pdf.subsection("Q4 - Streaming nudges before the replay ends")
    for item in (
        "Real-time-speed replay emits chunks through mock ASR, speaker-labeled transcript storage, signal detection, nudge generation, WebSocket delivery, and dashboard rendering.",
        "Signals include intent shift, compliance, frustration, buying intent, missed opportunity, callback, and payment difficulty.",
        "Nudges include evidence text, confidence, timestamp, and stage latency.",
        "Controls include confidence threshold, duplicate suppression, 45-second call-time cooldown, priority, topic grouping, expiry, and repetition limits.",
        "Full demo: 6 signals, 5 nudges. Neutral and noisy scenarios: 0 nudges each.",
    ):
        pdf.bullet(item)
    pdf.subsection("Measured local latency (milliseconds, n=7)")
    rows = (
        ("Mock ASR passthrough", "0.001584", "0.001921"),
        ("Signal extraction", "0.028541", "0.039529"),
        ("Nudge generation", "0.005584", "0.008488"),
        ("Delivery/SQLite", "1.130834", "1.381591"),
        ("End to end", "1.178541", "1.426871"),
        ("LLM", "NOT MEASURED", "NOT MEASURED"),
    )
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_fill_color(226, 239, 242)
    for width, label in zip((82, 45, 45), ("Stage", "P50", "P95")):
        pdf.cell(width, 7, label, border=1, fill=True)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8.2)
    for row in rows:
        for width, value in zip((82, 45, 45), row):
            pdf.cell(width, 7, value, border=1)
        pdf.ln()
    pdf.body(
        "These are in-process CPU/SQLite measurements with replay sleep excluded. They are not "
        "claims about cloud ASR, browser network delivery, or a hosted model."
    )

    # Architecture/evidence/limits
    pdf.add_page()
    pdf.title_text("Architecture, evidence, and production readiness")
    pdf.subsection("Architecture")
    pdf.body(
        "Voice path: React web session -> ASRProvider -> VoiceOrchestrator -> KnowledgeBase.answer "
        "-> FAISS + SQLite -> extractive/live LLM generator -> TTSProvider/browser speech."
    )
    pdf.body(
        "Live path: real-time replay chunks -> ASRProvider -> SignalDetector -> NudgeEngine -> "
        "SQLite + WebSocket hub -> Live Intelligence dashboard."
    )
    pdf.subsection("Repository evidence")
    for item in (
        "README.md - setup, environment variables, usage, testing, and limitations.",
        "docs/ARCHITECTURE.md - component and data-flow diagrams.",
        "docs/Q1_VOICE_AGENT.md through docs/Q4_REALTIME.md - implementation decisions.",
        "results/ - executed RAG, multilingual, nudge, latency, and test JSON.",
        "transcripts/ - Q1, Philippines, Indonesia, and Q4 executed scenarios.",
        "recordings/MANIFEST.json - explicit synthetic-audio provenance and missing live-call disclosure.",
        "docs/PRODUCTION_PLAN.md - 10x scale, noisy audio, security, and provider improvements.",
    ):
        pdf.bullet(item)
    pdf.subsection("Known limitations")
    for item in (
        "No live telephony integration; the submitted interface is a web session.",
        "No credentialed cloud ASR or LLM run; those quality and latency claims remain NOT MEASURED.",
        "TF-IDF is the executed embedding path. The optional sentence-transformers path was not run.",
        "Speaker labels are provided by scripted scenarios, not acoustic diarization.",
        "No native Filipino system voice was available; synthetic audio must not be presented as a customer call.",
    ):
        pdf.bullet(item)
    pdf.subsection("Production improvements")
    pdf.body(
        "Priorities: credentialed streaming ASR, tenant authentication, Postgres/pgvector, queues, "
        "encrypted PII, observability, provider fallbacks, native-speaker/compliance review, and "
        "load/noise evaluation at 10x concurrency."
    )
    pdf.subsection("Reviewer quick start")
    pdf.body(
        "Install backend/requirements.txt and frontend dependencies, copy .env.example to .env, "
        "run FastAPI on port 8000 and Vite on port 5173, then follow docs/DEMO_SCRIPT.md."
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--github-url",
        default="ADD_PUBLIC_OR_REVIEWER_ACCESSIBLE_GITHUB_URL",
    )
    parser.add_argument(
        "--video-url",
        default="ADD_UNLISTED_YOUTUBE_OR_PUBLIC_DRIVE_URL",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build_pdf(args.github_url, args.video_url, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
