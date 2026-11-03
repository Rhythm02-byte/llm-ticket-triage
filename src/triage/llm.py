"""Talks to a local model through Ollama and turns a ticket into a validated Triage."""
import json
import os

import httpx
from pydantic import ValidationError

from triage.schema import Triage

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")

SYSTEM_PROMPT = """You triage support tickets for a connected-vehicle smartphone app. Tickets are in German or English.

Return JSON with these fields:
- category: one of
  connectivity (the app can't reach the vehicle: Bluetooth, pairing, telematics, data sync),
  app_bug (crashes, freezes, wrong or broken screens in the app),
  navigation (routes, maps, directions, trip planning),
  account (login, password, subscription, billing, personal data),
  safety (crash or fall detection, emergency call, anything that affects rider safety),
  feedback (feature requests, praise, general opinions).
- urgency:
  high if rider safety is involved, the customer can't use the vehicle or the app at all, or they were charged wrongly;
  medium if a feature is broken but there is a workaround;
  low for questions, feedback and feature requests.
- language: "de" for German, "en" for English.
- summary: one short sentence in English describing the problem.

Classify only what the ticket says. Do not invent details."""


class TriageError(Exception):
    """The model did not return a valid triage, even after a retry."""


class OllamaClient:
    def __init__(self, url=OLLAMA_URL, model=OLLAMA_MODEL, timeout=120.0):
        self.url = url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _chat(self, text):
        response = httpx.post(
            f"{self.url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                # Ollama constrains the reply to this JSON schema
                "format": Triage.model_json_schema(),
                "stream": False,
                "options": {"temperature": 0, "seed": 42},
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    def triage(self, text, attempts=2):
        last_error = None
        for _ in range(attempts):
            try:
                return Triage.model_validate_json(self._chat(text))
            except (ValidationError, json.JSONDecodeError) as error:
                last_error = error
        raise TriageError(f"model output failed validation: {last_error}")

    def is_ready(self):
        """True when Ollama answers and the configured model is installed."""
        try:
            response = httpx.get(f"{self.url}/api/tags", timeout=5.0)
            response.raise_for_status()
        except httpx.HTTPError:
            return False
        names = {m["name"] for m in response.json().get("models", [])}
        return self.model in names
