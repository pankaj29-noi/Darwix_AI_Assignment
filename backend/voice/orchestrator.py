"""Conversation state machine for the three voice use cases.

Knowledge answers come from the Q2 retriever. This module does not store FAQ text.
"""

from __future__ import annotations

import json
import re
from uuid import uuid4

from app.config import PROJECT_ROOT
from app.database import utc_now
from multilingual import indonesia, philippines
from multilingual.detect import detect_indonesia
from rag.schemas import FALLBACK_EN
from voice.extract import (
    extract_health_slots,
    is_human_request,
    is_objection,
    is_question,
    is_refusal,
)
from voice.prompts import SYSTEM_PROMPT

HEALTH_FIELDS = [
    "insurance_requirement",
    "name",
    "age",
    "location",
    "family_coverage",
    "current_insurance",
    "budget_range",
    "preferred_coverage",
    "urgency",
    "callback_preference",
]

HEALTH_PROMPTS = {
    "insurance_requirement": "What kind of health insurance do you need?",
    "name": "What is your full name?",
    "age": "What is your age in years?",
    "location": "Which city do you live in?",
    "family_coverage": "Who should be covered: just you, or family members as well?",
    "current_insurance": "Do you currently have health insurance?",
    "budget_range": "What monthly budget do you have in mind, in rupees?",
    "preferred_coverage": "What sum insured would you like, for example 5 lakh?",
    "urgency": "How soon do you want the policy to start?",
    "callback_preference": "When is a good time for a callback if we need to follow up?",
}


def load_health_rules() -> dict:
    path = PROJECT_ROOT / "data" / "kb" / "health" / "rules.json"
    return json.loads(path.read_text(encoding="utf-8"))


def health_consent(text: str) -> str | None:
    lowered = text.lower()
    if re.search(r"\b(do not|don't)\b", lowered) and re.search(r"\b(consent|agree)\b", lowered):
        return "no"
    if re.search(r"\b(no|nope|stop)\b", lowered):
        return "no"
    if re.search(r"\b(yes|yeah|yep|agree|consent|sure|okay|ok)\b", lowered):
        return "yes"
    return None


def assess_health(fields: dict, rules: dict) -> dict:
    missing = [
        key
        for key in ("age", "location", "budget_range")
        if fields.get(key) in (None, "", "not provided")
    ]
    if missing:
        return {
            "eligible": False,
            "status": "incomplete",
            "reasons": [f"missing {', '.join(missing)}"],
        }
    reasons = []
    age = int(fields["age"])
    if age < rules["min_age"] or age > rules["max_age"]:
        reasons.append(f"age {age} is outside {rules['min_age']} to {rules['max_age']}")
    city = str(fields["location"]).strip().lower()
    if city not in rules["serviceable_locations"]:
        reasons.append(f"{fields['location']} is not in the serviceable city list")
    budget = int(str(fields["budget_range"]).replace(",", ""))
    if budget < rules["min_budget_inr"]:
        reasons.append(f"budget {budget} is below {rules['min_budget_inr']} rupees per month")
    if reasons:
        return {"eligible": False, "status": "not_eligible", "reasons": reasons}
    return {
        "eligible": True,
        "status": "preliminarily_eligible",
        "reasons": ["age, city, and budget are inside the published qualification rules"],
    }


