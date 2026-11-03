import httpx
import pytest
from fastapi.testclient import TestClient

from triage.app import app, get_client
from triage.llm import OllamaClient

VALID = '{"category": "connectivity", "urgency": "medium", "language": "de", "summary": "App cannot pair with the vehicle."}'


class FakeClient(OllamaClient):
    """Replays fixed model replies instead of calling Ollama."""

    def __init__(self, replies=(), ready=True, error=None):
        super().__init__(model="fake-model")
        self.replies = list(replies)
        self.ready = ready
        self.error = error
        self.calls = 0

    def _chat(self, text):
        self.calls += 1
        if self.error:
            raise self.error
        return self.replies.pop(0)

    def is_ready(self):
        return self.ready


@pytest.fixture
def use_client():
    def install(fake):
        app.dependency_overrides[get_client] = lambda: fake
        return TestClient(app)
    yield install
    app.dependency_overrides.clear()


def test_valid_reply_is_returned_with_model_and_latency(use_client):
    client = use_client(FakeClient([VALID]))

    response = client.post("/triage", json={"text": "Die App findet mein Motorrad nicht."})

    assert response.status_code == 200
    body = response.json()
    assert body["category"] == "connectivity"
    assert body["language"] == "de"
    assert body["model"] == "fake-model"
    assert body["latency_ms"] >= 0


def test_invalid_reply_is_retried_once(use_client):
    fake = FakeClient(['{"category": "weather"}', VALID])
    client = use_client(fake)

    response = client.post("/triage", json={"text": "Bluetooth keeps dropping."})

    assert response.status_code == 200
    assert fake.calls == 2


def test_two_invalid_replies_give_502(use_client):
    client = use_client(FakeClient(["not json", '{"category": "weather"}']))

    response = client.post("/triage", json={"text": "Something is wrong."})

    assert response.status_code == 502


def test_unknown_category_is_rejected_not_passed_through(use_client):
    bad = VALID.replace("connectivity", "hardware")
    client = use_client(FakeClient([bad, bad]))

    response = client.post("/triage", json={"text": "The screen is cracked."})

    assert response.status_code == 502


def test_empty_ticket_is_rejected_before_calling_the_model(use_client):
    fake = FakeClient([VALID])
    client = use_client(fake)

    response = client.post("/triage", json={"text": ""})

    assert response.status_code == 422
    assert fake.calls == 0


def test_unreachable_model_gives_503(use_client):
    client = use_client(FakeClient(error=httpx.ConnectError("refused")))

    response = client.post("/triage", json={"text": "App crashes on start."})

    assert response.status_code == 503


def test_health_reports_model_readiness(use_client):
    assert use_client(FakeClient(ready=True)).get("/health").status_code == 200
    assert use_client(FakeClient(ready=False)).get("/health").status_code == 503
