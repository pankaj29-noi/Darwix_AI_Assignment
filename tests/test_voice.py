"""Voice state machine tests."""

import json

from app.config import PROJECT_ROOT
from voice.orchestrator import assess_health, load_health_rules
from voice.prompts import SYSTEM_PROMPT


def _run(client, use_case: str, scenario: str):
    response = client.post(f"/voice/scenario?scenario={scenario}", json={"use_case": use_case})
    assert response.status_code == 200, response.text
    return response.json()


def test_system_prompt_does_not_hardcode_policy_facts():
    lowered = SYSTEM_PROMPT.lower()
    for fact in ("36 months", "rate card", "5 lakh", "cashless", "too expensive"):
        assert fact not in lowered


def test_cooperative_call_qualifies_and_cites_waiting_period(client):
    payload = _run(client, "health", "cooperative")
    call = payload["call"]
    assert call["state"] == "END"
    assert call["qualification"]["name"] == "Riya Sharma"
    assert call["qualification"]["age"] == 32
    assert call["qualification"]["location"] == "Pune"
    assert call["eligibility"]["status"] == "preliminarily_eligible"
    blob = " ".join(turn["text"] for turn in payload["turns"])
    assert "36 months" in blob
    assert "Paris" not in blob
    eligibility_turns = [
        turn for turn in payload["turns"] if turn.get("state") == "ELIGIBILITY" and turn.get("speaker") == "agent"
    ]
    assert eligibility_turns
    assert eligibility_turns[0]["sources"]
    assert eligibility_turns[0]["sources"][0]["version"] == "1.0"
    assert eligibility_turns[0]["sources"][0]["source_url"] == ""
    assert "A lead is qualified when age is from 18 to 65" in eligibility_turns[0]["text"]
    logs = client.app.state.db.conn.execute("SELECT COUNT(*) AS n FROM retrieval_logs").fetchone()["n"]
    assert logs >= 1


def test_objection_uses_knowledge_base(client):
    payload = _run(client, "health", "objection")
    blob = " ".join(turn["text"] for turn in payload["turns"] if turn["speaker"] == "agent")
    assert "rate card" in blob.lower()
    assert "50%" not in blob


def test_unsupported_question_then_human(client):
    payload = _run(client, "health", "unsupported")
    agents = [turn["text"] for turn in payload["turns"] if turn["speaker"] == "agent"]
    assert any("knowledge base" in text.lower() for text in agents)
    assert all("Paris" not in text for text in agents)
    assert payload["call"]["escalated"] is True
    assert payload["call"]["state"] == "ESCALATED"


def test_incomplete_does_not_invent_age(client):
    payload = _run(client, "health", "incomplete")
    assert payload["call"]["qualification"]["age"] == "not provided"
    assert payload["call"]["qualification"]["name"] == "Neha Iyer"


def test_conflicting_age_waits_for_confirmation(client):
    payload = _run(client, "health", "conflict")
    assert payload["call"]["qualification"]["age"] == 45
    assert any("two ages" in turn["text"].lower() for turn in payload["turns"])


def test_out_of_range_age_is_not_eligible():
    rules = load_health_rules()
    decision = assess_health(
        {"age": 70, "location": "Pune", "budget_range": 2500},
        rules,
    )
    assert decision["eligible"] is False
    assert decision["status"] == "not_eligible"


def test_scenarios_file_has_required_coverage():
    scenarios = json.loads((PROJECT_ROOT / "data" / "voice" / "scenarios.json").read_text())
    for key in ("health:cooperative", "health:objection", "health:unsupported", "health:incomplete", "health:conflict"):
        assert scenarios[key]["turns"]