class VoiceOrchestrator:
    def __init__(self, knowledge_base, database, voice_provider, llm=None):
        self.kb = knowledge_base
        self.db = database
        self.voice = voice_provider
        self.llm = llm
        self.sessions: dict[str, dict] = {}

    def start(self, use_case: str) -> dict:
        if use_case not in {"health", "philippines", "indonesia"}:
            raise ValueError("use_case must be health, philippines, or indonesia")
        started = self.voice.start_session(use_case)
        call_id = started["session_id"]
        if use_case == "philippines":
            message = philippines.greeting()
            fields_order = philippines.FIELDS
        elif use_case == "indonesia":
            message = indonesia.greeting()
            fields_order = indonesia.FIELDS
        else:
            message = (
                "Hello, this is Dana from Darwix Health on a web session. "
                "I can help you check a health-insurance lead. "
                "Do you consent to continue and to let me use your answers for this qualification?"
            )
            fields_order = HEALTH_FIELDS
        session = {
            "call_id": call_id,
            "use_case": use_case,
            "state": "CONSENT",
            "status": "in_progress",
            "fields": {},
            "field_order": fields_order,
            "declined": [],
            "pending_conflict": None,
            "eligibility": None,
            "eligibility_done": False,
            "summary_done": False,
            "escalated": False,
            "summary": "",
            "crm": None,
            "register": "formal",
            "mode": started["mode"],
            "created_at": utc_now(),
        }
        self.sessions[call_id] = session
        self.db.add_transcript(call_id, "agent", message)
        self._save(session)
        return self._public(session, message, fallback=False, sources=[])

    def handle(self, call_id: str, text: str) -> dict:
        session = self.sessions.get(call_id)
        if session is None:
            stored = self.db.get_call(call_id)
            if stored is None:
                raise ValueError("Unknown call_id")
            raise ValueError("Call exists in the database but not in this process. Start a new session.")
        text = text.strip()
        if not text:
            raise ValueError("Message text is empty")
        self.db.add_transcript(call_id, "customer", text)
        if session["state"] in {"END", "ESCALATED"}:
            message = "This web session is already closed."
            self.db.add_transcript(call_id, "agent", message)
            return self._public(session, message, fallback=False, sources=[])

        if is_human_request(text) and session["state"] != "CONSENT":
            return self._escalate(session, text)

        if session["state"] == "CONSENT":
            return self._handle_consent(session, text)

        resolved_conflict = False
        if session["pending_conflict"]:
            resolved = self._resolve_conflict(session, text)
            if not resolved:
                message = (
                    f"I heard two ages, {session['pending_conflict']['previous']} and "
                    f"{session['pending_conflict']['new']}. Which age should I keep?"
                )
                self.db.add_transcript(call_id, "agent", message)
                self._save(session)
                return self._public(session, message, fallback=False, sources=[])
            resolved_conflict = True

        parts: list[str] = []
        sources: list[dict] = []
        fallback = False
        if is_question(text) or is_objection(text):
            grounded = self._grounded(session, text)
            parts.append(grounded.answer)
            sources = grounded.sources
            fallback = grounded.fallback
            session["state"] = "OBJECTION" if is_objection(text) else "FAQ"
        elif is_refusal(text):
            pending = self._next_field(session)
            if pending:
                session["fields"][pending] = "not provided"
                session["declined"].append(pending)
        elif not resolved_conflict:
            self._fill(session, text)

        if session["pending_conflict"]:
            conflict = session["pending_conflict"]
            parts.append(
                f"I heard two ages, {conflict['previous']} and {conflict['new']}. Which age should I keep?"
            )
            session["state"] = "QUALIFICATION"
            message = " ".join(parts)
            self.db.add_transcript(session["call_id"], "agent", message)
            self._save(session)
            return self._public(session, message, fallback=fallback, sources=sources)

        pending = self._next_field(session)
        if pending:
            parts.append(self._prompt(session, pending))
            if pending == "insurance_requirement":
                session["state"] = "DISCOVERY"
            elif session["state"] not in {"FAQ", "OBJECTION"}:
                session["state"] = "QUALIFICATION"
            message = " ".join(part for part in parts if part)
            self.db.add_transcript(session["call_id"], "agent", message)
            self._save(session)
            return self._public(session, message, fallback=fallback, sources=sources)

        if not session["eligibility_done"]:
            eligibility_text, eligibility_sources = self._eligibility(session)
            parts.append(eligibility_text)
            sources = [*sources, *eligibility_sources]
            session["eligibility_done"] = True
            session["state"] = "ELIGIBILITY"
            if not session["fields"].get("callback_preference"):
                parts.append(self._prompt(session, "callback_preference"))
                session["state"] = "CALLBACK"
            message = " ".join(part for part in parts if part)
            self.db.add_transcript(session["call_id"], "agent", message)
            self._save(session)
            return self._public(session, message, fallback=fallback, sources=sources)

        if not session["summary_done"]:
            parts.append(self._summary(session))
            session["summary_done"] = True
            session["state"] = "SUMMARY"
            parts.append(self._end_prompt(session))
            message = " ".join(part for part in parts if part)
            self.db.add_transcript(session["call_id"], "agent", message)
            self._save(session)
            return self._public(session, message, fallback=fallback, sources=sources)

        if self._wants_end(session, text):
            session["state"] = "END"
            session["status"] = "completed"
            message = self._goodbye(session)
            self.db.add_transcript(session["call_id"], "agent", message)
            self._save(session)
            return self._public(session, message, fallback=False, sources=[])

        message = self._still_open_prompt(session)
        self.db.add_transcript(session["call_id"], "agent", message)
        self._save(session)
        return self._public(session, message, fallback=False, sources=[])

    def _handle_consent(self, session: dict, text: str) -> dict:
        if session["use_case"] == "philippines":
            decision = philippines.consent(text)
        elif session["use_case"] == "indonesia":
            decision = indonesia.consent(text)
            session["register"] = detect_indonesia(text)
            if session["register"] == "javanese_regional":
                session["register"] = "formal"
        else:
            decision = health_consent(text)
        if decision == "no":
            session["state"] = "END"
            session["status"] = "declined_consent"
            message = self._goodbye(session)
        elif decision == "yes":
            session["state"] = "DISCOVERY"
            message = self._prompt(session, self._next_field(session) or "insurance_requirement")
        else:
            message = self._reconsent(session)
        self.db.add_transcript(session["call_id"], "agent", message)
        self._save(session)
        return self._public(session, message, fallback=False, sources=[])

    def _resolve_conflict(self, session: dict, text: str) -> bool:
        match = re.search(r"\b(\d{1,2})\b", text)
        if not match:
            return False
        chosen = int(match.group(1))
        conflict = session["pending_conflict"]
        if chosen not in {int(conflict["previous"]), int(conflict["new"])}:
            return False
        session["fields"]["age"] = chosen
        session["pending_conflict"] = None
        return True

    def _fill(self, session: dict, text: str) -> None:
        if session["use_case"] == "indonesia":
            prepared, register, _ = indonesia.prepare_text(text)
            if register == "colloquial":
                session["register"] = "colloquial"
            elif register == "formal":
                session["register"] = "formal"
            text = prepared
        found = extract_health_slots(text) if session["use_case"] == "health" else {}
        if session["use_case"] == "philippines":
            name = re.search(r"\bako si\s+([A-Za-z]+(?:\s+[A-Za-z]+){0,3})", text, re.I)
            if name:
                found["name"] = name.group(1).title()
            city = re.search(r"\btaga\s+(.+?)\s+ako\b", text, re.I)
            if city:
                found["location"] = city.group(1).strip().title()
            if re.search(r"\blife insurance\b", text, re.I):
                found["insurance_requirement"] = (
                    "bancassurance life insurance" if "bank" in text.lower() else "life insurance"
                )
            if re.search(r"\b(wala pang account|walang account|no account)\b", text, re.I):
                found["bank_customer"] = "no partner-bank account"
            elif re.search(r"\b(may savings|may account|partner bank)\b", text, re.I):
                found["bank_customer"] = "partner-bank customer"
            beneficiary = re.search(r"\bbeneficiary ko si\s+([^.]+)", text, re.I)
            if beneficiary:
                found["beneficiary"] = beneficiary.group(1).strip()
            if re.search(r"\b(existing policy|life policy)\b", text, re.I):
                found["current_insurance"] = "none" if re.search(r"\bwala\b", text, re.I) else "yes"
            pesos = re.search(r"\b(\d[\d,]*)\s+pesos\b", text, re.I)
            if pesos:
                found["budget_range"] = int(pesos.group(1).replace(",", ""))
            if re.search(r"\bbukas ng umaga\b", text, re.I):
                found["callback_preference"] = "bukas ng umaga"
        if session["use_case"] == "indonesia":
            name = re.search(r"\bnama saya\s+([A-Za-z]+(?:\s+[A-Za-z]+){0,3})", text, re.I)
            if name:
                found["name"] = name.group(1).strip().title()
            if re.search(r"\bpembiayaan\b", text, re.I):
                found["insurance_requirement"] = text.strip().rstrip(".")
            amount = re.search(r"\b(\d[\d.]*)\b", text)
            if amount and self._next_field(session) == "budget_range":
                found["budget_range"] = int(amount.group(1).replace(".", ""))
            tenor = re.search(r"\b(\d+)\s*(bulan|tahun|months|month)\b", text, re.I)
            if tenor:
                found["tenor"] = tenor.group(0)
            if re.search(r"\bjatuh tempo\b", text, re.I):
                found["current_insurance"] = "jatuh tempo"
            if re.search(r"\bbesok pagi\b", text, re.I):
                found["callback_preference"] = "besok pagi"
        for key, value in found.items():
            self._assign(session, key, value)
        if found or session["pending_conflict"]:
            return
        pending = self._next_field(session)
        if pending and pending not in session["fields"]:
            if pending == "age":
                match = re.search(r"\b(\d{1,2})\b", text)
                if match:
                    self._assign(session, "age", int(match.group(1)))
                return
            if pending == "budget_range":
                match = re.search(r"\b(\d[\d,]*)\b", text)
                if match:
                    session["fields"]["budget_range"] = int(match.group(1).replace(",", ""))
                return
            session["fields"][pending] = text.strip()

    def _assign(self, session: dict, key: str, value) -> None:
        current = session["fields"].get(key)
        if (
            key == "age"
            and current not in (None, "", "not provided")
            and int(current) != int(value)
        ):
            session["pending_conflict"] = {"field": "age", "previous": int(current), "new": int(value)}
            return
        session["fields"][key] = value

    def _next_field(self, session: dict) -> str | None:
        for field in session["field_order"]:
            if field not in session["fields"]:
                return field
        return None

    def _prompt(self, session: dict, field: str) -> str:
        if session["use_case"] == "philippines":
            return philippines.PROMPTS[field]
        if session["use_case"] == "indonesia":
            return indonesia.prompts_for(session["register"])[field]
        return HEALTH_PROMPTS[field]

    def _grounded(self, session: dict, text: str):
        filters, fallback = self._retrieval_context(session, text)
        result = self.kb.answer(
            text,
            filters=filters,
            fallback_message=fallback,
            call_id=session["call_id"],
            llm=self.llm,
            system_prompt=SYSTEM_PROMPT,
        )
        if result.fallback and "language" in filters:
            broader = {key: value for key, value in filters.items() if key != "language"}
            second = self.kb.answer(
                text,
                filters=broader,
                fallback_message=fallback,
                call_id=session["call_id"],
                llm=self.llm,
                system_prompt=SYSTEM_PROMPT,
            )
            if not second.fallback:
                return second
        if result.fallback and "document_type" in filters:
            broader = {key: value for key, value in filters.items() if key != "document_type"}
            second = self.kb.answer(
                text,
                filters=broader,
                fallback_message=fallback,
                call_id=session["call_id"],
                llm=self.llm,
                system_prompt=SYSTEM_PROMPT,
            )
            if not second.fallback:
                return second
        return result

    def _retrieval_context(self, session: dict, text: str) -> tuple[dict, str]:
        if session["use_case"] == "philippines":
            return philippines.filters_for(text), philippines.fallback()
        if session["use_case"] == "indonesia":
            prepared, register, _ = indonesia.prepare_text(text)
            if register == "colloquial":
                session["register"] = "colloquial"
            filters = indonesia.filters_for(session["register"])
            return filters, indonesia.fallback(session["register"])
        return {"source_prefix": "health/"}, FALLBACK_EN

    def _eligibility(self, session: dict) -> tuple[str, list]:
        if session["use_case"] != "health":
            session["eligibility"] = {
                "eligible": None,
                "status": "lead_captured",
                "reasons": ["preliminary lead only; no underwriting decision was made"],
            }
            grounded = self._grounded(session, self._market_explainer(session))
            session["crm"] = self._crm(session)
            if session["use_case"] == "philippines":
                prefix = "Sapat na ito para sa preliminary lead. Hindi pa ito approval. "
            elif session["register"] == "colloquial":
                prefix = "Cukup buat dicatat dulu. Ini belum persetujuan. "
            else:
                prefix = "Data ini cukup untuk pencatatan awal. Ini belum persetujuan. "
            return prefix + grounded.answer, grounded.sources
        rules = load_health_rules()
        decision = assess_health(session["fields"], rules)
        session["eligibility"] = decision
        grounded = self._grounded(
            session,
            "Who qualifies for Darwix Health Shield by age, city, and monthly budget?",
        )
        if decision["status"] == "preliminarily_eligible":
            prefix = (
                "This lead looks preliminarily eligible under the qualification rules. "
                "This is not a final underwriting decision. "
            )
        elif decision["status"] == "incomplete":
            prefix = "I cannot mark eligibility because required details are missing. "
        else:
            prefix = "This lead is not eligible under the qualification rules: " + "; ".join(decision["reasons"]) + ". "
        session["crm"] = self._crm(session)
        return prefix + grounded.answer, grounded.sources

    def _market_explainer(self, session: dict) -> str:
        if session["use_case"] == "philippines":
            return "Paano binabayaran ang premium at ano ang ibig sabihin ng lapse at bank referral?"
        return "Bagaimana cicilan, tenor, dan denda dijelaskan dalam perjanjian pembiayaan?"

    def _summary(self, session: dict) -> str:
        if session["crm"] is None:
            session["crm"] = self._crm(session)
        fields = session["fields"]
        eligibility = session["eligibility"] or {}
        status = eligibility.get("status", session["status"])
        if session["use_case"] == "philippines":
            session["summary"] = (
                f"{philippines.summary_intro()} "
                f"Pangalan: {fields.get('name')}. Lungsod: {fields.get('location')}. "
                f"Bank: {fields.get('bank_customer')}. Beneficiary: {fields.get('beneficiary')}. "
                f"Premium: {fields.get('budget_range')} pesos kada buwan. "
                f"Existing policy: {fields.get('current_insurance')}. "
                f"Callback: {fields.get('callback_preference')}. "
                "Preliminary lead lang ito, hindi pa approval. Synthetic demo data."
            )
        elif session["use_case"] == "indonesia":
            session["summary"] = (
                "Ringkasan percakapan. "
                f"Nama: {fields.get('name')}. Produk: {fields.get('insurance_requirement')}. "
                f"Cicilan: {fields.get('budget_range')}. Tenor: {fields.get('tenor')}. "
                f"Status cicilan: {fields.get('current_insurance')}. "
                f"Callback: {fields.get('callback_preference')}. "
                "Ini pencatatan awal, bukan persetujuan. Data sintetis."
            )
        else:
            readable = ", ".join(f"{key}={value}" for key, value in fields.items())
            session["summary"] = (
                f"Here is the call summary. {readable}. "
                f"Status: {status}. Synthetic demo data only."
            )
        session["status"] = eligibility.get("status", session["status"])
        return session["summary"]

    def _crm(self, session: dict) -> dict:
        eligibility = session["eligibility"] or {}
        return {
            "synthetic": True,
            "lead_status": "escalated" if session["escalated"] else eligibility.get("status", "in_progress"),
            "use_case": session["use_case"],
            "fields": session["fields"],
            "callback_preference": session["fields"].get("callback_preference"),
            "note": "Mock CRM summary stored on the call. No external webhook was called.",
        }

    def _escalate(self, session: dict, text: str) -> dict:
        session["escalated"] = True
        session["state"] = "ESCALATED"
        session["status"] = "escalated"
        if session["use_case"] == "philippines":
            message = philippines.escalation()
        elif session["use_case"] == "indonesia":
            message = indonesia.escalation(session["register"])
        else:
            grounded = self._grounded(session, text) if is_question(text) else None
            message = (
                "I am escalating this web session to a human representative. "
                "I will stop the qualification here."
            )
            if grounded and grounded.fallback:
                message = grounded.answer + " " + message
        session["crm"] = self._crm(session)
        session["summary"] = message
        self.db.add_transcript(session["call_id"], "agent", message)
        self._save(session)
        return self._public(session, message, fallback=False, sources=[])

    def _end_prompt(self, session: dict) -> str:
        if session["use_case"] == "philippines":
            return "Tatapusin ko na ba ang web session?"
        if session["use_case"] == "indonesia":
            if session["register"] == "colloquial":
                return "Saya akhiri sesi web-nya sekarang?"
            return "Apakah saya akhiri sesi web ini?"
        return "Shall I end the web session?"

    def _still_open_prompt(self, session: dict) -> str:
        if session["use_case"] == "philippines":
            return "Sabihin lang ang oo kung tatapusin na natin ang web session."
        if session["use_case"] == "indonesia":
            if session["register"] == "colloquial":
                return "Bilang ya kalau sesi web-nya mau diakhiri."
            return "Katakan ya jika sesi web ini boleh diakhiri."
        return "Say yes when you want me to end the web session."

    def _wants_end(self, session: dict, text: str) -> bool:
        if session["use_case"] == "philippines":
            return philippines.consent(text) == "yes" or bool(re.search(r"\b(end|goodbye|tapos)\b", text, re.I))
        if session["use_case"] == "indonesia":
            return indonesia.consent(text) == "yes" or bool(re.search(r"\b(end|goodbye|selesai)\b", text, re.I))
        return bool(re.search(r"\b(yes|end|goodbye|stop)\b", text, re.I))

    def _goodbye(self, session: dict) -> str:
        if session["use_case"] == "philippines":
            return philippines.goodbye()
        if session["use_case"] == "indonesia":
            return indonesia.goodbye(session["register"])
        if session["status"] == "declined_consent":
            return "Thank you. I will end the web session because I do not have consent to continue."
        return "Thank you. I am ending this web session. A human team can follow the callback if one was requested."

    def _reconsent(self, session: dict) -> str:
        if session["use_case"] == "philippines":
            return "Pwede mo bang kumpirmahin kung oo o hindi ang pagpapatuloy ng call na ito?"
        if session["use_case"] == "indonesia":
            return "Mohon konfirmasi, apakah percakapan ini boleh dilanjutkan?"
        return "Please say yes if you consent to continue, or no if you want to stop."

    def _save(self, session: dict) -> None:
        self.db.upsert_call(
            {
                "id": session["call_id"],
                "use_case": session["use_case"],
                "state": session["state"],
                "status": session["status"],
                "qualification_json": json.dumps(session["fields"]),
                "summary": session["summary"],
                "escalated": int(session["escalated"]),
                "mode": session["mode"],
                "crm_json": json.dumps(session["crm"]),
                "created_at": session["created_at"],
                "updated_at": utc_now(),
            }
        )

    def _public(self, session: dict, message: str, fallback: bool, sources: list) -> dict:
        return {
            "call_id": session["call_id"],
            "use_case": session["use_case"],
            "state": session["state"],
            "status": session["status"],
            "message": message,
            "qualification": session["fields"],
            "escalated": session["escalated"],
            "fallback": fallback,
            "sources": sources,
            "summary": session["summary"] or None,
            "crm": session["crm"],
            "mode": session["mode"],
            "register": session["register"],
            "eligibility": session["eligibility"],
        }
