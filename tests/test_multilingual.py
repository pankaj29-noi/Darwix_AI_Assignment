"""Localization is configuration and retrieval, not a translator call."""

from multilingual.detect import detect_indonesia, detect_philippines, normalize_javanese_lexicon
from multilingual.indonesia import ACCENT_TEST, fallback, load_config as load_id
from multilingual.philippines import load_config as load_ph


def test_code_switching_detector():
    assert detect_philippines("Magkano yung premium per month?") == "taglish"
    assert detect_philippines("Wala pa akong beneficiary") == "tl"
    assert detect_philippines("I need a life insurance policy") == "en"
    assert detect_indonesia("Apakah tenor pembiayaan dapat diubah?") == "formal"
    assert detect_indonesia("Gue telat bayar cicilan, bisa nego denda nggak?") == "colloquial"
    assert detect_indonesia("Nyuwun sewu, cicilane telat, bayare piye?") == "javanese_regional"


def test_localization_examples_are_not_english_paraphrases_only():
    philippines = load_ph()
    indonesia = load_id()
    assert len(philippines["examples"]) >= 3
    assert len(indonesia["examples"]) >= 3
    for example in philippines["examples"] + indonesia["examples"]:
        assert example["why_localization"]
        assert example["text"] != example["literal_translation_to_avoid"]
    joined = " ".join(example["text"] for example in philippines["examples"]).lower()
    for term in ("premium", "policy", "beneficiary", "rider", "lapse", "coverage", "bank"):
        assert term in joined
    id_text = " ".join(example["text"] for example in indonesia["examples"]).lower()
    for term in ("cicilan", "tenor", "denda", "dp", "jatuh tempo", "angsuran", "pembiayaan"):
        assert term in id_text


def test_accent_report_does_not_invent_asr_output():
    assert ACCENT_TEST["actual_transcript"] == "NOT MEASURED"
    assert "NOT MEASURED" in ACCENT_TEST["observed_error"]
    normalized = normalize_javanese_lexicon(ACCENT_TEST["test_phrase"])
    assert "cicilan" in normalized
    assert "bagaimana" in normalized
    assert "english" not in fallback("colloquial").lower()


def test_philippines_cooperative_slots_are_not_inverted(client):
    response = client.post("/voice/scenario?scenario=cooperative", json={"use_case": "philippines"})
    assert response.status_code == 200, response.text
    fields = response.json()["call"]["qualification"]
    assert fields["bank_customer"] == "partner-bank customer"
    assert fields["location"] == "Quezon City"
    assert fields["name"] == "Juan Dela Cruz"
    summary = response.json()["call"]["summary"].lower()
    assert "i have enough" not in summary
    assert "quezon city" in summary
    eligibility = [
        turn
        for turn in response.json()["turns"]
        if turn.get("state") == "ELIGIBILITY" and turn.get("speaker") == "agent"
    ]
    assert eligibility and eligibility[0]["sources"]
    assert "hindi pa ito approval" in eligibility[0]["text"].lower()


def test_indonesia_cooperative_name_is_parsed(client):
    response = client.post("/voice/scenario?scenario=cooperative", json={"use_case": "indonesia"})
    assert response.status_code == 200, response.text
    fields = response.json()["call"]["qualification"]
    assert fields["name"] == "Sari Wulandari"
    assert fields["current_insurance"] == "jatuh tempo"
    eligibility = [
        turn
        for turn in response.json()["turns"]
        if turn.get("state") == "ELIGIBILITY" and turn.get("speaker") == "agent"
    ]
    assert eligibility
    assert "i have enough" not in eligibility[0]["text"].lower()
    assert eligibility[0]["sources"]


def test_philippines_objection_stays_localized(client):
    response = client.post("/voice/scenario?scenario=objection", json={"use_case": "philippines"})
    assert response.status_code == 200, response.text
    blob = " ".join(turn["text"] for turn in response.json()["turns"] if turn["speaker"] == "agent").lower()
    assert "lapse" in blob or "premium" in blob
    assert "paris" not in blob


def test_taglish_and_escalation(client):
    mixed = client.post("/voice/scenario?scenario=taglish", json={"use_case": "philippines"})
    assert mixed.status_code == 200
    escalated = client.post("/voice/scenario?scenario=escalation", json={"use_case": "philippines"})
    body = escalated.json()
    assert body["call"]["escalated"] is True
    assert "team" in body["call"]["message"].lower() or "tao" in body["call"]["message"].lower()


def test_indonesia_colloquial_and_escalation(client):
    colloquial = client.post("/voice/scenario?scenario=colloquial", json={"use_case": "indonesia"})
    assert colloquial.status_code == 200, colloquial.text
    blob = colloquial.json()["call"]["message"].lower()
    assert "denda" in blob or "cicilan" in blob or "tenor" in blob
    assert "penjara" not in blob
    escalated = client.post("/voice/scenario?scenario=escalation", json={"use_case": "indonesia"})
    assert escalated.json()["call"]["escalated"] is True
    assert "petugas" in escalated.json()["call"]["message"].lower()
