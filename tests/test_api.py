"""API contract tests."""

from providers.base import MissingCredentialError
from providers.llm import build_llm


def test_health_labels_mock_mode(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["llm_mode"] == "mock"
    assert body["voice_mode"] == "mock_web"
    assert "not a phone call" in body["mock_notice"]


def test_search_validation_and_records(client):
    empty = client.post("/kb/search", json={"query": ""})
    assert empty.status_code == 422
    found = client.post("/kb/search", json={"query": "cashless treatment network hospitals", "source_prefix": "health/"})
    assert found.status_code == 200
    body = found.json()
    assert "answer" in body and "confidence" in body and "fallback" in body
    records = client.get("/kb/records")
    assert records.status_code == 200
    assert len(records.json()["records"]) > 5


def test_unknown_call_is_404(client):
    response = client.get("/calls/does-not-exist")
    assert response.status_code == 404


def test_realtime_chunk_and_tables(client):
    created = client.post("/realtime/session")
    assert created.status_code == 200
    call_id = created.json()["call_id"]
    chunk = client.post(
        "/realtime/chunk",
        json={
            "call_id": call_id,
            "speaker": "customer",
            "text": "My wife also needs cover, and we have two kids.",
            "t_ms": 1200,
        },
    )
    assert chunk.status_code == 200, chunk.text
    assert chunk.json()["nudges"]
    transcript = client.get(f"/calls/{call_id}/transcript")
    assert transcript.status_code == 200
    assert transcript.json()["turns"][0]["speaker"] == "customer"
    names = set(client.app.state.db.table_names())
    expected = {
        "knowledge_records",
        "calls",
        "transcripts",
        "retrieval_logs",
        "signals",
        "nudges",
        "latency_metrics",
        "evaluation_results",
    }
    assert expected <= names


def test_llm_builder_refuses_to_fake_a_call():
    assert build_llm("mock", "", "gpt-4o-mini", "https://example.invalid") is None
    try:
        from providers.llm import OpenAICompatibleLLM

        OpenAICompatibleLLM("", "gpt-4o-mini", "https://example.invalid")
        raised = False
    except MissingCredentialError:
        raised = True
    assert raised


def test_websocket_returns_a_nudge(client):
    created = client.post("/realtime/session")
    call_id = created.json()["call_id"]
    with client.websocket_connect(f"/ws/realtime/{call_id}") as socket:
        socket.send_json(
            {
                "type": "chunk",
                "speaker": "customer",
                "text": "My wife also needs cover, and we have two kids.",
                "t_ms": 0,
            }
        )
        event = socket.receive_json()
        assert event["type"] == "chunk_result"
        assert event["nudges"]
        assert event["latency_ms"]["llm_ms"] == "NOT MEASURED"
